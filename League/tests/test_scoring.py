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

    def test_calculate_points_all_correct(self, user_profile, league, teams):
        """Test when all three predictions are correct"""
        # Create prediction
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        # Create matching result
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[0],
            second_place=teams[1],
            third_place=teams[2],
        )
        
        points = calculate_points(prediction, result)
        expected = (
            league.first_place_points +
            league.second_place_points +
            league.third_place_points
        )
        assert points == expected  # 10 + 5 + 3 = 18

    def test_calculate_points_first_only(self, user_profile, league, teams):
        """Test when only first place is correct"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[0],  # Correct
            second_place=teams[2],  # Wrong
            third_place=teams[1],   # Wrong
        )
        
        points = calculate_points(prediction, result)
        assert points == league.first_place_points  # 10

    def test_calculate_points_second_only(self, user_profile, league, teams):
        """Test when only second place is correct"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[2],
            second_place=teams[1],  # Correct
            third_place=teams[0],
        )
        
        points = calculate_points(prediction, result)
        assert points == league.second_place_points  # 5

    def test_calculate_points_third_only(self, user_profile, league, teams):
        """Test when only third place is correct"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[1],
            second_place=teams[0],
            third_place=teams[2],  # Correct
        )
        
        points = calculate_points(prediction, result)
        assert points == league.third_place_points  # 3

    def test_calculate_points_none_correct(self, user_profile, league, teams):
        """Test when no predictions are correct"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[3],
            second_place=teams[4],
            third_place=teams[0],
        )
        
        points = calculate_points(prediction, result)
        assert points == 0

    def test_calculate_points_custom_league_points(
        self, user_profile, league_with_custom_points, db
    ):
        """Test scoring with custom league points (20, 10, 5)"""
        # Create teams for custom league
        teams = [
            Team.objects.create(name=f"Team {i}", league=league_with_custom_points)
            for i in range(5)
        ]
        
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league_with_custom_points,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        result = LeagueResult.objects.create(
            league=league_with_custom_points,
            first_place=teams[0],
            second_place=teams[1],
            third_place=teams[2],
        )
        
        points = calculate_points(prediction, result)
        assert points == 35  # 20 + 10 + 5

    def test_calculate_points_first_and_third(self, user_profile, league, teams):
        """Test when first and third are correct but not second"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[0],  # Correct
            second_place=teams[3],  # Wrong
            third_place=teams[2],   # Correct
        )
        
        points = calculate_points(prediction, result)
        expected = league.first_place_points + league.third_place_points
        assert points == expected  # 10 + 3 = 13


@pytest.mark.integration
@pytest.mark.league
class TestScoringIntegration:
    """Test scoring system integration with signals"""

    def test_points_auto_calculated_on_result_save(
        self, user_profile, league, teams
    ):
        """Test that points are automatically calculated when result is saved"""
        # Create prediction
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        assert prediction.points == 0  # Initially 0
        
        # Create result (signal should trigger)
        LeagueResult.objects.create(
            league=league,
            first_place=teams[0],
            second_place=teams[1],
            third_place=teams[2],
        )
        
        # Refresh prediction from database
        prediction.refresh_from_db()
        
        # Points should be auto-calculated
        expected = (
            league.first_place_points +
            league.second_place_points +
            league.third_place_points
        )
        assert prediction.points == expected

    def test_points_recalculated_on_result_update(
        self, user_profile, league, teams
    ):
        """Test that points are recalculated when result is updated"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        # Create initial result
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[0],
            second_place=teams[1],
            third_place=teams[2],
        )
        
        prediction.refresh_from_db()
        initial_points = prediction.points
        assert initial_points == 18  # All correct
        
        # Update result
        result.first_place = teams[3]  # Change first place
        result.save()
        
        prediction.refresh_from_db()
        # Now only second and third are correct
        expected = league.second_place_points + league.third_place_points
        assert prediction.points == expected  # 5 + 3 = 8

    def test_multiple_predictions_scored_correctly(
        self, user_profile, second_user, league, teams
    ):
        """Test that multiple users' predictions are scored independently"""
        # User 1 prediction
        pred1 = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        # User 2 prediction (different)
        pred2 = Prediction.objects.create(
            profile=second_user.profile,
            league=league,
            first_place_team=teams[1],
            second_place_team=teams[0],
            third_place_team=teams[2],
        )
        
        # Create result
        LeagueResult.objects.create(
            league=league,
            first_place=teams[0],  # Matches pred1
            second_place=teams[1],  # Matches pred1
            third_place=teams[2],  # Matches both
        )
        
        pred1.refresh_from_db()
        pred2.refresh_from_db()
        
        # User 1 got all correct
        assert pred1.points == 18
        
        # User 2 only got third correct
        assert pred2.points == 3