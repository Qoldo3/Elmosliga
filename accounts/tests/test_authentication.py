"""
Tests for user authentication, registration, and account management.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import EmailVerificationToken, PasswordResetToken

User = get_user_model()


@pytest.mark.auth
class TestUserRegistration:
    """Test user registration"""

    def test_register_user_success(self, api_client, db):
        """Test successful user registration"""
        url = reverse("accounts-v1:register")
        data = {
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "password1": "StrongPass123!",
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "Email" in response.data
        assert User.objects.filter(email="newuser@example.com").exists()
        
        # User should not be verified initially
        user = User.objects.get(email="newuser@example.com")
        assert not user.is_verified
        
        # Verification token should be created
        assert EmailVerificationToken.objects.filter(user=user).exists()

    def test_register_user_password_mismatch(self, api_client, db):
        """Test registration with mismatched passwords"""
        url = reverse("accounts-v1:register")
        data = {
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "password1": "DifferentPass123!",
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not User.objects.filter(email="newuser@example.com").exists()

    def test_register_user_weak_password(self, api_client, db):
        """Test registration with weak password"""
        url = reverse("accounts-v1:register")
        data = {
            "email": "newuser@example.com",
            "password": "123",
            "password1": "123",
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not User.objects.filter(email="newuser@example.com").exists()

    def test_register_duplicate_email(self, api_client, user):
        """Test registration with existing email"""
        url = reverse("accounts-v1:register")
        data = {
            "email": user.email,
            "password": "StrongPass123!",
            "password1": "StrongPass123!",
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.auth
class TestAccountActivation:
    """Test account activation"""

    def test_activate_account_success(self, api_client, unverified_user):
        """Test successful account activation"""
        # Create verification token
        token = EmailVerificationToken.create_token(unverified_user)
        
        url = reverse("accounts-v1:activate-account", kwargs={"token": token.token})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # User should now be verified
        unverified_user.refresh_from_db()
        assert unverified_user.is_verified
        
        # Token should be marked as used
        token.refresh_from_db()
        assert token.used

    def test_activate_account_invalid_token(self, api_client):
        """Test activation with invalid token"""
        url = reverse("accounts-v1:activate-account", kwargs={"token": "invalid_token"})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_activate_account_already_activated(self, api_client, user):
        """Test activation for already verified user"""
        token = EmailVerificationToken.create_token(user)
        
        url = reverse("accounts-v1:activate-account", kwargs={"token": token.token})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert "already activated" in response.data["message"].lower()


@pytest.mark.auth
class TestJWTAuthentication:
    """Test JWT token authentication"""

    def test_jwt_login_success(self, api_client, user):
        """Test successful JWT login"""
        url = reverse("accounts-v1:jwt-create")
        data = {
            "email": user.email,
            "password": "testpass123",
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user_id" in response.data
        assert response.data["email"] == user.email

    def test_jwt_login_unverified_user(self, api_client, unverified_user):
        """Test JWT login with unverified user"""
        url = reverse("accounts-v1:jwt-create")
        data = {
            "email": unverified_user.email,
            "password": "testpass123",
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_jwt_login_wrong_password(self, api_client, user):
        """Test JWT login with wrong password"""
        url = reverse("accounts-v1:jwt-create")
        data = {
            "email": user.email,
            "password": "wrongpassword",
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_jwt_refresh_token(self, api_client, user):
        """Test JWT refresh token"""
        # First login to get tokens
        login_url = reverse("accounts-v1:jwt-create")
        login_data = {
            "email": user.email,
            "password": "testpass123",
        }
        login_response = api_client.post(login_url, login_data)
        refresh_token = login_response.data["refresh"]
        
        # Now refresh the token
        refresh_url = reverse("accounts-v1:token_refresh")
        refresh_data = {"refresh": refresh_token}
        response = api_client.post(refresh_url, refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data


@pytest.mark.auth
class TestPasswordManagement:
    """Test password change and reset"""

    def test_change_password_success(self, authenticated_client, user):
        """Test successful password change"""
        url = reverse("accounts-v1:password-change")
        data = {
            "old_password": "testpass123",
            "new_password": "NewStrongPass123!",
            "new_password1": "NewStrongPass123!",
        }
        response = authenticated_client.put(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password("NewStrongPass123!")

    def test_change_password_wrong_old_password(self, authenticated_client):
        """Test password change with wrong old password"""
        url = reverse("accounts-v1:password-change")
        data = {
            "old_password": "wrongpassword",
            "new_password": "NewStrongPass123!",
            "new_password1": "NewStrongPass123!",
        }
        response = authenticated_client.put(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_password_request(self, api_client, user):
        """Test password reset request"""
        url = reverse("accounts-v1:password-reset")
        data = {"email": user.email}
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert PasswordResetToken.objects.filter(user=user).exists()

    def test_reset_password_confirm(self, api_client, user):
        """Test password reset confirmation"""
        # Create reset token
        token = PasswordResetToken.create_token(user)
        
        url = reverse(
            "accounts-v1:password-reset-confirm",
            kwargs={"token": token.token}
        )
        data = {
            "new_password": "NewResetPass123!",
            "new_password1": "NewResetPass123!",
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password("NewResetPass123!")


@pytest.mark.auth
class TestProfile:
    """Test user profile operations"""

    def test_get_profile(self, authenticated_client, user_profile):
        """Test getting user profile"""
        url = reverse("accounts-v1:profile")
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user_profile.user.email

    def test_update_profile(self, authenticated_client, user_profile):
        """Test updating user profile"""
        url = reverse("accounts-v1:profile")
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "description": "Test description",
        }
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        user_profile.refresh_from_db()
        assert user_profile.first_name == "John"
        assert user_profile.last_name == "Doe"

    def test_profile_created_on_user_creation(self, db):
        """Test that profile is automatically created with user"""
        user = User.objects.create_user(
            email="newuser@example.com",
            password="testpass123"
        )
        
        assert hasattr(user, "profile")
        assert user.profile.user == user