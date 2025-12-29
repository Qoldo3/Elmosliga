from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from mail_templated import EmailMessage
from .utils import EmailThread
from .serializers import (
    RegisterSerializer,
    CustomTokenSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    ProfileSerializer,
    ResendActivationEmailSerializer,
    ResetPasswordSerializerConfirm,
    ResetPasswordSerializer,
)
from accounts.models import (
    Profile,
    EmailVerificationToken,
    PasswordResetToken,
)

from rest_framework.authtoken.models import Token
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    # User Registration View
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            verification_token = EmailVerificationToken.create_token(user)
            email = serializer.validated_data["email"]
            data = {
                "email": email,
            }
            user_obj = get_object_or_404(get_user_model(), email=email)

            email_obj = EmailMessage(
                "email/Activation.tpl",
                {"token": verification_token.token},
                settings.EMAIL_HOST_USER,
                to=[email],
            )
            EmailThread(email_obj).start()
            return Response(
                {
                    "message": "User registered successfully",
                    "Email": serializer.data["email"],
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomToken(ObtainAuthToken):
    serializer_class = CustomTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk, "email": user.email})


class LogoutView(APIView):
    # Logout View to delete the token
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(
            {"message": "Successfully logged out."}, status=status.HTTP_200_OK
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class ChangePasswordApiView(generics.GenericAPIView):
    model = get_user_model()
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def get_object(self, queryset=None):
        return self.request.user

    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response(
                {"details": "password changed successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    # Profile View to get user profile data
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, user=self.request.user)
        return obj


class ActivateAccountView(APIView):
    def get(self, request, token, *args, **kwargs):
        # decode JWT token to get user ID and activate account
        try:
            verification_token = EmailVerificationToken.objects.get(token=token)
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"error": "Activation link has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not verification_token.is_valid():
            if verification_token.used:
                return Response(
                    {"error": "This activation link has already been used."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"error": "Activation link has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        user = verification_token.user
        if user.is_verified:
            return Response(
                {"message": "Account is already activated."}, status=status.HTTP_200_OK
            )
        user.is_verified = True
        user.save()
        verification_token.mark_as_used()

        return Response(
            {"message": "Account activated successfully."}, status=status.HTTP_200_OK
        )


class ResendActivationEmailView(generics.GenericAPIView):
    serializer_class = ResendActivationEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = serializer.validated_data["user"]
        verification_token = EmailVerificationToken.create_token(user_obj)
        email_obj = EmailMessage(
            "email/Activation.tpl",
            {"token": verification_token.token},
            settings.EMAIL_HOST_USER,
            to=[user_obj.email],
        )
        EmailThread(email_obj).start()
        return Response(
            {"message": "If the email exists, an email has been sent.."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = serializer.validated_data["user"]
        reset_token = PasswordResetToken.create_token(user_obj)
        email_obj = EmailMessage(
            "email/ResetPass.tpl",
            {"token": reset_token.token},
            settings.EMAIL_HOST_USER,
            to=[user_obj.email],
        )
        EmailThread(email_obj).start()

        return Response(
            {"message": "Password reset email sent."}, status=status.HTTP_200_OK
        )


class ResetPasswordConfirmView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializerConfirm

    def post(self, request, token, *args, **kwargs):
        # decode JWT token to get user ID and reset password
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"error": "Invalid password reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not reset_token.is_valid():
            if reset_token.used:
                return Response(
                    {"error": "This password reset link has already been used."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"error": "Password reset link has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        user_obj = reset_token.user
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_obj.set_password(serializer.data.get("new_password"))
            user_obj.save()
            reset_token.mark_as_used()
            return Response(
                {"message": "Password reset successfully."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
