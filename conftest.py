"""
Pytest configuration and shared fixtures.
Place this file in your project root directory.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import Profile
from League.models import League, Team, Prediction, LeagueResult

User = get_user_model()


# ============================================
# User & Authentication Fixtures
# ============================================

@pytest.fixture
def user(db):
    """Create a regular verified user"""
    return User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        is_verified=True
    )


@pytest.fixture
def unverified_user(db):
    """Create an unverified user"""
    return User.objects.create_user(
        email="unverified@example.com",
        password="testpass123",
        is_verified=False
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    return User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass123"
    )


@pytest.fixture
def user_profile(user):
    """Get or create profile for user"""
    return user.profile


@pytest.fixture
def second_user(db):
    """Create a second verified user for testing"""
    return User.objects.create_user(
        email="testuser2@example.com",
        password="testpass123",
        is_verified=True
    )


# ============================================
# API Client Fixtures
# ============================================

@pytest.fixture
def api_client():
    """Return a DRF API client"""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an authenticated admin API client"""
    api_client.force_authenticate(user=admin_user)
    return api_client


# ============================================
# League & Team Fixtures
# ============================================

@pytest.fixture
def league(db):
    """Create a test league"""
    return League.objects.create(
        name="Premier League",
        is_active=True,
        first_place_points=20,
        second_place_points=15,
        third_place_points=10,
        fourth_place_points=7,
        fifth_place_points=5,
        sixth_place_points=3
    )


@pytest.fixture
def league_with_custom_points(db):
    """Create a league with custom points"""
    return League.objects.create(
        name="Champions League",
        is_active=True,
        first_place_points=30,
        second_place_points=20,
        third_place_points=15,
        fourth_place_points=10,
        fifth_place_points=7,
        sixth_place_points=5
    )


@pytest.fixture
def inactive_league(db):
    """Create an inactive league"""
    return League.objects.create(
        name="Inactive League",
        is_active=False,
        first_place_points=20,
        second_place_points=15,
        third_place_points=10,
        fourth_place_points=7,
        fifth_place_points=5,
        sixth_place_points=3
    )


@pytest.fixture
def teams(db, league):
    """Create 6 teams for a league (needed for 1st-6th place results)"""
    team_names = ["Team A", "Team B", "Team C", "Team D", "Team E", "Team F"]
    return [
        Team.objects.create(name=name, league=league)
        for name in team_names
    ]


@pytest.fixture
def team_a(teams):
    return teams[0]


@pytest.fixture
def team_b(teams):
    return teams[1]


@pytest.fixture
def team_c(teams):
    return teams[2]


# ============================================
# Prediction Fixtures
# ============================================

@pytest.fixture
def prediction(db, user_profile, league, teams):
    """Create a prediction (user predicts one team)"""
    return Prediction.objects.create(
        profile=user_profile,
        league=league,
        predicted_team=teams[0],
    )


@pytest.fixture
def multiple_predictions(db, user_profile, second_user, league, teams):
    """Create predictions for multiple users"""
    pred1 = Prediction.objects.create(
        profile=user_profile,
        league=league,
        predicted_team=teams[0],
    )
    
    pred2 = Prediction.objects.create(
        profile=second_user.profile,
        league=league,
        predicted_team=teams[1],
    )
    
    return [pred1, pred2]


# ============================================
# League Result Fixtures
# ============================================

@pytest.fixture
def league_result(db, league, teams):
    """Create a league result with 1st-6th place"""
    return LeagueResult.objects.create(
        league=league,
        first_place=teams[0],
        second_place=teams[1],
        third_place=teams[2],
        fourth_place=teams[3],
        fifth_place=teams[4],
        sixth_place=teams[5],
    )


# ============================================
# Factory Fixtures
# ============================================

@pytest.fixture
def user_factory(db):
    """Factory to create multiple users"""
    def create_user(email=None, password="testpass123", is_verified=True):
        if email is None:
            import uuid
            email = f"user{uuid.uuid4().hex[:8]}@example.com"
        return User.objects.create_user(
            email=email,
            password=password,
            is_verified=is_verified
        )
    return create_user


@pytest.fixture
def team_factory(db):
    """Factory to create multiple teams"""
    def create_team(name, league):
        return Team.objects.create(name=name, league=league)
    return create_team