from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.filterset import ExchangeRateFilter
from finance.models import ExchangeRate, ExchangeRateHistory
from finance.serializer.exchange_rate import ExchangeRateSerializer, ExchangeRateListSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


def _bad(msg):
    return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)


def _forbidden(msg):
    return Response({"detail": msg}, status=status.HTTP_403_FORBIDDEN)


def _not_found(msg):
    return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)


def _user_filial_ids(user):
    return list(user.filials.values_list("id", flat=True))


class ExchangeRateFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in ExchangeRate._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, "max_length", None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info, status=status.HTTP_200_OK)


class ExchangeRateViewList(ListCreateAPIView):
    """
    Public list (faqat GET)
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = ExchangeRateSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ExchangeRateFilter
    search_fields = ("filial__name", 'dollar')
    ordering = ["pk"]
    http_method_names = ["get"]
    pagination_class = None

    def get_queryset(self):
        return ExchangeRate.objects.all()


class ExchangeRateView(ListCreateAPIView):
    serializer_class = ExchangeRateListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ExchangeRateFilter
    search_fields = ("filial__name", 'dollar')
    ordering = ["pk"]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        user_filial_ids = _user_filial_ids(self.request.user)
        return (
            ExchangeRate.objects
            .filter(filial_id__in=user_filial_ids)
            .select_related("filial")
            .order_by("pk")
        )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = ExchangeRateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        filial = serializer.validated_data.get("filial") or getattr(request.user, "order_filial", None)
        if filial is None:
            return _bad("filial yuborilmadi va userda order_filial ham yo‘q.")

        if not request.user.filials.filter(id=filial.id).exists():
            return _forbidden("Sizda bu filial uchun kurs qo‘shish huquqi yo‘q.")

        rate: ExchangeRate = serializer.save(
            created_by=request.user,
            updated_by=request.user,
            filial=filial
        )

        ExchangeRateHistory.objects.create(
            exchange_rate=rate,
            filial=filial,
            old_dollar=0,
            new_dollar=rate.dollar,
            created_by=request.user,
            updated_by=request.user,
        )

        return Response(ExchangeRateListSerializer(rate).data, status=status.HTTP_201_CREATED)


class ExchangeRateDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ExchangeRateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ✅ ENDI DETAIL HAM FILIAL BO‘YICHA
        user_filial_ids = _user_filial_ids(self.request.user)
        return ExchangeRate.objects.filter(filial_id__in=user_filial_ids).select_related("filial")

    def _get_obj(self, request, pk, *, lock=False):
        try:
            pk_int = int(pk)
        except Exception:
            return None, _bad("id noto‘g‘ri (int bo‘lishi kerak).")

        qs = self.get_queryset()
        if lock:
            qs = qs.select_for_update(of=("self",))

        obj = qs.filter(id=pk_int).first()
        if not obj:
            return None, _not_found("ExchangeRate topilmadi yoki sizda dostup yo‘q.")
        return obj, None

    def get(self, request, pk):
        obj, err = self._get_obj(request, pk, lock=False)
        if err:
            return err
        return Response(ExchangeRateListSerializer(obj).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, pk):
        obj, err = self._get_obj(request, pk, lock=True)
        if err:
            return err

        old_dollar = obj.dollar

        serializer = self.serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_rate: ExchangeRate = serializer.save(updated_by=request.user, is_active=True)

        if old_dollar != updated_rate.dollar:
            ExchangeRateHistory.objects.create(
                exchange_rate=updated_rate,
                filial=updated_rate.filial,
                old_dollar=old_dollar,
                new_dollar=updated_rate.dollar,
                created_by=request.user,
                updated_by=request.user,
            )

        # response: sizdagi kabi serializer.data (logika o‘zgarmadi)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @transaction.atomic
    def delete(self, request, pk):
        obj, err = self._get_obj(request, pk, lock=True)
        if err:
            return err

        obj.delete()
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)