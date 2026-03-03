from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.filterset import SkladFilter
from accounts.models import Sklad
from accounts.serializers import SkladListSerializer, SkladSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


def _not_found(msg="Topilmadi."):
    return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)


def _forbidden(msg="Sizda dostup yo‘q."):
    return Response({"detail": msg}, status=status.HTTP_403_FORBIDDEN)


def _bad_request(msg="Noto‘g‘ri so‘rov."):
    return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)


class SkladFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in Sklad._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, "max_length", None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info, status=status.HTTP_200_OK)


class SkladViewList(ListCreateAPIView):
    """
    Public list (faqat GET).
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = SkladSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SkladFilter
    search_fields = ("name", "phone_number", "address", "filial__name")
    ordering = ["sorting", "-id"]
    http_method_names = ["get"]
    pagination_class = None

    def get_queryset(self):
        return (
            Sklad.objects
            .filter(is_delete=False)
            .select_related("filial", "region", "district")
            .order_by("sorting", "-id")
        )


class SkladView(ListCreateAPIView):
    serializer_class = SkladListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SkladFilter
    search_fields = ("name", "phone_number", "address", "filial__name")
    ordering = ["sorting", "-id"]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list("id", flat=True)

        return (
            Sklad.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related("filial", "region", "district")
            .order_by("sorting", "-id")
        )

    def post(self, request, *args, **kwargs):
        serializer = SkladSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        filial = serializer.validated_data.get("filial") or request.user.order_filial
        if filial is None:
            return Response(
                {"filial": "filial yuborilmadi va userda order_filial ham yo‘q."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.filials.filter(id=filial.id).exists():
            return Response(
                {"detail": "Sizda bu filial uchun sklad yaratish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        obj = serializer.save(created_by=request.user, filial=filial)
        return Response(SkladListSerializer(obj).data, status=status.HTTP_201_CREATED)


class SkladDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SkladSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Sklad.objects.all().select_related("filial", "region", "district")

    def _get_obj(self, request, pk: int):
        try:
            pk_int = int(pk)
        except Exception:
            return None, _bad_request("id noto‘g‘ri (int bo‘lishi kerak).")

        obj = (
            Sklad.objects
            .select_related("filial", "region", "district")
            .filter(id=pk_int)
            .first()
        )
        if not obj:
            return None, _not_found("Sklad topilmadi.")

        # dostup: user faqat o'z filialidagi sklad
        if obj.filial_id is None:
            return None, _bad_request("Sklad.filial null. Dostup tekshirib bo‘lmaydi.")

        if not request.user.filials.filter(id=obj.filial_id).exists():
            return None, _forbidden("Sizda bu skladga dostup yo‘q.")

        return obj, None

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err
        return Response(SkladListSerializer(obj).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err

        serializer = self.serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)

        # filialni o'zgartirmoqchi bo'lsa ham: yangi filial userga tegishli bo'lsin
        new_filial = serializer.validated_data.get("filial")
        if new_filial and (not request.user.filials.filter(id=new_filial.id).exists()):
            return _forbidden("Sizda bu filialga skladni o‘tkazish huquqi yo‘q.")

        saved = serializer.save(updated_by=request.user)
        return Response(SkladListSerializer(saved).data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err

        obj.is_delete = True
        obj.save(update_fields=["is_delete", "updated_time"])
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)


class ProductTypeSuggestSortingByModelView(APIView):
    """
    Siz yuborgan kod logikasini o'zgartirmadim, lekin:
    - Sklad modelida 'madel_id' bo'lmasa xato bermasdan 400 qaytaramiz.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, madel):
        # ⚠️ Sizning kodingizda: Sklad.objects.filter(madel_id=...)
        # Agar Sklad modelida bu field bo'lmasa — server 500 bo'lib ketadi.
        # Shuning uchun oldindan tekshiramiz (logika o'zgarmaydi).
        field_names = {f.name for f in Sklad._meta.fields}
        if "madel" not in field_names and "madel_id" not in field_names:
            return _bad_request("Sklad modelida 'madel' (madel_id) field yo‘q. Bu view noto‘g‘ri modelga ulangan.")

        used = (
            Sklad.objects
            .filter(
                is_delete=False,
                madel_id=madel,          # siz yozganidek qoldirdim
                sorting__isnull=False
            )
            .order_by("sorting")
            .values_list("sorting", flat=True)
        )

        suggested = 1
        for s in used:
            try:
                s_int = int(s)
            except (TypeError, ValueError):
                continue

            if s_int < suggested:
                continue
            if s_int == suggested:
                suggested += 1
            else:
                break

        return Response(
            {
                "madel": madel,
                "suggested_sorting": suggested,
                "message": "Tavsiya etilgan tartib raqam."
            },
            status=status.HTTP_200_OK
        )