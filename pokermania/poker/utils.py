import sys
import io
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import os
from pypokerengine.api.game import setup_config, start_poker
import importlib.util
import json
import re
from .models import Bot, Match, TestBot


def load_bot(filepath,bot_name=None):
    try:
        spec = importlib.util.spec_from_file_location("Bot", filepath)
        bot = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bot)
        if hasattr(bot, 'Bot'):
            return bot.Bot(bot_name=bot_name), True
        else:
            return "The 'Bot' class is not found in the module.", False
    except Exception as e:
        return str(e), False


def parse_poker_output_to_json(content):
    rounds = []
    round_pattern = re.compile(r"Started the round (\d+)")
    street_pattern = re.compile(r'Street "([^"]+)" started\. \(community card = \[(.*?)\]\)')
    action_pattern = re.compile(r'"([^"]+)" declared "([^:]+):(\d+)"')
    winner_pattern = re.compile(r'''"\['(.+?)'\]" won the round (\d+) \(stack = (\{.*\})\)''')

    current_round = None
    current_street = None

    for line in content.splitlines():
        round_match = round_pattern.search(line)
        if round_match:
            if current_round:
                rounds.append(current_round)
            current_round = {
                "round_number": int(round_match.group(1)),
                "actions": {"preflop": [], "flop": [], "turn": [], "river": []},
                "community_cards": {"preflop":[],"flop": [], "turn": [], "river": []},
                "winner": None,
                "stacks": {}
            }
            current_street = "preflop"
            continue

        if current_round:
            street_match = street_pattern.search(line)
            if street_match:
                street_name = street_match.group(1)
                current_street = street_name
                cards = street_match.group(2).replace("'", "").split(", ") if street_match.group(2) else []
                current_round["community_cards"][street_name] = cards
                if street_name not in current_round["actions"]:
                    current_round["actions"][street_name] = []
                continue

            action_match = action_pattern.search(line)
            if action_match:
                name, action, amount = action_match.groups()
                current_round["actions"][current_street].append({"name": name, "action": action, "amount": int(amount)})
                continue

            winner_match = winner_pattern.search(line)

            if winner_match:
                winner_name = winner_match.group(1)
                current_round["winner"] = winner_name
                stack_info = eval(winner_match.group(3))
                current_round["stacks"] = stack_info
                continue

    if current_round:
        rounds.append(current_round)

    return {"rounds": rounds}


