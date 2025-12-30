"""
Tests for the scoring system.
"""
import pytest
from League.services.scoring import calculate_points
from League.models import League, Team, Prediction, LeagueResult


@pytest.mark.unit
@pytest.mark.league
class TestScoringSystem:
    """Test the points calculation system"""

    def test_calculate_points_first_place(self, user_profile, league, teams):
        """Test when predicted team finishes 1st"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=teams[0],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[0],  # Predicted team finished 1st
            second_place=teams[1],
            third_place=teams[2],
            fourth_place=teams[3],
            fifth_place=teams[4],
            sixth_place=teams[5],
        )
        
        points = calculate_points(prediction, result)
        assert points == league.first_place_points  # 20

    def test_calculate_points_second_place(self, user_profile, league, teams):
        """Test when predicted team finishes 2nd"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=teams[0],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[1],
            second_place=teams[0],  # Predicted team finished 2nd
            third_place=teams[2],
            fourth_place=teams[3],
            fifth_place=teams[4],
            sixth_place=teams[5],
        )
        
        points = calculate_points(prediction, result)
        assert points == league.second_place_points  # 15

    def test_calculate_points_third_place(self, user_profile, league, teams):
        """Test when predicted team finishes 3rd"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=teams[0],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[1],
            second_place=teams[2],
            third_place=teams[0],  # Predicted team finished 3rd
            fourth_place=teams[3],
            fifth_place=teams[4],
            sixth_place=teams[5],
        )
        
        points = calculate_points(prediction, result)
        assert points == league.third_place_points  # 10

    def test_calculate_points_fourth_place(self, user_profile, league, teams):
        """Test when predicted team finishes 4th"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=teams[0],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[1],
            second_place=teams[2],
            third_place=teams[3],
            fourth_place=teams[0],  # Predicted team finished 4th
            fifth_place=teams[4],
            sixth_place=teams[5],
        )
        
        points = calculate_points(prediction, result)
        assert points == league.fourth_place_points  # 7

    def test_calculate_points_fifth_place(self, user_profile, league, teams):
        """Test when predicted team finishes 5th"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=teams[0],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[1],
            second_place=teams[2],
            third_place=teams[3],
            fourth_place=teams[4],
            fifth_place=teams[0],  # Predicted team finished 5th
            sixth_place=teams[5],
        )
        
        points = calculate_points(prediction, result)
        assert points == league.fifth_place_points  # 5

    def test_calculate_points_sixth_place(self, user_profile, league, teams):
        """Test when predicted team finishes 6th"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=teams[0],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[1],
            second_place=teams[2],
            third_place=teams[3],
            fourth_place=teams[4],
            fifth_place=teams[5],
            sixth_place=teams[0],  # Predicted team finished 6th
        )
        
        points = calculate_points(prediction, result)
        assert points == league.sixth_place_points  # 3

    def test_calculate_points_not_in_top_six(self, user_profile, league, teams):
        """Test when predicted team doesn't finish in top 6"""
        # Create additional team that won't be in top 6
        extra_team = Team.objects.create(name="Extra Team", league=league)
        
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=extra_team,
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[0],
            second_place=teams[1],
            third_place=teams[2],
            fourth_place=teams[3],
            fifth_place=teams[4],
            sixth_place=teams[5],
        )
        
        points = calculate_points(prediction, result)
        assert points == 0  # Team not in top 6

    def test_calculate_points_custom_league_points(
        self, user_profile, league_with_custom_points, db
    ):
        """Test scoring with custom league points"""
        # Create teams for custom league
        teams = [
            Team.objects.create(name=f"Team {i}", league=league_with_custom_points)
            for i in range(6)
        ]
        
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league_with_custom_points,
            predicted_team=teams[0],
        )
        
        result = LeagueResult.objects.create(
            league=league_with_custom_points,
            first_place=teams[0],  # Finished 1st
            second_place=teams[1],
            third_place=teams[2],
            fourth_place=teams[3],
            fifth_place=teams[4],
            sixth_place=teams[5],
        )
        
        points = calculate_points(prediction, result)
        assert points == 30  # Custom league: 1st place = 30 points


@pytest.mark.integration
@pytest.mark.league
class TestScoringIntegration:
    """Test scoring system integration with signals"""

    def test_points_auto_calculated_on_result_save(
        self, user_profile, league, teams
    ):
        """Test that points are automatically calculated when result is saved"""
        # Create prediction (user predicts team will finish 1st)
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=teams[0],
        )
        
        assert prediction.points == 0  # Initially 0
        
        # Create result (team finishes 1st - signal should trigger)
        LeagueResult.objects.create(
            league=league,
            first_place=teams[0],  # Predicted team finished 1st
            second_place=teams[1],
            third_place=teams[2],
            fourth_place=teams[3],
            fifth_place=teams[4],
            sixth_place=teams[5],
        )
        
        # Refresh prediction from database
        prediction.refresh_from_db()
        
        # Points should be auto-calculated (1st place = 20 points)
        assert prediction.points == league.first_place_points  # 20

    def test_points_recalculated_on_result_update(
        self, user_profile, league, teams
    ):
        """Test that points are recalculated when result is updated"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=teams[0],
        )
        
        # Create initial result (team finishes 1st)
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[0],  # Predicted team finished 1st
            second_place=teams[1],
            third_place=teams[2],
            fourth_place=teams[3],
            fifth_place=teams[4],
            sixth_place=teams[5],
        )
        
        prediction.refresh_from_db()
        initial_points = prediction.points
        assert initial_points == 20  # 1st place
        
        # Update result (team now finishes 2nd)
        result.first_place = teams[1]
        result.second_place = teams[0]  # Predicted team now 2nd
        result.save()
        
        prediction.refresh_from_db()
        # Now team finished 2nd
        assert prediction.points == league.second_place_points  # 15

    def test_multiple_predictions_scored_correctly(
        self, user_profile, second_user, league, teams
    ):
        """Test that multiple users' predictions are scored independently"""
        # User 1 prediction (predicts teams[0])
        pred1 = Prediction.objects.create(
            profile=user_profile,
            league=league,
            predicted_team=teams[0],
        )
        
        # User 2 prediction (predicts teams[1])
        pred2 = Prediction.objects.create(
            profile=second_user.profile,
            league=league,
            predicted_team=teams[1],
        )
        
        # Create result
        LeagueResult.objects.create(
            league=league,
            first_place=teams[0],  # User 1's team finished 1st
            second_place=teams[1],  # User 2's team finished 2nd
            third_place=teams[2],
            fourth_place=teams[3],
            fifth_place=teams[4],
            sixth_place=teams[5],
        )
        
        pred1.refresh_from_db()
        pred2.refresh_from_db()
        
        # User 1's team finished 1st
        assert pred1.points == 20
        
        # User 2's team finished 2nd
        assert pred2.points == 15