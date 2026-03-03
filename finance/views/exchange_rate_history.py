from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from restapp.pagination import ResultsSetPagination
from finance.filterset import ExchangeRateHistoryFilter
from finance.models import ExchangeRateHistory, ExchangeRate
from finance.serializer.exchange_rate_history import (
    ExchangeRateHistorySerializer,
    ExchangeRateHistoryListSerializer,
)


def _bad(msg):
    return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)


def _forbidden(msg):
    return Response({"detail": msg}, status=status.HTTP_403_FORBIDDEN)


def _not_found(msg):
    return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)


def _user_filial_ids(user):
    return list(user.filials.values_list("id", flat=True))


class ExchangeRateHistoryFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in ExchangeRateHistory._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, "max_length", None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info, status=status.HTTP_200_OK)


class ExchangeRateHistoryView(ListCreateAPIView):
    serializer_class = ExchangeRateHistoryListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ExchangeRateHistoryFilter
    search_fields = ("filial__name",)
    ordering = ["-pk"]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        user_filial_ids = _user_filial_ids(self.request.user)
        return (
            ExchangeRateHistory.objects
            .select_related("exchange_rate", "filial")
            .filter(filial_id__in=user_filial_ids)
            .order_by("-pk")
        )

    def post(self, request, **kwargs):
        serializer = ExchangeRateHistorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ✅ xavfsizlik: filial userga tegishlimi?
        filial = serializer.validated_data.get("filial")
        filial_id = getattr(filial, "id", None)
        if filial_id is None:
            return _bad("filial majburiy.")

        if not request.user.filials.filter(id=filial_id).exists():
            return _forbidden("Sizda bu filial uchun ExchangeRateHistory yaratish huquqi yo‘q.")

        # ✅ exchange_rate ham shu filialniki bo‘lishi kerak (ko‘p joyda shu talab bo‘ladi)
        exr = serializer.validated_data.get("exchange_rate")
        exr_id = getattr(exr, "id", None)
        if exr_id:
            ok = ExchangeRate.objects.filter(id=exr_id, filial_id=filial_id).exists()
            if not ok:
                return _bad("exchange_rate ushbu filialga tegishli emas.")

        obj = serializer.save(created_by=request.user, updated_by=request.user)

        # list serializerda qaytaramiz (select_related bilan)
        out = ExchangeRateHistoryListSerializer(
            ExchangeRateHistory.objects.select_related("exchange_rate", "filial").get(pk=obj.pk)
        ).data
        return Response(out, status=status.HTTP_201_CREATED)


class ExchangeRateHistoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ExchangeRateHistorySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "put", "delete"]

    def get_queryset(self):
        user_filial_ids = _user_filial_ids(self.request.user)
        return (
            ExchangeRateHistory.objects
            .select_related("exchange_rate", "filial")
            .filter(filial_id__in=user_filial_ids)
        )

    def _get_obj(self, request, pk):
        try:
            pk_int = int(pk)
        except Exception:
            return None, _bad("id noto‘g‘ri (int bo‘lishi kerak).")

        obj = self.get_queryset().filter(id=pk_int).first()
        if not obj:
            return None, _not_found("ExchangeRateHistory topilmadi yoki sizda dostup yo‘q.")
        return obj, None

    def get(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err
        return Response(ExchangeRateHistoryListSerializer(obj).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err

        serializer = self.serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)

        # ✅ filialni o‘zgartirishsa ham userning filialida bo‘lsin
        filial = serializer.validated_data.get("filial") or obj.filial
        filial_id = getattr(filial, "id", None)
        if filial_id and not request.user.filials.filter(id=filial_id).exists():
            return _forbidden("Sizda bu filialga o‘tkazish huquqi yo‘q.")

        # ✅ exchange_rate ham shu filialniki bo‘lishi kerak
        exr = serializer.validated_data.get("exchange_rate") or obj.exchange_rate
        exr_id = getattr(exr, "id", None)
        if exr_id and filial_id:
            ok = ExchangeRate.objects.filter(id=exr_id, filial_id=filial_id).exists()
            if not ok:
                return _bad("exchange_rate ushbu filialga tegishli emas.")

        updated = serializer.save(updated_by=request.user)

        out = ExchangeRateHistoryListSerializer(
            ExchangeRateHistory.objects.select_related("exchange_rate", "filial").get(pk=updated.pk)
        ).data
        return Response(out, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err
        obj.delete()
        return Response({"detail": "Deleted"}, status=status.HTTP_204_NO_CONTENT)