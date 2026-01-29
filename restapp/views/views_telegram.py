import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from restapp.serializers import TelegramRegisterSerializer, TelegramTokenSerializer
from restapp.views.tg_webapp import verify_webapp_init_data

User = get_user_model()


def _check_secret(request) -> bool:
    secret = request.headers.get("X-TG-SECRET")
    return bool(secret) and secret == settings.TG_SECRET


class TelegramRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not _check_secret(request):
            return Response({"detail": "Unauthorized (Error secret key)"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = TelegramRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        telegram_id = data["telegram_id"]
        phone = data["phone_number"].strip()
        full_name = data["full_name"].strip()
        region_id = data["region_id"]
        district_id = data["district_id"]

        user = User.objects.filter(telegram_id=telegram_id).first()
        if not user:
            user = User.objects.filter(phone_number=phone).first()

        created = False
        if not user:
            created = True
            username = f"tg_{telegram_id}"
            if User.objects.filter(username=username).exists():
                username = f"tg_{telegram_id}_{User.objects.count()+1}"

            user = User(
                username=username,
                telegram_id=telegram_id,
                phone_number=phone,
                full_name=full_name,
                region_id=region_id,
                district_id=district_id,
                is_active=True,
            )
            user.set_unusable_password()
            user.save()
        else:
            user.telegram_id = telegram_id
            user.phone_number = phone
            user.full_name = full_name
            user.region_id = region_id
            user.district_id = district_id
            user.is_active = True
            user.save(update_fields=[
                "telegram_id", "phone_number", "full_name", "region_id", "district_id", "is_active"
            ])

        return Response({"ok": True, "created": created, "user_id": user.id})


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


class TelegramWebAppLoginView(APIView):
    """
    ✅ Bot WebApp tugmasi ochganda ishlaydi:
      GET /api/v1/tg/login/?tgWebAppData=...

    Vazifa:
      - tgWebAppData verify
      - telegram_id ni olish
      - User topish
      - JWT access yaratish
      - cookie set
      - savdo saytga redirect
    """
    permission_classes = [AllowAny]

    def get(self, request):
        init_data = request.GET.get("tgWebAppData") or request.GET.get("initData") or ""
        if not init_data:
            return Response({"detail": "tgWebAppData topilmadi"}, status=status.HTTP_400_BAD_REQUEST)

        ok, data = verify_webapp_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
        if not ok:
            return Response({"detail": "Telegram initData hash noto‘g‘ri"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user_json = json.loads(data.get("user") or "{}")
            telegram_id = int(user_json.get("id"))
        except Exception:
            return Response({"detail": "Telegram user.id o‘qib bo‘lmadi"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(telegram_id=telegram_id, is_active=True).first()
        if not user:
            # xohlasangiz savdo saytda /register ga yuboring
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        redirect_to = getattr(settings, "SAVDO_REDIRECT_URL", "https://savdo.elegantchinni.uz/")
        resp = HttpResponseRedirect(redirect_to)

        resp.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,      # ✅ front JS o‘qiy olmaydi (xavfsiz)
            secure=True,        # ✅ https shart
            samesite="None",    # ✅ Telegram WebView’da ham ishlashi uchun
            domain=".elegantchinni.uz",
            path="/",
            max_age=86400,
        )
        return resp
