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
    total_chips_exchanged = models.IntegerField(default=0)
    total_rounds = models.IntegerField(default=50)
    played_at = models.DateTimeField(auto_now_add=True)
    rounds_data = models.JSONField(max_length=100000)  # New field to store data for all rounds

    class Meta:
        ordering = ['-played_at']

    def __str__(self):
        return f"{self.bot1.name} vs {self.bot2.name} ({self.played_at.date()})"


class Round(models.Model):
    """New model to store individual round data"""
    match = models.ForeignKey(Match, related_name='rounds', on_delete=models.CASCADE)
    round_number = models.IntegerField()
    winner = models.TextField()
    chips_exchanged = models.IntegerField()
    replay_data = models.JSONField(max_length=100000)
    hole_cards = models.JSONField()

    class Meta:
        ordering = ['round_number']
        unique_together = ['match', 'round_number']

    def __str__(self):
        return f"Round {self.round_number} of {self.match}"


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

