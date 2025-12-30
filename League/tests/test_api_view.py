"""
Tests for League API endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from django.db.models import Sum
from League.models import Prediction, LeagueResult


@pytest.mark.integration
@pytest.mark.league
class TestLeagueListAPI:
    """Test league listing endpoint"""

    def test_list_leagues_authenticated(self, authenticated_client, league, teams):
        """Test listing leagues as authenticated user"""
        url = reverse("league-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == league.name
        assert len(response.data[0]["teams"]) == 6

    def test_list_leagues_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list leagues"""
        url = reverse("league-list")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_only_active_leagues(
        self, authenticated_client, league, inactive_league
    ):
        """Test that only active leagues are returned"""
        url = reverse("league-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == league.name


@pytest.mark.integration
@pytest.mark.prediction
class TestPredictionAPI:
    """Test prediction creation and listing endpoints"""

    def test_create_prediction(self, authenticated_client, league, teams):
        """Test creating a prediction (user predicts one team)"""
        url = reverse("prediction-create")
        data = {
            "league": league.id,
            "predicted_team": teams[0].id,
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "prediction" in response.data
        assert response.data["prediction"]["points"] == 0
        assert response.data["prediction"]["predicted_team"] == teams[0].id

    def test_update_existing_prediction(
        self, authenticated_client, prediction, teams
    ):
        """Test updating an existing prediction"""
        url = reverse("prediction-create")
        data = {
            "league": prediction.league.id,
            "predicted_team": teams[1].id,  # Changed
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Should update, not create new
        prediction.refresh_from_db()
        assert prediction.predicted_team == teams[1]
        assert Prediction.objects.filter(league=prediction.league).count() == 1

    def test_create_prediction_team_must_be_from_league(
        self, authenticated_client, league, db
    ):
        """Test that predicted team must belong to the selected league"""
        from League.models import League, Team
        
        # Create another league with teams
        other_league = League.objects.create(name="Other League")
        other_team = Team.objects.create(name="Other Team", league=other_league)
        
        url = reverse("prediction-create")
        data = {
            "league": league.id,
            "predicted_team": other_team.id,  # Wrong league!
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_predict_inactive_league(
        self, authenticated_client, inactive_league, db
    ):
        """Test that predictions cannot be made for inactive leagues"""
        from League.models import Team
        
        team = Team.objects.create(name="Team A", league=inactive_league)
        
        url = reverse("prediction-create")
        data = {
            "league": inactive_league.id,
            "predicted_team": team.id,
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_user_predictions(self, authenticated_client, prediction):
        """Test listing user's predictions"""
        url = reverse("prediction-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["league"] == prediction.league.id


@pytest.mark.integration
@pytest.mark.league
class TestLeagueResultAPI:
    """Test league result management (admin only)"""

    def test_create_result_as_admin(self, admin_client, league, teams):
        """Test creating league result as admin (1st-6th place)"""
        url = reverse("result-create")
        data = {
            "league": league.id,
            "first_place": teams[0].id,
            "second_place": teams[1].id,
            "third_place": teams[2].id,
            "fourth_place": teams[3].id,
            "fifth_place": teams[4].id,
            "sixth_place": teams[5].id,
        }
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert LeagueResult.objects.filter(league=league).exists()

    def test_create_result_as_regular_user(
        self, authenticated_client, league, teams
    ):
        """Test that regular users cannot create results"""
        url = reverse("result-create")
        data = {
            "league": league.id,
            "first_place": teams[0].id,
            "second_place": teams[1].id,
            "third_place": teams[2].id,
            "fourth_place": teams[3].id,
            "fifth_place": teams[4].id,
            "sixth_place": teams[5].id,
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_result_as_admin(self, admin_client, league_result, teams):
        """Test updating league result as admin"""
        url = reverse("result-update", kwargs={"pk": league_result.pk})
        data = {
            "league": league_result.league.id,
            "first_place": teams[1].id,  # Changed
            "second_place": teams[0].id,  # Changed
            "third_place": teams[2].id,
            "fourth_place": teams[3].id,
            "fifth_place": teams[4].id,
            "sixth_place": teams[5].id,
        }
        response = admin_client.put(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        league_result.refresh_from_db()
        assert league_result.first_place == teams[1]


@pytest.mark.integration
@pytest.mark.league
class TestLeaderboardAPI:
    """Test leaderboard endpoints"""

    def test_global_leaderboard(
        self, authenticated_client, multiple_predictions, league_result
    ):
        """Test global leaderboard"""
        url = reverse("leaderboard-global")
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2
        assert "rank" in response.data[0]
        assert "total_points" in response.data[0]
        
        # Check ranking is correct (highest points first)
        if len(response.data) > 1:
            assert (
                response.data[0]["total_points"] >=
                response.data[1]["total_points"]
            )

    def test_league_leaderboard(
        self, authenticated_client, multiple_predictions, league_result, league
    ):
        """Test league-specific leaderboard"""
        url = reverse("leaderboard-league", kwargs={"league_id": league.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Two predictions
        assert "rank" in response.data[0]
        assert "points" in response.data[0]

    def test_leaderboard_requires_authentication(self, api_client):
        """Test that leaderboard requires authentication"""
        url = reverse("leaderboard-global")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_leaderboard_handles_users_with_no_predictions(
        self, authenticated_client, user_factory, db
    ):
        """Test leaderboard includes users with no predictions"""
        # Create user with no predictions
        user_factory(email="nopredictions@example.com")
        
        url = reverse("leaderboard-global")
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Users with no predictions should have 0 points
        users_with_zero = [u for u in response.data if u["total_points"] == 0]
        assert len(users_with_zero) >= 1


@pytest.mark.integration
@pytest.mark.league
class TestCompleteWorkflow:
    """Test complete prediction and scoring workflow"""

    def test_complete_prediction_workflow(
        self, authenticated_client, admin_client, league, teams, user
    ):
        """Test complete workflow: create prediction -> create result -> check points"""
        
        # Step 1: User creates prediction (predicts team will finish 1st)
        prediction_url = reverse("prediction-create")
        prediction_data = {
            "league": league.id,
            "predicted_team": teams[0].id,
        }
        pred_response = authenticated_client.post(prediction_url, prediction_data)
        assert pred_response.status_code == status.HTTP_201_CREATED
        assert "prediction" in pred_response.data
        
        # Get prediction ID from response
        prediction_id = pred_response.data["prediction"]["id"]
        
        # Step 2: Admin creates result (team finishes 1st)
        result_url = reverse("result-create")
        result_data = {
            "league": league.id,
            "first_place": teams[0].id,
            "second_place": teams[1].id,
            "third_place": teams[2].id,
            "fourth_place": teams[3].id,
            "fifth_place": teams[4].id,
            "sixth_place": teams[5].id,
        }
        result_response = admin_client.post(result_url, result_data)
        assert result_response.status_code == status.HTTP_201_CREATED
        
        # Step 3: Check prediction points were calculated
        # Use the prediction ID from the API response
        prediction = Prediction.objects.get(id=prediction_id)
        prediction.refresh_from_db()  # Ensure we have the latest data
        assert prediction.points == 20  # Team finished 1st: 20 points

        # Step 4: Check leaderboard
        # Use the email of the user who actually owns the prediction
        prediction_owner_email = prediction.profile.user.email

        leaderboard_url = reverse("leaderboard-global")
        leaderboard_response = authenticated_client.get(leaderboard_url)
        assert leaderboard_response.status_code == status.HTTP_200_OK

        # Prediction owner should be on leaderboard with correct points
        owner_entry = next(
            (u for u in leaderboard_response.data if u["user__email"] == prediction_owner_email),
            None,
        )
        assert (
            owner_entry is not None
        ), f"Prediction owner {prediction_owner_email} not found in leaderboard. Available users: {[u['user__email'] for u in leaderboard_response.data]}"

        # The leaderboard should show the total points from all predictions
        # Since we have one prediction with 20 points, total should be 20
        assert (
            owner_entry["total_points"] == 20
        ), f"Expected 20 points for {prediction_owner_email}, got {owner_entry['total_points']}. Leaderboard data: {leaderboard_response.data}"