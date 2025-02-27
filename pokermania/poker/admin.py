from django.contrib import admin
from .models import User,Bot,Match,TestMatch,TestBot


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'players_display', 'winner', 'played_at')
    search_fields = ('players__name', 'winner')

    def players_display(self, obj):
        return ", ".join([bot.name for bot in obj.players.all()])
    players_display.short_description = "Players"

class TestMatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_bot1', 'get_players', 'winner', 'played_at')
    list_filter = ('winner', 'played_at')
    search_fields = ('winner', 'bot1__name', 'players__name')

    @admin.display(description="Bot 1")
    def get_bot1(self, obj):
        """Returns the name of bot1."""
        return obj.bot1.name

    @admin.display(description="Players")
    def get_players(self, obj):
        """Returns a comma-separated list of player names (excluding bot1)."""
        # Exclude bot1 from the players list to avoid duplication
        players = obj.players.exclude(id=obj.bot1.id)
        return ", ".join([player.name for player in players])

admin.site.register(TestMatch, TestMatchAdmin)
@admin.register(TestBot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
