import traceback

from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import get_user_model, logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import re, os
from pypokerengine.api.game import setup_config
from .models import Bot, Match, TestBot, TestMatch
from .utils import play_match, load_bot, redirect_stdout_to_file

User = get_user_model()


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirmPassword = request.POST.get('confirmPassword')

        # Check if passwords match
        if password != confirmPassword:
            messages.error(request, "Passwords do not match!")
            return redirect('/login/')

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('/login/')
        if not re.search(r'\d', password):
            messages.error(request, "Password must contain at least one number.")
            return redirect('/login/')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect('/login/')
        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return redirect('/login/')

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.info(request, "Username already taken!")
            return redirect('/login/')

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.save()

        messages.info(request, "Account created Successfully!")
        return redirect('/login/')

    return render(request, 'login.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not User.objects.filter(username=username).exists():
            messages.error(request, 'Invalid Username')
            return redirect('/login/')
        user = authenticate(username=username, password=password)

        if user is None:
            messages.error(request, "Invalid Password")
            return redirect('/login/')
        else:
            login(request, user)
            return redirect('/')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def home(request):
    user_logged_in = request.user.is_authenticated
    return render(request, 'home.html', {'user_logged_in': user_logged_in})


@login_required
def deploy_bot(request):
    return render(request, 'deploy.html')


def contact_us(request):
    return render(request, 'contact.html')


def documentation(request):
    return render(request, 'documentation.html')


@login_required
def upload_bot(request):
    user = request.user
    bot_name = request.POST.get('bot_name')
    bot_file_path = request.POST.get('bot_file_path')

    if Bot.objects.filter(user=user).count() > 5:
        return render(request, 'deploy.html', {'message': "You can only upload a maximum of 5 bots."})

    try:
        with open(bot_file_path, 'r') as file:
            bot_file = file.read()

    except FileNotFoundError:
        return render(request, 'deploy.html', {'message': f"The file at {bot_file_path} was not found."})

    try:
        new_bot = Bot.objects.create(user=user, name=bot_name, file=bot_file, path=bot_file_path)
    except Exception as e:

        traceback.print_exc()
        raise
    existing_bots = Bot.objects.exclude(id=new_bot.id)

    for existing_bot in existing_bots:
        winner, chips_exchanged, rounds_data, win_counts = play_match(
            bot_file_path, existing_bot.path, new_bot, existing_bot
        )

        if winner is not None:
            Match.objects.create(
                bot1=new_bot,
                bot2=existing_bot,
                winner=winner,
                total_chips_exchanged=chips_exchanged,
                rounds_data=rounds_data,
                bot1_wins=win_counts[0],
                bot2_wins=win_counts[1]
            )

    return redirect('/my_bots/')


def leaderboard(request):
    bots = Bot.objects.all().order_by('-score')  # Only regular bots are considered
    data = []

    for idx, bot in enumerate(bots, start=1):
        earnings = f"${bot.chips_won:,.0f}"
        win_rate = (bot.wins / bot.total_games * 100) if bot.total_games > 0 else 0

        data.append({
            'rank': idx,
            'botName': bot.name,
            'owner': bot.user.username,
            'wins': bot.wins,
            'total_games': bot.total_games,
            'win_rate': f"{win_rate:.1f}%",
            'earnings': earnings,
            'score': bot.score
        })

    return render(request, 'leaderboard.html', {'data': data})


@login_required
def my_bots(request):
    # Fetch only the user's bots
    bots = Bot.objects.filter(user=request.user)
    selected_bot = request.GET.get('bot', 'all')
    bot_matches = {}

    if selected_bot != 'all':
        # Fetch matches for the selected bot
        selected_bot_instance = Bot.objects.get(name=selected_bot, user=request.user)
        matches = Match.objects.filter(bot1=selected_bot_instance) | Match.objects.filter(bot2=selected_bot_instance)
    else:
        # Fetch matches for all bots owned by the user
        matches = Match.objects.filter(bot1__in=bots) | Match.objects.filter(bot2__in=bots)

    for match in matches:
        for bot in [match.bot1, match.bot2]:
            if bot.user == request.user:
                if bot.name not in bot_matches:
                    bot_matches[bot.name] = []

                opponent = match.bot2 if bot == match.bot1 else match.bot1
                bot_matches[bot.name].append({
                    'bot_name': bot.name,
                    'opponent': opponent.name,
                    'result': match.winner,
                    'date': match.played_at,
                    'chips_exchanged': abs(match.total_chips_exchanged),
                    'id': match.id,
                    'bot1_wins': match.bot1_wins,
                    'bot2_wins': match.bot2_wins
                })

    return render(request, 'bots.html', {
        'bots': bots,
        'bot_matches': bot_matches,
        'selected_bot': selected_bot,
    })


def replay(request, match_id):
    match = Match.objects.get(id=match_id)
    if match.bot1.user != request.user and match.bot2.user != request.user:
        return redirect('/my_bots/')

    player = "L" if match.bot1.user == request.user else "R"


    return render(request, 'game.html', {
        'match': match,
        'player': player,
        'rounds_data': match.rounds_data
    })


@login_required
def test_run(request):
    user = request.user
    bot_name = request.POST.get('name')
    bot_file = request.FILES['file']


    if Bot.objects.filter(name=bot_name).exists():
        messages.info(request, "BotName already taken!")
        return redirect('/deploy_bot/')


    # Create a test bot
    new_test_bot = TestBot.objects.create(user=user, name=bot_name, file=bot_file)

    # Predefined test bots
    test_bots_info = [
        {"name": "Always_call_bot", "path": "bots/always_call_bot.py"},
        {"name": "Aggressive_bot", "path": "bots/aggressive_bot.py"},
        {"name": "Cautious_bot", "path": "bots/cautious_bot.py"},
        {"name": "Probability_based_bot", "path": "bots/probability_based_bot.py"},
        {"name": "Random_bot", "path": "bots/random_bot.py"}
    ]

    results = []

    for bot_info in test_bots_info:
        # No interaction with regular bots
        opponent_bot, _ = TestBot.objects.get_or_create(
            user=request.user,  # Associate with the user for better tracking
            name=bot_info['name'],
            defaults={'file': bot_info['path']}
        )

        # Simulate a match between the test bot and the predefined test bot
        winner, chips_exchanged, rounds_data, win_counts = play_match(
            new_test_bot.file.path,
            opponent_bot.file.path,
            new_test_bot,
            opponent_bot
        )

        if(win_counts==None):
            return JsonResponse({"Error":winner,"Error":chips_exchanged})
        
        # Log results in TestMatch model
        test_match=TestMatch.objects.create(
            bot1=new_test_bot,

            opponent_name=opponent_bot.name,
            winner=winner,
            total_chips_exchanged=chips_exchanged,
            test_bot_wins=win_counts[0],
            opponent_wins=win_counts[1],
            rounds_data=rounds_data
        )

        results.append({
            'match_id': test_match.id,
            'opponent_name': opponent_bot.name,
            'winner': winner,
            'chips_exchanged': chips_exchanged,
            'bot_wins': win_counts[0],
            'opponent_wins': win_counts[1],
            'rounds_data': rounds_data
        })

    return render(request, 'test_run_response.html', {
        'results': results,
        'testbot': new_test_bot
    })

@login_required
def test_replay(request, match_id):
    match = TestMatch.objects.get(id=match_id)

    if match.bot1.user != request.user:
        return redirect('/test_run/')

    player = "L" if match.bot1.user == request.user else "R"

    return render(request, 'testgame.html', {
        'bot_name':match.bot1.name,
        'player_name':match.opponent_name,
        'match': match,
        'player': player,
        'rounds_data': match.rounds_data,
    })

def test_match_results(request, bot_id):
    bot_instance = get_object_or_404(TestBot, id=bot_id)

    matches = TestMatch.objects.filter(
        Q(bot1_id=bot_instance.id)
    ).order_by('-played_at')  

    # Collect match results
    results = []
    for match in matches:
        results.append({
            'match_id': match.id,
            'opponent_name': match.opponent_name,
            'winner': match.winner,
            'chips_exchanged': match.total_chips_exchanged,
            'bot_wins': match.test_bot_wins,
            'opponent_wins': match.opponent_wins,
            'played_at': match.played_at,
            'rounds_data': match.rounds_data,
        })

    context = {
        'testbot': bot_instance,
        'results': results,
    }
    return render(request, 'test_run_Response2.html', context)

