from django.urls import path
from League import views
urlpatterns = [
    path("leagues/", views.LeagueListView.as_view(), name="league-list"),
    path("prediction/", views.PredictionCreateUpdateView.as_view(), name="prediction"),
    path("league/<int:pk>/result/", views.LeagueResultUpdateView.as_view(), name="league-result"),
    path("leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
]
