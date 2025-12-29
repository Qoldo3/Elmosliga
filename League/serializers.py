from rest_framework import serializers
from League.models import League, Team, Prediction, LeagueResult


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("id", "name", "image", "league")


class LeagueSerializer(serializers.ModelSerializer):
    teams = TeamSerializer(many=True, read_only=True)
    
    class Meta:
        model = League
        fields = (
            "id",
            "name",
            "image",
            "is_active",
            "first_place_points",
            "second_place_points",
            "third_place_points",
            "teams",
        )


class PredictionSerializer(serializers.ModelSerializer):
    first_place_team_name = serializers.CharField(
        source="first_place_team.name", read_only=True
    )
    second_place_team_name = serializers.CharField(
        source="second_place_team.name", read_only=True
    )
    third_place_team_name = serializers.CharField(
        source="third_place_team.name", read_only=True
    )
    league_name = serializers.CharField(source="league.name", read_only=True)

    class Meta:
        model = Prediction
        fields = (
            "id",
            "league",
            "league_name",
            "first_place_team",
            "first_place_team_name",
            "second_place_team",
            "second_place_team_name",
            "third_place_team",
            "third_place_team_name",
            "points",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("points", "created_at", "updated_at")

    def validate(self, attrs):
        league = attrs.get("league")
        first_team = attrs.get("first_place_team")
        second_team = attrs.get("second_place_team")
        third_team = attrs.get("third_place_team")

        # Check all teams belong to the league
        teams = [first_team, second_team, third_team]
        for team in teams:
            if team.league != league:
                raise serializers.ValidationError(
                    f"Team {team.name} must belong to {league.name}"
                )

        # Check all teams are different
        if len(set(teams)) != 3:
            raise serializers.ValidationError(
                "All three teams must be different"
            )

        # Check if league is active
        if not league.is_active:
            raise serializers.ValidationError(
                "Cannot make predictions for inactive leagues"
            )

        return attrs

    def create(self, validated_data):
        profile = self.context["request"].user.profile
        prediction, created = Prediction.objects.update_or_create(
            profile=profile,
            league=validated_data["league"],
            defaults={
                "first_place_team": validated_data["first_place_team"],
                "second_place_team": validated_data["second_place_team"],
                "third_place_team": validated_data["third_place_team"],
            },
        )
        return prediction


class LeagueResultSerializer(serializers.ModelSerializer):
    first_place_name = serializers.CharField(
        source="first_place.name", read_only=True
    )
    second_place_name = serializers.CharField(
        source="second_place.name", read_only=True
    )
    third_place_name = serializers.CharField(
        source="third_place.name", read_only=True
    )
    league_name = serializers.CharField(source="league.name", read_only=True)

    class Meta:
        model = LeagueResult
        fields = (
            "id",
            "league",
            "league_name",
            "first_place",
            "first_place_name",
            "second_place",
            "second_place_name",
            "third_place",
            "third_place_name",
            "updated_at",
        )

    def validate(self, attrs):
        league = attrs.get("league", self.instance.league if self.instance else None)
        first = attrs.get("first_place", self.instance.first_place if self.instance else None)
        second = attrs.get("second_place", self.instance.second_place if self.instance else None)
        third = attrs.get("third_place", self.instance.third_place if self.instance else None)

        teams = [first, second, third]
        
        # Check all teams belong to the league
        for team in teams:
            if team and team.league != league:
                raise serializers.ValidationError(
                    f"Team {team.name} must belong to {league.name}"
                )

        # Check all teams are different
        if len(set(teams)) != 3:
            raise serializers.ValidationError(
                "All three teams must be different"
            )

        return attrs