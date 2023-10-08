from oauth2_provider import oauth2_validators
from oauth2_provider import admin as oauth2_admin

from .models import User


class OAuth2Validator(oauth2_validators.OAuth2Validator):
    oidc_claim_scope = {
        **oauth2_validators.OAuth2Validator.oidc_claim_scope,
        "role": "profile",
    }

    def get_additional_claims(self, request):
        user: User = request.user
        return {
            "sub": str(user.public_id),
            "role": user.role,
            "email": user.email,
        }


class ApplicationAdmin(oauth2_admin.ApplicationAdmin):
    view_on_site = False
