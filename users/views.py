from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import (
    TokenBlacklistSerializer,
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from users.serializers import (
    AccessTokenResponseSerializer,
    AuthResponseSerializer,
    RegisterSerializer,
    TokenPairResponseSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register a user",
        description=(
            "Create a user account and immediately return JWT access and refresh "
            "tokens."
        ),
        request=RegisterSerializer,
        responses={
            status.HTTP_201_CREATED: AuthResponseSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="The registration data is invalid."
            ),
        },
        tags=["Authentication"],
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get the current user",
        description=(
            "Return the profile of the user identified by the JWT access token."
        ),
        responses={
            status.HTTP_200_OK: UserSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="A valid JWT access token is required."
            ),
        },
        tags=["Authentication"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class LoginView(TokenObtainPairView):
    @extend_schema(
        summary="Log in",
        description="Authenticate with email and password and return a JWT token pair.",
        request=TokenObtainPairSerializer,
        responses={
            status.HTTP_200_OK: TokenPairResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="The email or password is incorrect."
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshTokenView(TokenRefreshView):
    @extend_schema(
        summary="Refresh an access token",
        description="Exchange a valid refresh token for a new JWT access token.",
        request=TokenRefreshSerializer,
        responses={
            status.HTTP_200_OK: AccessTokenResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="The refresh token is invalid or expired."
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(TokenBlacklistView):
    @extend_schema(
        summary="Log out",
        description="Blacklist a refresh token so it can no longer be used.",
        request=TokenBlacklistSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="The refresh token was successfully blacklisted."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="The refresh token is invalid or already blacklisted."
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
