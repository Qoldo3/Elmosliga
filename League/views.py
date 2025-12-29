from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import League, Team, Prediction, LeagueResult
from .serializers import LeagueSerializer, PredictionSerializer, LeagueResultSerializer
from django.db.models import Sum
from accounts.models import Profile


class LeagueListView(generics.ListAPIView):
    queryset = League.objects.filter(is_active=True)
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]


class PredictionCreateUpdateView(generics.CreateAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]


class LeagueResultUpdateView(generics.UpdateAPIView):
    queryset = LeagueResult.objects.all()
    serializer_class = LeagueResultSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        result = serializer.save()
        result.calculate_points()  # update points for predictions


class LeaderboardView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        leaderboard = (
            Profile.objects.annotate(total_points=Sum("predictions__points"))
            .order_by("-total_points")
            .values("user__email", "total_points")
        )
        return Response(leaderboard)
