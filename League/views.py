from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import League, Team, Prediction, LeagueResult
from .serializers import (
    LeagueSerializer,
    TeamSerializer,
    PredictionSerializer,
    LeagueResultSerializer,
)
from django.db.models import Sum, F
from accounts.models import Profile


class LeagueListView(generics.ListAPIView):
    """List all active leagues with their teams"""
    queryset = League.objects.filter(is_active=True).prefetch_related("teams")
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]


class TeamListView(generics.ListAPIView):
    """List teams for a specific league"""
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        league_id = self.kwargs.get("league_id")
        return Team.objects.filter(league_id=league_id)


class PredictionCreateUpdateView(generics.CreateAPIView):
    """Create or update a prediction for a league"""
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prediction = serializer.save()
        
        return Response(
            {
                "message": "Prediction saved successfully",
                "prediction": PredictionSerializer(prediction).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PredictionListView(generics.ListAPIView):
    """List all predictions for the current user"""
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Prediction.objects.filter(
            profile=self.request.user.profile
        ).select_related(
            "league",
            "first_place_team",
            "second_place_team",
            "third_place_team",
        )


class LeagueResultUpdateView(generics.UpdateAPIView):
    """Admin only - Update league results and recalculate all prediction points"""
    queryset = LeagueResult.objects.all()
    serializer_class = LeagueResultSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        result = serializer.save()
        # Points are automatically recalculated by the signal


class LeagueResultCreateView(generics.CreateAPIView):
    """Admin only - Create league result"""
    queryset = LeagueResult.objects.all()
    serializer_class = LeagueResultSerializer
    permission_classes = [permissions.IsAdminUser]


class LeaderboardView(generics.ListAPIView):
    """Get leaderboard showing all users ranked by total points"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        leaderboard = (
            Profile.objects.annotate(total_points=Sum("predictions__points"))
            .order_by("-total_points")
            .values(
                "id",
                "user__email",
                "first_name",
                "last_name",
                "total_points",
                "image",
            )
        )
        
        # Add rank
        leaderboard_list = list(leaderboard)
        for idx, entry in enumerate(leaderboard_list, start=1):
            entry["rank"] = idx
            # Handle None values
            if entry["total_points"] is None:
                entry["total_points"] = 0
        
        return Response(leaderboard_list)


class LeagueLeaderboardView(generics.ListAPIView):
    """Get leaderboard for a specific league"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, league_id, *args, **kwargs):
        predictions = (
            Prediction.objects.filter(league_id=league_id)
            .select_related("profile__user")
            .order_by("-points")
            .values(
                "profile__id",
                "profile__user__email",
                "profile__first_name",
                "profile__last_name",
                "points",
                "first_place_team__name",
                "second_place_team__name",
                "third_place_team__name",
            )
        )
        
        predictions_list = list(predictions)
        for idx, entry in enumerate(predictions_list, start=1):
            entry["rank"] = idx
        
        return Response(predictions_list)