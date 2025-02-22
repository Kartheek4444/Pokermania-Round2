from django.contrib import admin
from .models import User,Bot,Match,TestMatch


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
    list_display = ('bot1', 'bot2', 'winner')
    search_fields = ('bot1', 'bot2', 'winner')

@admin.register(TestMatch)
class TestMatchAdmin(admin.ModelAdmin):
    list_display = ('id','bot1', 'opponent_name', 'winner')
    search_fields = ('bot1', 'opponent_name', 'winner')