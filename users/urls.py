from django.urls import path

from users.views import (
    CurrentUserView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
]

app_name = "users"
