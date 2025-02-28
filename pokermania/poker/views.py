import traceback
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import get_user_model, logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect ,get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
import re
from .models import Bot, Match, TestBot, TestMatch
from .utils import play_match,play_test_match

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
    if Bot.objects.filter(user=user).count()>20:
        messages.error(request, "You can only upload 10 bot.")
        return redirect('deploy_bot') 

    try:
        with open(bot_file_path, 'r') as file:
            bot_file = file.read()

    except FileNotFoundError:
        messages.error(request, f"The file at {bot_file_path} was not found.")
        return redirect('deploy_bot')

    try:
        Bot.objects.create(user=user, name=bot_name, file=bot_file, path=bot_file_path)
        
        messages.success(request, f"Bot '{bot_name}' uploaded successfully!")
    
    except Exception as e:
        traceback.print_exc()
        messages.error(request, "An error occurred while uploading the bot.")
        return redirect('deploy_bot')

    return redirect('deploy_bot')

@login_required
@transaction.atomic
def test_run(request):
    try:
        user = request.user
        bot_name = request.POST.get('name').strip()
        bot_file = request.FILES['file']

        # Validate bot name
        if not bot_name:
            messages.error(request, "Bot name cannot be empty")
            return redirect('/deploy_bot/')

        # Check for existing bot names
        if Bot.objects.filter(name=bot_name).exists():
            messages.info(request, "Bot name already taken!")
            return redirect('/deploy_bot/')

        # Create new test bot
        try:
            new_test_bot = TestBot.objects.create(
                user=user,
                name=bot_name,
                file=bot_file
            )
        except (IOError, ValidationError) as e:
            messages.error(request, f"Error saving bot file: {str(e)}")
            return redirect('/deploy_bot/')

        # Load predefined bots with error handling
        predefined_bots_info = [
            {"name": "Aggressive", "path": "bots/aggressive_bot.py"},
            {"name": "Always_Call", "path": "bots/always_call_bot.py"},
            {"name": "Cautious_bot", "path": "bots/cautious_bot.py"},
            {"name": "Probability_based_bot", "path": "bots/probability_based_bot.py"},
            {"name": "Random_bot", "path": "bots/random_bot.py"}
        ]

        test_bots = []
        for bot_info in predefined_bots_info:
            try:
                bot, _ = TestBot.objects.get_or_create(
                    user=user,
                    name=bot_info['name'],
                    defaults={'file': bot_info['path']}
                )
                test_bots.append(bot)
            except Exception as e:
                messages.error(request, f"Error loading predefined bot {bot_info['name']}: {str(e)}")
                return redirect('/deploy_bot/')

        all_bots = [new_test_bot] + test_bots
        bot_paths = [bot.file.path for bot in all_bots]
        try:
            match_result, rounds_data = play_test_match(bot_paths, all_bots)
        except Exception as e:
            messages.error(request, f"Error executing match: {str(e)}")
            return redirect('/deploy_bot/')

        if isinstance(match_result, str) and match_result.startswith("Invalid"):
            messages.error(request, f"Match error: {match_result}")
            return redirect('/deploy_bot/')
        # Create match record
        try:
            test_match = TestMatch.objects.create(
                winner=match_result,
                rounds_data=rounds_data,
                player_order=[bot.id for bot in all_bots]
            )
            test_match.players.set([new_test_bot] + test_bots)
        except Exception as e:
            messages.error(request, f"Error saving match results: {str(e)}")
            return redirect('/deploy_bot/')

        # Prepare results
        results = {
            'match_id': test_match.id,
            'opponents': [bot.name for bot in test_bots],
            'winner': match_result,
            'rounds_data': rounds_data
        }

        return render(request, 'test_run_Response.html', {
            'results': results,
            'testbot': new_test_bot
        })

    except Exception as e:
        messages.error(request, f"Unexpected error occurred: {str(e)}")
        return redirect('/deploy_bot/')
    
