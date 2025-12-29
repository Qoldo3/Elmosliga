from rest_framework import serializers
from League.models import League, Team, Prediction, LeagueResult

class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = "__all__"


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = (
            "id",
            "league",
            "first_place_team",
            "points",
        )
        read_only_fields = ("points",)
    def validate(self, attrs):
        league = attrs.get("league")
        team = attrs.get("first_place_team")
        if team.league != league:
            raise serializers.ValidationError("Team must belong to the selected league.")
        return attrs

    def create(self, validated_data):
        profile = self.context["request"].user.profile
        prediction, created = Prediction.objects.update_or_create(
            profile=profile,
            league=validated_data["league"],
            defaults={"first_place_team": validated_data["first_place_team"]},
        )
        return prediction


class LeagueResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeagueResult
        fields = "__all__"
