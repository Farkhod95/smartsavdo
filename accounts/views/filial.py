from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.filterset import FilialFilter
from accounts.models import Filial
from accounts.serializers import FilialListSerializer, FilialSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


def _not_found(msg="Topilmadi."):
    return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)


def _forbidden(msg="Sizda dostup yo‘q."):
    return Response({"detail": msg}, status=status.HTTP_403_FORBIDDEN)


class FilialFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in Filial._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, "max_length", None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info, status=status.HTTP_200_OK)


class FilialViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = FilialSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = FilialFilter
    search_fields = ("name", "phone_number", "address")
    ordering = ["pk"]
    http_method_names = ["get"]
    pagination_class = None

    def get_queryset(self):
        return Filial.objects.filter(is_delete=False)


class FilialSelfView(ListCreateAPIView):
    """
    Userga tegishli filiallar ro'yxati.
    """
    serializer_class = FilialListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = FilialFilter
    search_fields = ("name", "phone_number", "address")
    ordering = ["pk"]
    http_method_names = ["get"]

    def get_queryset(self):
        user = self.request.user

        # Eng optimal: M2M join (filials) orqali
        return (
            Filial.objects
            .filter(is_delete=False, id__in=user.filials.values_list("id", flat=True))
            .distinct()
            .order_by("pk")
        )


class FilialView(ListCreateAPIView):
    """
    Private list + create. (Agar siz public list alohida ishlatyapsiz - bu private bo'lib qoladi)
    """
    serializer_class = FilialListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = FilialFilter
    search_fields = ("name", "phone_number", "address")
    ordering = ["pk"]

    def get_queryset(self):
        # Agar siz xohlaysiz: superadmin hammasini ko'rsin — bu yerda alohida shart qo'yasiz.
        # Hozir: user faqat o'z filiallarniki.
        user = self.request.user
        return Filial.objects.filter(
            is_delete=False,
            id__in=user.filials.values_list("id", flat=True)
        ).order_by("pk")

    def post(self, request, *args, **kwargs):
        # Filial yaratish: bu yerda sizning biznes qoidangizga bog'liq.
        # Hozir logika buzilmasin deb: oldingidek create qildim.
        serializer = FilialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(created_by=request.user)

        # xohlasangiz: yangi yaratilgan filialni user.filials ga qo'shib qo'yish mumkin:
        # request.user.filials.add(obj)

        return Response(FilialSerializer(obj).data, status=status.HTTP_201_CREATED)


class FilialDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = FilialSerializer
    permission_classes = [IsAuthenticated]

    def _get_obj(self, request, pk: int):
        """
        Http404 chiqarmaymiz, tushunarli Response qaytaramiz.
        Dostup: user.filials ichida bo'lishi shart.
        """
        try:
            pk_int = int(pk)
        except Exception:
            return None, Response({"detail": "id noto'g'ri."}, status=status.HTTP_400_BAD_REQUEST)

        user_filial_ids = request.user.filials.values_list("id", flat=True)

        obj = Filial.objects.filter(id=pk_int, is_delete=False).first()
        if not obj:
            return None, _not_found("Filial topilmadi yoki o‘chirilgan.")

        if obj.id not in set(user_filial_ids):
            return None, _forbidden("Sizda bu filialga dostup yo‘q.")

        return obj, None

    def get(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err
        return Response(FilialListSerializer(obj).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err

        serializer = self.serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        saved = serializer.save(updated_by=request.user)

        return Response(self.serializer_class(saved).data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err

        obj.is_delete = True
        obj.save(update_fields=["is_delete", "updated_time"])
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)