@login_required
def test_replay(request, match_id):
    match = get_object_or_404(TestMatch, id=match_id)
    ordered_players = [TestBot.objects.get(id=bot_id).name for bot_id in match.player_order]
    
    return render(request, 'test_multigame.html', {
        'rounds_data': match.rounds_data,
        'players': ordered_players,  # Correct order
        'match': match,
        'bot_id': match.bot1.id
    })



def test_match_results(request, match_id):
    try:
        # Get match with error handling for invalid ID
        match = get_object_or_404(TestMatch, id=match_id)
        
        # Get user's bot in the match with permission check
        testbot = match.players.filter(user=request.user).first()
        if not testbot:
            messages.error(request, "You don't have permission to view this match")
            return redirect('deploy_bot')  # Redirect to appropriate page

        # Validate match data integrity
        if not all(hasattr(match, attr) for attr in ['winner', 'played_at', 'rounds_data']):
            messages.error(request, "Invalid match data structure")
            return redirect('deploy_bot')

        # Safely prepare opponents list
        try:
            opponents = [player.name for player in match.players.all() if player.id != testbot.id]
        except AttributeError as e:
            messages.error(request, f"Error processing player data: {str(e)}")
            return redirect('deploy_bot')
        
        # Validate rounds data format
        if not isinstance(match.rounds_data, list):
            messages.error(request, "Invalid round data format")
            return redirect('deploy_bot')

        # Prepare results with error handling
        try:
            results = [{
                'match': match,
                'opponents': opponents,
                'winner': match.winner,
                'played_at': match.played_at,
                'rounds_data': match.rounds_data,
            }]
        except KeyError as e:
            messages.error(request, f"Missing key in match data: {str(e)}")
            return redirect('deploy_bot')

        context = {
            'testbot': testbot,
            'results': results,
        }

        return render(request, 'test_run_Response2.html', context)

    except PermissionDenied:
        messages.error(request, "You don't have permission to access this resource")
        return redirect('login')
        
    except ObjectDoesNotExist as e:
        messages.error(request, "Requested resource no longer exists")
        return redirect('deploy_bot')
        
    except Exception as e:
        # Log the exception here (consider adding logging)
        messages.error(request, "An unexpected error occurred")
        return redirect('deploy_bot')


@login_required
def admin_panel(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        # Get selected bots from form
        selected_bot_ids = request.POST.getlist('bots')
        selected_bots = Bot.objects.filter(id__in=selected_bot_ids)
        
        # Validate selection
        if len(selected_bots) < 2:
            messages.error(request, "Please select at least 2 bots.")
            return redirect('admin_panel')
        if len(selected_bots) > 6:
            messages.error(request, "Maximum 6 bots allowed per match.")
            return redirect('admin_panel')

        bot_paths = [bot.path for bot in selected_bots]

        result = play_match(bot_paths,selected_bots)
        
        # Handle errors from play_match
        if isinstance(result[0], list):  # Error case
            for error in result[0]:
                messages.error(request, error)
            return redirect('admin_panel')
        
        # Unpack normal results
        winner_name,rounds_data = result

        if(rounds_data==None):
            return JsonResponse({"Error":winner_name})

        try:            
            # Create match record
            match = Match.objects.create(
                winner=winner_name,
                rounds_data=rounds_data
            )
            match.players.add(*selected_bots)
        
        except Exception as e:
            messages.error(request, f"Error saving match: {str(e)}")

        return redirect('admin_panel')

    # GET request - show all bots and recent matches
    all_bots = Bot.objects.all().order_by('name')
    recent_matches = Match.objects.all().order_by('-played_at')[:10]

    return render(request, 'admin_panel.html', {
        'all_bots': all_bots,
        'recent_matches': recent_matches,
        'max_bots': range(2, 7)
    })

@login_required
def replay(request, match_id):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('')
    
    match = get_object_or_404(Match,id=match_id)
    players = [bot.name for bot in match.players.all()]
    return render(request, 'multigame.html',{
        'rounds_data': match.rounds_data,
        'players': players,
    })