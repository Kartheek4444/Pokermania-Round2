import traceback
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import get_user_model, logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import re, os, json
from pypokerengine.api.game import setup_config
from .models import Bot, Match, TestBot, TestMatch
from .utils import play_match

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
    print("\n=== Debugging: Upload Bot ===")
    print(f"User: {user.username}")
    print(f"Bot Name: {bot_name}")
    print(f"Bot File Path: {bot_file_path}")
    if Bot.objects.filter(user=user).count()>10:
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

    return redirect('home')

@login_required
def test_run(request):
    user = request.user
    bot_name = request.POST.get('name')
    bot_file = request.FILES['file']

    if Bot.objects.filter(name=bot_name).exists():
        messages.info(request, "BotName already taken!")
        return redirect('/deploy_bot/')

    new_test_bot = TestBot.objects.create(user=user, name=bot_name, file=bot_file)

    predefined_bots_info = [
        {"name": "Aggressive", "path": "bots/aggressive_bot.py"},
        {"name": "Always_Call", "path": "bots/always_call_bot.py"},
        {"name": "Cautious_bot", "path": "bots/cautious_bot.py"},
        {"name": "Probability_based_bot", "path": "bots/probability_based_bot.py"},
        {"name": "Random_bot", "path": "bots/random_bot.py"}
    ]

    test_bots = []
    for bot_info in predefined_bots_info:
        bot, _ = TestBot.objects.get_or_create(
            user=user,
            name=bot_info['name'],
            defaults={'file': bot_info['path']}
        )
        test_bots.append(bot)

    all_bots = [new_test_bot] + test_bots
    bot_paths = [bot.file.path for bot in all_bots]

    match_result, rounds_data = play_match(bot_paths, all_bots)

    if isinstance(match_result, str) and match_result.startswith("Invalid"):
        return JsonResponse({"error": match_result})


    test_match = TestMatch.objects.create(
        winner=match_result,
        rounds_data=rounds_data
    )
    test_match.players.set([new_test_bot] + test_bots)
    
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

@login_required
def test_replay(request, match_id):
    match = get_object_or_404(TestMatch,id=match_id)
    players = [bot.name for bot in match.players.all()]
    return render(request, 'test_multigame.html',{
        'rounds_data': match.rounds_data,
        'players': players,
        'match':match,
        'bot_id': match.bot1.id
    })

def test_match_results(request, match_id):
    # Fetch the bot instance
    match=get_object_or_404(TestMatch,id=match_id)
    bot_instance = match.bot1

    # Fetch matches involving the bot
    # matches = TestMatch.objects.filter(
    #     players=bot_instance  # Filter matches where the bot is one of the players
    # ).order_by('-played_at')

    # Collect match results
    results = []
    # Get the opponent(s) for the match
    opponents = [player.name for player in match.players.all() if player.id != bot_instance.id]
    results.append({
        'match': match,
        'opponents': opponents,  # List of opponent names
        'winner': match.winner,
        'played_at': match.played_at,
        'rounds_data': match.rounds_data,
    })

    # Prepare the context
    context = {
        'testbot': bot_instance,
        'results': results,
    }

    # Render the template
    return render(request, 'test_run_Response2.html', context)


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

        bot_paths = [bot.file.path for bot in selected_bots]

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