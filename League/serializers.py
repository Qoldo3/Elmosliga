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
            "fourth_place_points",
            "fifth_place_points",
            "sixth_place_points",
            "teams",
        )


class PredictionSerializer(serializers.ModelSerializer):
    predicted_team_name = serializers.CharField(
        source="predicted_team.name", read_only=True
    )
    league_name = serializers.CharField(source="league.name", read_only=True)

    class Meta:
        model = Prediction
        fields = (
            "id",
            "league",
            "league_name",
            "predicted_team",
            "predicted_team_name",
            "points",
            "is_predicted",  # NEW FIELD
            "created_at",
            "updated_at",
        )
        read_only_fields = ("points", "is_predicted", "created_at", "updated_at")

    def validate(self, attrs):
        league = attrs.get("league")
        predicted_team = attrs.get("predicted_team")
        
        # Get the request from context
        request = self.context.get("request")
        profile = getattr(request.user, 'profile', None)

        if not predicted_team:
            raise serializers.ValidationError("Predicted team is required")

        # Check team belongs to the league
        if predicted_team.league != league:
            raise serializers.ValidationError(
                f"Team {predicted_team.name} must belong to {league.name}"
            )

        # Check if league is active
        if not league.is_active:
            raise serializers.ValidationError(
                "Cannot make predictions for inactive leagues"
            )
        
        # NEW: Check if user has already predicted for this league
        if self.instance is None:  # Only for creation
            existing_prediction = Prediction.objects.filter(
                profile=profile,
                league=league,
                is_predicted=True
            ).first()
            
            if existing_prediction:
                raise serializers.ValidationError(
                    "You have already made a prediction for this league and cannot change it."
                )

        # NEW: For updates, check if already predicted
        if self.instance and self.instance.is_predicted:
            raise serializers.ValidationError(
                "You have already made a prediction for this league and cannot change it."
            )

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        profile = getattr(user, 'profile', None)
        if not profile:
            from accounts.models import Profile
            profile = Profile.objects.create(user=user)
        
        # Mark as predicted when creating
        validated_data['is_predicted'] = True
        
        prediction, created = Prediction.objects.update_or_create(
            profile=profile,
            league=validated_data["league"],
            defaults={
                "predicted_team": validated_data["predicted_team"],
                "is_predicted": True,
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
    fourth_place_name = serializers.CharField(
        source="fourth_place.name", read_only=True
    )
    fifth_place_name = serializers.CharField(
        source="fifth_place.name", read_only=True
    )
    sixth_place_name = serializers.CharField(
        source="sixth_place.name", read_only=True
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
            "fourth_place",
            "fourth_place_name",
            "fifth_place",
            "fifth_place_name",
            "sixth_place",
            "sixth_place_name",
            "updated_at",
        )

    def validate(self, attrs):
        league = attrs.get("league", self.instance.league if self.instance else None)
        first = attrs.get("first_place", self.instance.first_place if self.instance else None)
        second = attrs.get("second_place", self.instance.second_place if self.instance else None)
        third = attrs.get("third_place", self.instance.third_place if self.instance else None)
        fourth = attrs.get("fourth_place", self.instance.fourth_place if self.instance else None)
        fifth = attrs.get("fifth_place", self.instance.fifth_place if self.instance else None)
        sixth = attrs.get("sixth_place", self.instance.sixth_place if self.instance else None)

        if not league:
            raise serializers.ValidationError("League is required")

        teams = [first, second, third, fourth, fifth, sixth]
        
        # Filter out None values for validation
        valid_teams = [team for team in teams if team is not None]
        
        # Check all teams belong to the league
        for team in valid_teams:
            if team.league != league:
                raise serializers.ValidationError(
                    f"Team {team.name} must belong to {league.name}"
                )

        # Check all teams are different and all six are provided
        if len(valid_teams) != 6:
            raise serializers.ValidationError("All six teams must be provided")
        
        if len(set(valid_teams)) != 6:
            raise serializers.ValidationError(
                "All six teams must be different"
            )

        return attrs