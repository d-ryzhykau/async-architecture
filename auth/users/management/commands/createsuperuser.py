import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import capfirst

from users.models import User
from users.services import user_create_superuser

PASSWORD_FIELD = "password"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            f"--{User.USERNAME_FIELD}",
            help="Specifies login for the superuser.",
        )
        for field_name in User.REQUIRED_FIELDS:
            parser.add_argument(
                f"--{field_name}",
                help=f"Specifies {field_name} for the superuser.",
            )

    def _get_input_message(self, field):
        message = capfirst(field.verbose_name)
        if field.default:
            message += f" (leave blank to use '{field.default}')"
        message += ": "
        return message

    def _get_input_data(self, field, message):
        raw_value = input(message)
        if raw_value == "" and field.default:
            return field.default

        try:
            return field.clean(raw_value, None)
        except ValidationError as exc:
            self.stderr.write(f"Error: {'; '.join(exc.messages)}")
            return None

    def handle(self, *args, **options):
        # validate values of command line options to fail early
        required_fields = [User.USERNAME_FIELD] + User.REQUIRED_FIELDS
        user_data = {}

        invalid_options_fields = []
        for field_name in required_fields:
            if options.get(field_name) is None:
                continue

            field = User._meta.get_field(field_name)
            try:
                user_data[field_name] = field.clean(options[field_name], None)
            except ValidationError:
                invalid_options_fields.append(field_name)

        if invalid_options_fields:
            self.stderr.write("Invalid values of command line arguments:")
            for field_name in invalid_options_fields:
                self.stderr.write(
                    self.style.ERROR(f"--{field_name}: {options[field_name]!r}")
                )
            raise CommandError("Invalid values of command line arguments.")

        for field_name in required_fields:
            field = User._meta.get_field(field_name)
            message = self._get_input_message(field)
            while user_data.get(field_name) is None:
                user_data[field_name] = self._get_input_data(field, message)

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
            else:
                user_data[PASSWORD_FIELD] = password

        user_create_superuser(**user_data)
        self.stdout.write("Superuser created successfully.")
