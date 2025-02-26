from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class User(AbstractUser):
    # Fix related_name conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name="custom_user_set",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="custom_user_permissions_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )


class Bot(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('poker.User', on_delete=models.CASCADE)
    name = models.TextField()
    file = models.FileField(upload_to='static/bots/',max_length=5000)
    path = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    wins = models.IntegerField(default=0)
    total_games = models.IntegerField(default=0)
    chips_won = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} (by {self.user.username})"


class Match(models.Model):
    id = models.AutoField(primary_key=True)
    players = models.ManyToManyField(Bot, related_name="matches")  # Multiple bots per match
    winner = models.TextField()
    played_at = models.DateTimeField(auto_now_add=True)
    rounds_data = models.JSONField(max_length=100000)

    class Meta:
        ordering = ['-played_at']

    def __str__(self):
        player_names = ", ".join(bot.name for bot in self.players.all())
        return f"Match ({self.played_at.date()}): {player_names} | Winner: {self.winner}"



class TestBot(models.Model):
    user = models.ForeignKey('poker.User', on_delete=models.CASCADE)
    name = models.TextField()
    file = models.FileField(upload_to='test_bots/')  # Changed upload_to for better organization
    created_at = models.DateTimeField(auto_now_add=True)
    chips_won = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    total_games = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Test Bot: {self.name}"


class TestMatch(models.Model):
    """New model to store test match results"""
    id = models.AutoField(primary_key=True)  # Changed from game_id to id for consistency
    bot1 = models.ForeignKey(TestBot, related_name='test_matches', on_delete=models.CASCADE)
    opponent_name = models.TextField()
    winner = models.TextField()
    total_chips_exchanged = models.IntegerField()
    test_bot_wins = models.IntegerField()
    opponent_wins = models.IntegerField()
    played_at = models.DateTimeField(auto_now_add=True)
    rounds_data = models.JSONField(max_length=100000)

    class Meta:
        ordering = ['-played_at']

    def __str__(self):
        return f"Test Match: {self.bot1.name} vs {self.opponent_name}"

