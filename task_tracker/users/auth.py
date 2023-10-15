from django.shortcuts import render
from mozilla_django_oidc import auth as oidc_auth
from mozilla_django_oidc import views as oidc_views


class OIDCAuthenticationBackend(oidc_auth.OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        return self.UserModel.objects.filter(public_id=claims["sub"])

    def create_user(self, claims):
        return self.UserModel.objects.create(
            public_id=claims["sub"],
            email=claims["email"],
            role=claims["role"],
        )


class OIDCAuthenticationRequestView(oidc_views.OIDCAuthenticationRequestView):
    """Initiate authentication only for POST requests."""

    http_method_names = ["get", "post"]

    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        # reuse logic of default view's get
        return super().get(request)
