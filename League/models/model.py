from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import Profile


class League(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="leagues/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

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
        related_name="+",
        on_delete=models.CASCADE
    )
    second_place = models.ForeignKey(
        Team,
        related_name="+",
        on_delete=models.CASCADE
    )
    third_place = models.ForeignKey(
        Team,
        related_name="+",
        on_delete=models.CASCADE
    )
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Ensure all teams belong to the same league
        teams = [self.first_place, self.second_place, self.third_place]
        for team in teams:
            if team.league != self.league:
                raise ValidationError("All teams must belong to the same league.")

    def __str__(self):
        return f"Result - {self.league.name}"

    def calculate_points(self):
        """
        Assign points to all predictions of this league.
        Example points: 1st=10, 2nd=5, 3rd=2
        """
        points_map = {
            self.first_place.id: 10,
            self.second_place.id: 5,
            self.third_place.id: 2
        }
        for prediction in self.league.predictions.all():
            prediction.points = points_map.get(prediction.first_place_team.id, 0)
            prediction.save()


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
    # Only user selects first-place team
    first_place_team = models.ForeignKey(
        Team,
        related_name="+",
        on_delete=models.CASCADE
    )
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "league")

    def clean(self):
        # Ensure selected team belongs to the selected league
        if self.first_place_team.league != self.league:
            raise ValidationError("Selected team must belong to the selected league.")

    def __str__(self):
        return f"{self.profile.user.email} - {self.league.name}"
