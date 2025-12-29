from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import Profile


class League(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="leagues/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # Points awarded for correct first place prediction
    first_place_points = models.IntegerField(default=10)
    second_place_points = models.IntegerField(default=5)
    third_place_points = models.IntegerField(default=3)

    def __str__(self):
        return self.name


class Team(models.Model):
    league = models.ForeignKey(
        League,
        related_name="teams",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="teams/", blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.league.name})"


class LeagueResult(models.Model):
    league = models.OneToOneField(
        League,
        related_name="result",
        on_delete=models.CASCADE
    )
    first_place = models.ForeignKey(
        Team,
        related_name="first_place_results",
        on_delete=models.CASCADE
    )
    second_place = models.ForeignKey(
        Team,
        related_name="second_place_results",
        on_delete=models.CASCADE
    )
    third_place = models.ForeignKey(
        Team,
        related_name="third_place_results",
        on_delete=models.CASCADE
    )
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Ensure all teams belong to the same league
        teams = [self.first_place, self.second_place, self.third_place]
        for team in teams:
            if team.league != self.league:
                raise ValidationError(
                    f"Team {team.name} must belong to {self.league.name}"
                )
        
        # Ensure all teams are different
        if len(set(teams)) != 3:
            raise ValidationError("All three teams must be different")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Result - {self.league.name}"


class Prediction(models.Model):
    profile = models.ForeignKey(
        Profile,
        related_name="predictions",
        on_delete=models.CASCADE
    )
    league = models.ForeignKey(
        League,
        related_name="predictions",
        on_delete=models.CASCADE
    )
    first_place_team = models.ForeignKey(
        Team,
        related_name="first_place_predictions",
        on_delete=models.CASCADE
    )
    second_place_team = models.ForeignKey(
        Team,
        related_name="second_place_predictions",
        on_delete=models.CASCADE
    )
    third_place_team = models.ForeignKey(
        Team,
        related_name="third_place_predictions",
        on_delete=models.CASCADE
    )
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("profile", "league")

    def clean(self):
        # Ensure all teams belong to the selected league
        teams = [self.first_place_team, self.second_place_team, self.third_place_team]
        for team in teams:
            if team.league != self.league:
                raise ValidationError(
                    f"Team {team.name} must belong to {self.league.name}"
                )
        
        # Ensure all teams are different
        if len(set(teams)) != 3:
            raise ValidationError("All three predicted teams must be different")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.profile.user.email} - {self.league.name} ({self.points} pts)"