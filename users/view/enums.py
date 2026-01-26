from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from restapp.utils.enumserialize import enum_serialize


class UserGenderList(APIView):
    def get(self, request):
        return Response(enum_serialize(User.GENDERS.choices))

