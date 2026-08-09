from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from users.validators import PasswordComplexityValidator


class PasswordComplexityValidatorTests(SimpleTestCase):
    def setUp(self):
        self.validator = PasswordComplexityValidator()

    def test_accepts_complex_password(self):
        self.validator.validate("StrongPassword123!")

    def test_rejects_password_without_required_character_types(self):
        invalid_passwords = (
            "strongpassword123!",
            "STRONGPASSWORD123!",
            "StrongPassword!",
            "StrongPassword123",
            "StrongPassword123 ",
        )

        for password in invalid_passwords:
            with self.subTest(password=password):
                with self.assertRaisesMessage(
                    ValidationError,
                    "This password must contain at least one uppercase letter",
                ):
                    self.validator.validate(password)
