from django.urls import path
from League import views

urlpatterns = [
    # Leagues
    path("leagues/", views.LeagueListView.as_view(), name="league-list"),
    path("leagues/<int:league_id>/teams/", views.TeamListView.as_view(), name="team-list"),
    
    # Predictions
    path("prediction/", views.PredictionCreateUpdateView.as_view(), name="prediction-create"),
    path("predictions/", views.PredictionListView.as_view(), name="prediction-list"),
    path("predictions/check/<int:league_id>/", views.CheckPredictionView.as_view(), name="prediction-check"),
    
    # Results (Admin only)
    path("admin/results/", views.LeagueResultListView.as_view(), name="result-list"),
    path("admin/result/create/", views.LeagueResultCreateView.as_view(), name="result-create"),
    path("admin/result/<int:pk>/", views.LeagueResultUpdateView.as_view(), name="result-update"),
    path("admin/result/<int:pk>/delete/", views.LeagueResultDeleteView.as_view(), name="result-delete"),
    
    # Leaderboards
    path("leaderboard/", views.LeaderboardView.as_view(), name="leaderboard-global"),
    path("leaderboard/<int:league_id>/", views.LeagueLeaderboardView.as_view(), name="leaderboard-league"),
]