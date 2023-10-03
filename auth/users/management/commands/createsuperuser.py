import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from users.models import User
from users.services import user_create

PASSWORD_FIELD = "password"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            f"--{User.USERNAME_FIELD}",
            help="Specifies login for the superuser.",
        )

    def handle(self, *args, **options):
        user_data = {}
        username_field = User._meta.get_field(User.USERNAME_FIELD)

        # validate values of command line options to fail early
        if options.get(User.USERNAME_FIELD) is not None:
            try:
                user_data[User.USERNAME_FIELD] = username_field.clean(
                    options[User.USERNAME_FIELD], None
                )
            except ValidationError:
                self.stderr.write(
                    self.style.ERROR(
                        f"--{User.USERNAME_FIELD}: {options[User.USERNAME_FIELD]!r}"
                    )
                )
                raise CommandError("Invalid value of command line argument.")

        while user_data.get(User.USERNAME_FIELD) is None:
            raw_value = input("Login: ")
            try:
                user_data[User.USERNAME_FIELD] = username_field.clean(raw_value, None)
            except ValidationError as exc:
                self.stderr.write(f"Error: {'; '.join(exc.messages)}")

        while user_data.get(PASSWORD_FIELD) is None:
            password = getpass.getpass()
            password2 = getpass.getpass("Password (again): ")
            if password != password2:
                self.stderr.write("Error: Your passwords didn't match.")
                # Don't validate passwords that don't match.
                continue
            if password.strip() == "":
                self.stderr.write("Error: Blank passwords aren't allowed.")
                # Don't validate blank passwords.
                continue
            try:
                validate_password(password, User(**user_data))
            except ValidationError as exc:
                self.stderr.write("\n".join(exc.messages))
                continue

            user_data[PASSWORD_FIELD] = password

        user_data["role"] = User.Role.ADMIN
        user_data["is_superuser"] = True

        user_create(**user_data)
        self.stdout.write("Superuser created successfully.")