def play_match(bot1_path, bot2_path, bot1, bot2, num_rounds=5, stack=10000):
    bot1_instance, chk1 = load_bot(bot1_path,bot1.name)
    bot2_instance, chk2 = load_bot(bot2_path,bot2.name)

    if not chk1 or not chk2:
        return bot1_instance, bot2_instance, None, None

    bot1_wins = 0
    bot2_wins = 0
    rounds_data = []
    results_stack = 0

    config = setup_config(max_round=num_rounds, initial_stack=stack, small_blind_amount=250)
    config.register_player(name=bot1.name, algorithm=bot1_instance)
    config.register_player(name=bot2.name, algorithm=bot2_instance)

    output_file = "poker_output.txt"

    # Capture the entire output of the match (all rounds) at once
    result, success = redirect_stdout_to_file(config, output_file)

    # Read and parse the output file
    replay_data = read_output_file_and_parse(output_file)
    previous_stack = [stack, stack]
    # Break down the replay data into individual rounds

    for round_num in range(len(replay_data["rounds"])):
        round_data = replay_data["rounds"][round_num] if round_num < len(replay_data["rounds"]) else {}

        if not round_data:
            continue  # Skip if no data for the current round

        # Initialize structures
        actions = {'preflop': {'name': [], 'action': [], 'amount': []},
                   'flop': {'name': [], 'action': [], 'amount': []},
                   'turn': {'name': [], 'action': [], 'amount': []},
                   'river': {'name': [], 'action': [], 'amount': []}}

        communitycards = [[], [], [], []]  # preflop, flop, turn, river
        streets = []  # Will store the streets that actually happened

        # Process each street
        for street in ['preflop', 'flop', 'turn', 'river']:
            street_actions = round_data.get("actions", {}).get(street, [])
            if street_actions:  # If actions exist for the street
                streets.append(street)
                actions[street]['name'] = [action['name'] for action in street_actions]
                actions[street]['action'] = [action['action'] for action in street_actions]
                actions[street]['amount'] = [action['amount'] for action in street_actions]

                # Update community cards
            if street == 'preflop':
                communitycards[0] = []  # No community cards for preflop
            else:
                communitycards_index = ['flop', 'turn', 'river'].index(street) + 1
                communitycards[communitycards_index] = round_data.get("community_cards", {}).get(street, [])

        # Assemble round data in the desired format

        # Accessing the round result
        winner = round_data["winner"]
        stacks = round_data["stacks"]
        bot1_hole_cards=bot1_instance.hole_cards_log
        bot2_hole_cards=bot2_instance.hole_cards_log

        hole_cards=[[],[]]
        hole_cards[0]=bot1_hole_cards[round_num]["hole_cards"]
        hole_cards[1]=bot2_hole_cards[round_num]["hole_cards"]

        if winner is None or stacks == {}:  # tie has happened
            rounds_data.append({
                'hole_cards':hole_cards,
                'street': streets,
                'actions': actions,
                'communitycards': communitycards,
                'chips_exchanged': 0,
                'total_chips_exchanged': 0,
                'winner': "No one"
            })
        else:

            stacks_array = list(stacks.values())

            round_chips = abs(stacks_array[0] - previous_stack[0])
            both_chips_exchanged = abs(stacks_array[0] - previous_stack[0]) + abs(stacks_array[1] - previous_stack[1])
            previous_stack = stacks_array

            if winner == bot1.name:
                bot1_wins += 1
            else:
                bot2_wins += 1

            rounds_data.append({
                'hole_cards': hole_cards,
                'street': streets,
                'actions': actions,
                'communitycards': communitycards,
                'chips_exchanged': abs(round_chips),
                'total_chips_exchanged': both_chips_exchanged,
                'winner': winner
            })

    # Determine match winner
    winner = ""
    if bot1_wins > bot2_wins:
        winner = bot1.name
    elif bot2_wins > bot1_wins:
        winner = bot2.name
    else:
        winner = "No one"

    # Update bot statistics
    update_bot_stats(bot1, bot2, winner, abs(result["players"][0]["stack"] - result["rule"]["initial_stack"]),
                     bot1_wins, num_rounds)


    return winner, abs(result["players"][0]["stack"] - result["rule"]["initial_stack"]), rounds_data, [bot1_wins,
                                                                                                       bot2_wins]


def redirect_stdout_to_file(config, output_file):
    with open(output_file, "w") as file:
        original_stdout = sys.stdout
        try:
            sys.stdout = file
            result = start_poker(config, verbose=1)
            return result, True
        except Exception as e:
            sys.stdout = original_stdout
            with open(output_file, "a") as err_file:
                err_file.write(f"\nError: {str(e)}")
            return str(e), False
        finally:
            sys.stdout = original_stdout


def redirect_stdout_to_memory(config):
    buffer = io.StringIO()  # Create an in-memory buffer
    original_stdout = sys.stdout  # Save the original stdout
    try:
        sys.stdout = buffer  # Redirect stdout to the buffer
        result = start_poker(config, verbose=1)  # Run the poker game
        output_content = buffer.getvalue()  # Get the buffer's content as a string
        return result, output_content, True
    except Exception as e:
        return None, str(e), False
    finally:
        sys.stdout = original_stdout  # Restore the original stdout


def read_output_from_memory(output_content):
    return parse_poker_output_to_json(output_content)


def read_output_file_and_parse(input_file):
    with open(input_file, "r") as file:
        content = file.read()
    return parse_poker_output_to_json(content)


def update_bot_stats(bot1, bot2, winner, chips_exchanged, bot1_wins, num_rounds):
    chips_per_round = chips_exchanged / num_rounds
    score_per_round = 20 + 80 * chips_per_round / 10000

    if winner == bot1.name:
        bot1.chips_won += chips_exchanged
        bot2.chips_won -= chips_exchanged
        bot1.wins += 1
        bot1.score += score_per_round * bot1_wins
        bot2.score -= score_per_round * (num_rounds - bot1_wins)
    else:
        bot1.chips_won -= chips_exchanged
        bot2.chips_won += chips_exchanged
        bot2.wins += 1
        bot2.score += score_per_round * (num_rounds - bot1_wins)
        bot1.score -= score_per_round * bot1_wins

    bot1.total_games += 1
    bot2.total_games += 1
    bot1.save()
    bot2.save()
