from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)

from .serializers import UserSerializer


class MasterSaveTokenObtainPairSerializer(
    TokenObtainPairSerializer
):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["email"] = user.email
        token["role"] = user.role
        token["first_name"] = user.first_name

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = UserSerializer(
            self.user
        ).data

        return data