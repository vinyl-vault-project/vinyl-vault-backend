from django.contrib.auth import get_user_model
from django.test import TestCase


User = get_user_model()


class UserManagerTests(TestCase):
    def test_create_user_hashes_password_and_sets_default_flags(self):
        password = "StrongPassword123!"

        user = User.objects.create_user(
            email="listener@EXAMPLE.COM",
            username="listener",
            password=password,
        )

        self.assertEqual(user.email, "listener@example.com")
        self.assertEqual(user.username, "listener")
        self.assertTrue(user.check_password(password))
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_saves_profile_fields(self):
        user = User.objects.create_user(
            email="profile@example.com",
            username="profile_user",
            password="StrongPassword123!",
            first_name="Miles",
            last_name="Davis",
            phone="+380501234567",
            address="Kyiv, Ukraine",
        )

        self.assertEqual(user.first_name, "Miles")
        self.assertEqual(user.last_name, "Davis")
        self.assertEqual(user.phone, "+380501234567")
        self.assertEqual(user.address, "Kyiv, Ukraine")
        self.assertEqual(str(user), "profile@example.com")

    def test_create_user_requires_email(self):
        with self.assertRaisesMessage(ValueError, "The given email must be set"):
            User.objects.create_user(
                email="",
                username="listener",
                password="StrongPassword123!",
            )

    def test_create_user_requires_username(self):
        with self.assertRaisesMessage(ValueError, "Username must be set"):
            User.objects.create_user(
                email="listener@example.com",
                username="",
                password="StrongPassword123!",
            )

    def test_create_superuser_sets_required_flags(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="StrongPassword123!",
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_superuser_rejects_invalid_flags(self):
        invalid_flags = (
            {"is_staff": False},
            {"is_superuser": False},
        )

        for flags in invalid_flags:
            with self.subTest(flags=flags):
                with self.assertRaises(ValueError):
                    User.objects.create_superuser(
                        email=f"admin-{len(flags)}@example.com",
                        username=f"admin-{len(flags)}",
                        password="StrongPassword123!",
                        **flags,
                    )
