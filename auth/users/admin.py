from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from users.models import User
from users.services import user_create, user_delete, user_update


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_("Password"),
        required=True,
        strip=False,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        required=True,
        strip=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ["email", "role", "is_deleted"]

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data["email"])
        if email and User.objects.filter(email=email, is_deleted=False).exists():
            raise ValidationError(_("This email is already used."))
        return email

    def clean_password2(self):
        password2 = self.cleaned_data["password2"]
        validate_password(password2)
        return password2

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", _("Passwords don't match."))
        return cleaned_data


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        help_text="Password hash. Use <a>this form to change password."
    )

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = self.fields["password"]
        password.help_text = format_html(
            _(
                "Raw passwords are not stored, so there is no way to see this "
                "user`s password, but you can change the password using "
                '<a href="{}">this form</a>.'
            ),
            reverse("admin:auth_user_password_change", kwargs={"id": self.instance.pk})
        )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # add User form
    add_form = UserCreationForm
    add_fieldsets = (
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["email", "role", "password1", "password2"],
            },
        ),
    )

    # change User form
    form = UserChangeForm
    fieldsets = (
        (None, {"fields": ["email", "password", "public_id"]}),
        (
            _("Permissions"),
            {"fields": ["role", "is_deleted", "groups", "user_permissions"]},
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    list_display = ["email", "role", "is_deleted"]
    list_filter = ["role", "is_deleted"]
    search_fields = ["email"]
    ordering = ["pk"]
    actions = None

    readonly_fields = ["public_id", "is_deleted"]

    def get_readonly_fields(self, request, obj):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj is not None:
            readonly_fields = list(readonly_fields) + ["role"]
        return readonly_fields

    def save_form(self, request, form, change):
        super().save_form(request, form, change)

        if change and form.has_changed():
            form: UserChangeForm
            return user_update(
                user=form.instance,
                email=form.cleaned_data["email"],
            )
        else:
            form: UserCreationForm
            return user_create(
                email=form.cleaned_data["email"],
                role=form.cleaned_data["role"],
                password=form.cleaned_data["password2"],
            )

    def save_model(self, *args, **kwargs):
        # as model is saved in self.save_form this step can be skipped
        pass

    def delete_model(self, request, obj):
        user_delete(obj)
