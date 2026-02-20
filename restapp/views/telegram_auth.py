from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Filial
from restapp.serializers import TelegramRegisterSerializer, TelegramTokenSerializer
from sales.models import Client

User = get_user_model()

def _check_secret(request) -> bool:
    secret = request.headers.get("X-TG-SECRET")
    return bool(secret) and secret == "change-me-strong-secret"


class TelegramRegisterClientView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not _check_secret(request):
            return Response({"detail": "Unauthorized (Error secret key"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = TelegramRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        telegram_id = data["telegram_id"]
        phone = data["phone_number"].strip()
        full_name = data["full_name"].strip()
        region_id = data["region_id"]
        district_id = data["district_id"]

        # 1) Avval telegram_id bo‘yicha topamiz
        client = Client.objects.filter(telegram_id=telegram_id).first()
        # 2) Agar topilmasa, phone bo‘yicha ham tekshirib ko‘ramiz (xohlasangiz olib tashlaysiz)
        if not client:
            client = client.objects.filter(phone_number=phone).first()

        filial = Filial.objects.filter(region_id=region_id, district_id=district_id).first()
        if not filial:
            filial = None


        created = False
        if not client:
            created = True
            client = Client(
                telegram_id=telegram_id,
                phone_number=phone,
                full_name=full_name,
                region_id=region_id,     # sizda region maydoni "Company"
                district_id=district_id,
                filial=filial,
                is_active=False,
            )
            client.save()
        else:
            # update
            client.telegram_id = telegram_id
            client.phone_number = phone
            client.full_name = full_name
            client.region_id = region_id
            client.district_id = district_id
            client.filial=filial
            client.is_active = False
            client.save(update_fields=[
                "telegram_id", "phone_number", "full_name", "region", "district", "is_active"
            ])

        return Response({
            "ok": True,
            "created": created,
            "client_id": client.id,
        })


class TelegramRegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not _check_secret(request):
            return Response({"detail": "Unauthorized (Error secret key"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = TelegramRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        telegram_id = data["telegram_id"]
        phone = data["phone_number"].strip()
        full_name = data["full_name"].strip()
        region_id = data["region_id"]
        district_id = data["district_id"]

        # 1) Avval telegram_id bo‘yicha topamiz
        user = User.objects.filter(telegram_id=telegram_id).first()

        # 2) Agar topilmasa, phone bo‘yicha ham tekshirib ko‘ramiz (xohlasangiz olib tashlaysiz)
        if not user:
            user = User.objects.filter(phone_number=phone).first()

        created = False
        if not user:
            created = True
            # username unique bo‘lishi kerak. Eng oddiy:
            username = f"tg_{telegram_id}"
            # Agar username to‘qnashsa:
            if User.objects.filter(username=username).exists():
                username = f"tg_{telegram_id}_{User.objects.count()+1}"

            user = User(
                username=username,
                telegram_id=telegram_id,
                phone_number=phone,
                full_name=full_name,
                region_id=region_id,     # sizda region maydoni "Company"
                district_id=district_id,
                is_active=True,
            )
            user.set_unusable_password()  # telegram orqali kirsa ham bo‘ladi
            user.save()
        else:
            # update
            user.telegram_id = telegram_id
            user.phone_number = phone
            user.full_name = full_name
            user.region_id = region_id
            user.district_id = district_id
            user.is_active = True
            user.save(update_fields=[
                "telegram_id", "phone_number", "full_name", "region", "district", "is_active"
            ])

        return Response({
            "ok": True,
            "created": created,
            "user_id": user.id,
        })

class TelegramTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not _check_secret(request):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = TelegramTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        telegram_id = ser.validated_data["telegram_id"]

        user = User.objects.filter(telegram_id=telegram_id, is_active=True).first()
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user_id": user.id,
        })
