"""
Tests for League models: League, Team, Prediction, LeagueResult
"""
import pytest
from django.core.exceptions import ValidationError
from League.models import League, Team, Prediction, LeagueResult


@pytest.mark.unit
@pytest.mark.league
class TestLeagueModel:
    """Test League model"""

    def test_create_league(self, db):
        """Test creating a league"""
        league = League.objects.create(
            name="Test League",
            is_active=True,
            first_place_points=15,
            second_place_points=8,
            third_place_points=4,
        )
        
        assert league.name == "Test League"
        assert league.is_active is True
        assert league.first_place_points == 15
        assert league.second_place_points == 8
        assert league.third_place_points == 4
        assert str(league) == "Test League"

    def test_league_default_points(self, db):
        """Test league with default points"""
        league = League.objects.create(name="Default League")
        
        assert league.first_place_points == 10
        assert league.second_place_points == 5
        assert league.third_place_points == 3

    def test_league_custom_points(self, league_with_custom_points):
        """Test league with custom points"""
        assert league_with_custom_points.first_place_points == 20
        assert league_with_custom_points.second_place_points == 10
        assert league_with_custom_points.third_place_points == 5


@pytest.mark.unit
@pytest.mark.league
class TestTeamModel:
    """Test Team model"""

    def test_create_team(self, league):
        """Test creating a team"""
        team = Team.objects.create(
            name="Test Team",
            league=league
        )
        
        assert team.name == "Test Team"
        assert team.league == league
        assert str(team) == f"Test Team ({league.name})"

    def test_team_league_relationship(self, league, teams):
        """Test team-league relationship"""
        assert league.teams.count() == 5
        assert all(team.league == league for team in teams)


@pytest.mark.unit
@pytest.mark.prediction
class TestPredictionModel:
    """Test Prediction model"""

    def test_create_prediction(self, user_profile, league, teams):
        """Test creating a prediction"""
        prediction = Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        assert prediction.profile == user_profile
        assert prediction.league == league
        assert prediction.first_place_team == teams[0]
        assert prediction.second_place_team == teams[1]
        assert prediction.third_place_team == teams[2]
        assert prediction.points == 0  # Default

    def test_prediction_unique_together(self, user_profile, league, teams):
        """Test that user can only have one prediction per league"""
        Prediction.objects.create(
            profile=user_profile,
            league=league,
            first_place_team=teams[0],
            second_place_team=teams[1],
            third_place_team=teams[2],
        )
        
        # Try to create another prediction for same user and league
        with pytest.raises(Exception):  # IntegrityError
            Prediction.objects.create(
                profile=user_profile,
                league=league,
                first_place_team=teams[1],
                second_place_team=teams[0],
                third_place_team=teams[2],
            )

    def test_prediction_teams_must_be_from_league(self, user_profile, league, db):
        """Test validation: teams must belong to the league"""
        # Create team from different league
        other_league = League.objects.create(name="Other League")
        other_team = Team.objects.create(name="Other Team", league=other_league)
        
        team_a = Team.objects.create(name="Team A", league=league)
        team_b = Team.objects.create(name="Team B", league=league)
        
        # Try to create prediction with team from wrong league
        with pytest.raises(ValidationError):
            prediction = Prediction(
                profile=user_profile,
                league=league,
                first_place_team=other_team,  # Wrong league!
                second_place_team=team_a,
                third_place_team=team_b,
            )
            prediction.save()

    def test_prediction_teams_must_be_different(self, user_profile, league, teams):
        """Test validation: all three teams must be different"""
        with pytest.raises(ValidationError):
            prediction = Prediction(
                profile=user_profile,
                league=league,
                first_place_team=teams[0],
                second_place_team=teams[0],  # Same as first!
                third_place_team=teams[2],
            )
            prediction.save()

    def test_prediction_str_representation(self, prediction):
        """Test prediction string representation"""
        assert prediction.league.name in str(prediction)
        assert prediction.profile.user.email in str(prediction)


@pytest.mark.unit
@pytest.mark.league
class TestLeagueResultModel:
    """Test LeagueResult model"""

    def test_create_league_result(self, league, teams):
        """Test creating a league result"""
        result = LeagueResult.objects.create(
            league=league,
            first_place=teams[0],
            second_place=teams[1],
            third_place=teams[2],
        )
        
        assert result.league == league
        assert result.first_place == teams[0]
        assert result.second_place == teams[1]
        assert result.third_place == teams[2]

    def test_league_result_one_per_league(self, league, teams):
        """Test that each league can only have one result"""
        LeagueResult.objects.create(
            league=league,
            first_place=teams[0],
            second_place=teams[1],
            third_place=teams[2],
        )
        
        # Try to create another result for same league
        with pytest.raises(Exception):  # IntegrityError
            LeagueResult.objects.create(
                league=league,
                first_place=teams[1],
                second_place=teams[0],
                third_place=teams[2],
            )

    def test_league_result_teams_must_be_from_league(self, league, db):
        """Test validation: result teams must belong to the league"""
        other_league = League.objects.create(name="Other League")
        other_team = Team.objects.create(name="Other Team", league=other_league)
        
        team_a = Team.objects.create(name="Team A", league=league)
        team_b = Team.objects.create(name="Team B", league=league)
        
        with pytest.raises(ValidationError):
            result = LeagueResult(
                league=league,
                first_place=other_team,  # Wrong league!
                second_place=team_a,
                third_place=team_b,
            )
            result.save()

    def test_league_result_teams_must_be_different(self, league, teams):
        """Test validation: all three result teams must be different"""
        with pytest.raises(ValidationError):
            result = LeagueResult(
                league=league,
                first_place=teams[0],
                second_place=teams[0],  # Same as first!
                third_place=teams[2],
            )
            result.save()

    def test_league_result_str_representation(self, league_result):
        """Test result string representation"""
        assert league_result.league.name in str(league_result)