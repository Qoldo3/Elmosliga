from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import Profile


class League(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="leagues/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # Points awarded for correct predictions at each position (1st-6th place)
    first_place_points = models.IntegerField(default=20)
    second_place_points = models.IntegerField(default=15)
    third_place_points = models.IntegerField(default=10)
    fourth_place_points = models.IntegerField(default=7)
    fifth_place_points = models.IntegerField(default=5)
    sixth_place_points = models.IntegerField(default=3)

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
    fourth_place = models.ForeignKey(
        Team,
        related_name="fourth_place_results",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    fifth_place = models.ForeignKey(
        Team,
        related_name="fifth_place_results",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    sixth_place = models.ForeignKey(
        Team,
        related_name="sixth_place_results",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Ensure all teams belong to the same league
        teams = [
            self.first_place, self.second_place, self.third_place,
            self.fourth_place, self.fifth_place, self.sixth_place
        ]
        # Filter out None values for validation
        valid_teams = [team for team in teams if team is not None]
        
        for team in valid_teams:
            if team.league != self.league:
                raise ValidationError(
                    f"Team {team.name} must belong to {self.league.name}"
                )
        
        # Ensure all teams are different (only if all 6 are provided)
        if len(valid_teams) == 6 and len(set(valid_teams)) != 6:
            raise ValidationError("All six teams must be different")

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
    predicted_team = models.ForeignKey(
        Team,
        related_name="predictions",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("profile", "league")

    def clean(self):
        # Ensure the predicted team belongs to the selected league
        if self.predicted_team and self.predicted_team.league != self.league:
            raise ValidationError(
                f"Team {self.predicted_team.name} must belong to {self.league.name}"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.profile.user.email} - {self.league.name}: {self.predicted_team.name} ({self.points} pts)"