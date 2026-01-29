from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.request import Request


class CookieJWTAuthentication(JWTAuthentication):
    """
    access token cookie’da bo‘lsa, Authorization header shart emas.
    Cookie nomi: access_token
    """
    cookie_name = "access_token"

    def authenticate(self, request: Request):
        raw_token = request.COOKIES.get(self.cookie_name)
        if not raw_token:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        return (user, validated_token)
