from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PasswordComplexityValidator:
    """Require a mix of character types in user passwords."""

    message = _(
        "This password must contain at least one uppercase letter, "
        "one lowercase letter, one digit, and one special character."
    )

    def validate(self, password, user=None):
        has_uppercase = any(character.isupper() for character in password)
        has_lowercase = any(character.islower() for character in password)
        has_digit = any(character.isdigit() for character in password)
        has_special = any(
            not character.isalnum() and not character.isspace()
            for character in password
        )

        if not all((has_uppercase, has_lowercase, has_digit, has_special)):
            raise ValidationError(
                self.message,
                code="password_not_complex",
            )

    def get_help_text(self):
        return self.message
