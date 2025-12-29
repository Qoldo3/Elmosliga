from rest_framework import serializers
from accounts.models import User, Profile
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.shortcuts import get_object_or_404


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    # User Registration Serializer with password validation
    password = serializers.CharField(max_length=250, write_only=True)
    password1 = serializers.CharField(max_length=250, write_only=True)

    class Meta:
        model = User
        fields = ("email", "password", "password1")

    def validate(self, attrs):
        # Validate that the two passwords match and meet the password validation criteria
        if attrs["password"] != attrs["password1"]:
            raise serializers.ValidationError("Passwords do not match")
        try:
            validate_password(attrs.get("password"))
        except serializers.ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        return super().validate(attrs)

    def create(self, validated_data):
        # Create a new user with the validated data
        validated_data.pop("password1", None)
        return User.objects.create_user(**validated_data)


class CustomTokenSerializer(serializers.Serializer):
    # Custom Token Serializer to include user data along with token
    email = serializers.CharField(label=_("email"), write_only=True)
    password = serializers.CharField(
        label=_("Password"),
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )
    token = serializers.CharField(label=_("Token"), read_only=True)

    def validate(self, attrs):
        # Validate the user credentials
        username = attrs.get("email")
        password = attrs.get("password")

        if username and password:
            user = authenticate(
                request=self.context.get("request"),
                username=username,
                password=password,
            )

            if not user:
                msg = _("Unable to log in with provided credentials.")
                raise serializers.ValidationError(msg, code="authorization")
            if not user.is_verified:
                msg = _("User account is not verified.")
                raise serializers.ValidationError(msg, code="authorization")
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        if not self.user.is_verified:
            msg = _("User account is not verified.")
            raise serializers.ValidationError(msg, code="authorization")
        return {
            "refresh": validated_data["refresh"],
            "access": validated_data["access"],
            "user_id": self.user.id,
            "email": self.user.email,
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("new_password1"):
            raise serializers.ValidationError("Passwords do not match")
        try:
            validate_password(attrs.get("new_password"))
        except serializers.ValidationError as e:
            return serializers.ValidationError({"new_password": e.messages})
        return super().validate(attrs)


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "email",
            "image",
            "description",
            "first_name",
            "last_name",
            "created_date",
        )
        read_only_fields = ("id", "email", "created_date")


class ResendActivationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        try:
            user_obj = get_object_or_404(get_user_model(), email=email)
        except:
            raise serializers.ValidationError("User with this email does not exist.")
        if user_obj.is_verified:
            raise serializers.ValidationError("Account is already verified.")
        attrs["user"] = user_obj
        return super().validate(attrs)


class ResetPasswordSerializerConfirm(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("new_password1"):
            raise serializers.ValidationError("Passwords do not match")
        try:
            validate_password(attrs.get("new_password"))
        except serializers.ValidationError as e:
            return serializers.ValidationError({"new_password": e.messages})
        return super().validate(attrs)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        try:
            user_obj = get_object_or_404(get_user_model(), email=email)
        except:
            raise serializers.ValidationError("User with this email does not exist.")
        attrs["user"] = user_obj
        return super().validate(attrs)
