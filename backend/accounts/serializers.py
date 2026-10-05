from django.db import transaction
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from scholars.models import ScholarProfile

from .models import User


class ScholarProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScholarProfile
        fields = [
            "id",
            "scholar_id",
            "institution",
            "country",
            "program",
            "study_level",
            "graduation_year",
            "verification_status",
            "rejection_reason",
            "verified_at",
        ]

        read_only_fields = [
            "id",
            "verification_status",
            "rejection_reason",
            "verified_at",
        ]


class UserSerializer(serializers.ModelSerializer):
    scholar_profile = ScholarProfileSerializer(
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "scholar_profile",
        ]

        read_only_fields = [
            "id",
            "email",
            "role",
            "scholar_profile",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    password_confirmation = serializers.CharField(
        write_only=True,
    )

    profile = ScholarProfileSerializer(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirmation",
            "first_name",
            "last_name",
            "phone",
            "profile",
        ]

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return email

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirmation = attrs.pop(
            "password_confirmation",
            None,
        )

        if password != password_confirmation:
            raise serializers.ValidationError(
                {
                    "password_confirmation": (
                        "Passwords do not match."
                    )
                }
            )

        validate_password(password)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile_data = validated_data.pop("profile")

        user = User.objects.create_user(
            role=User.Role.SCHOLAR,
            **validated_data,
        )

        ScholarProfile.objects.create(
            user=user,
            **profile_data,
        )

        return user