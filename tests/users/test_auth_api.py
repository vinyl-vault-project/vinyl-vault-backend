from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


User = get_user_model()


class RegistrationApiTests(APITestCase):
    def setUp(self):
        self.url = reverse("users:register")
        self.payload = {
            "username": "vinyl_fan",
            "email": "fan@example.com",
            "password": "StrongPassword123!",
        }

    def test_registration_creates_user_and_returns_tokens(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

        user = User.objects.get(email=self.payload["email"])
        self.assertEqual(user.username, self.payload["username"])
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotEqual(user.password, self.payload["password"])

        self.assertNotIn("password", response.data)
        self.assertNotIn("password", response.data["user"])
        self.assertEqual(response.data["user"]["id"], user.pk)
        self.assertEqual(response.data["user"]["email"], user.email)

        access = AccessToken(response.data["access"])
        refresh = RefreshToken(response.data["refresh"])
        self.assertEqual(access["user_id"], str(user.pk))
        self.assertEqual(refresh["user_id"], str(user.pk))

    def test_registration_token_immediately_authenticates_user(self):
        registration_response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )
        access = registration_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(reverse("users:current-user"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.payload["email"])
        self.assertEqual(response.data["username"], self.payload["username"])

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(**self.payload)
        duplicate_payload = {
            **self.payload,
            "username": "another_user",
        }

        response = self.client.post(self.url, duplicate_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rejects_duplicate_username(self):
        User.objects.create_user(**self.payload)
        duplicate_payload = {
            **self.payload,
            "email": "another@example.com",
        }

        response = self.client.post(self.url, duplicate_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rejects_weak_password(self):
        payload = {
            **self.payload,
            "password": "password",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.exists())

    def test_registration_requires_username_email_and_password(self):
        for field in ("username", "email", "password"):
            with self.subTest(field=field):
                payload = {**self.payload}
                payload.pop(field)

                response = self.client.post(self.url, payload, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)


class AuthenticationApiTests(APITestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.user = User.objects.create_user(
            email="listener@example.com",
            username="listener",
            password=self.password,
            first_name="Ella",
            last_name="Fitzgerald",
            phone="+380501234567",
            address="Kyiv, Ukraine",
        )
        self.login_url = reverse("users:login")
        self.refresh_url = reverse("users:token_refresh")
        self.logout_url = reverse("users:logout")
        self.me_url = reverse("users:current-user")

    def test_login_accepts_email_and_password(self):
        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        AccessToken(response.data["access"])
        RefreshToken(response.data["refresh"])

    def test_login_does_not_accept_username_instead_of_email(self):
        response = self.client.post(
            self.login_url,
            {
                "username": self.user.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_rejects_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            self.login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_returns_new_access_token(self):
        refresh = RefreshToken.for_user(self.user)

        response = self.client.post(
            self.refresh_url,
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        AccessToken(response.data["access"])

    def test_current_user_requires_authentication(self):
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_returns_authenticated_user(self):
        access = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": self.user.pk,
                "username": self.user.username,
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "phone": self.user.phone,
                "address": self.user.address,
            },
        )

    def test_logout_blacklists_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)

        logout_response = self.client.post(
            self.logout_url,
            {"refresh": str(refresh)},
            format="json",
        )
        refresh_response = self.client.post(
            self.refresh_url,
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
