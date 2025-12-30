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
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce
from accounts.models import Profile
from django.shortcuts import get_object_or_404


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


class PredictionCreateUpdateView(generics.CreateAPIView, generics.UpdateAPIView):
    """Create or update a prediction for a league"""
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get existing prediction for the user and league if it exists"""
        profile = getattr(self.request.user, 'profile', None)
        if not profile:
            return None
        try:
            return Prediction.objects.get(
                profile=profile,
                league_id=self.request.data.get('league')
            )
        except (Prediction.DoesNotExist, KeyError):
            return None

    def post(self, request, *args, **kwargs):
        # Check if prediction already exists
        existing_prediction = self.get_object()
        
        if existing_prediction:
            # Update existing prediction
            serializer = self.get_serializer(existing_prediction, data=request.data)
            serializer.is_valid(raise_exception=True)
            prediction = serializer.save()
            status_code = status.HTTP_200_OK
            message = "Prediction updated successfully"
        else:
            # Create new prediction
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            prediction = serializer.save()
            status_code = status.HTTP_201_CREATED
            message = "Prediction saved successfully"
        
        return Response(
            {
                "message": message,
                "prediction": PredictionSerializer(prediction).data,
            },
            status=status_code,
        )


class PredictionListView(generics.ListAPIView):
    """List all predictions for the current user"""
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile = getattr(self.request.user, 'profile', None)
        if not profile:
            return Prediction.objects.none()
        return Prediction.objects.filter(
            profile=profile
        ).select_related(
            "league",
            "predicted_team",
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
            Profile.objects.select_related("user")
            .annotate(
                total_points=Coalesce(Sum("predictions__points"), Value(0))
            )
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
        
        return Response(leaderboard_list)


class LeagueLeaderboardView(generics.ListAPIView):
    """Get leaderboard for a specific league"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, league_id, *args, **kwargs):
        predictions = (
            Prediction.objects.filter(league_id=league_id)
            .select_related(
                "profile__user",
                "predicted_team"
            )
            .order_by("-points")
            .values(
                "profile__id",
                "profile__user__email",
                "profile__first_name",
                "profile__last_name",
                "points",
                "predicted_team__name",
            )
        )
        
        predictions_list = list(predictions)
        for idx, entry in enumerate(predictions_list, start=1):
            entry["rank"] = idx
        
        return Response(predictions_list)