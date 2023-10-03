from oauth2_provider import oauth2_validators

from .models import User


class OAuth2Validator(oauth2_validators.OAuth2Validator):
    def get_additional_claims(self, request):
        user: User = request.user
        return {
            "sub": str(user.public_id),
            "role": user.role,
            "email": user.email,
        }
