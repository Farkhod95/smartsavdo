from decimal import Decimal

from collections import OrderedDict
from django.db import transaction
from django.db.models import F, QuerySet
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, status
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
    GenericAPIView,
    ListAPIView,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.filterset import DebtRepaymentFilter
from finance.models import DebtRepayment
from finance.serializer.debt_repayment import (
    DebtRepaymentSerializer,
    DebtRepaymentListSerializer,
    DebtRepaymentAccountingSerializer,
)
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.models import Client


# -----------------------------
# Helpers: Http404 yo'q, JSON error
# -----------------------------
def _not_found(msg="Topilmadi."):
    return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)


def _forbidden(msg="Sizda dostup yo‘q."):
    return Response({"detail": msg}, status=status.HTTP_403_FORBIDDEN)


def _bad_request(msg="Noto‘g‘ri so‘rov."):
    return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)


def _parse_int(v, name="id"):
    try:
        return int(v), None
    except Exception:
        return None, _bad_request(f"{name} noto‘g‘ri (int bo‘lishi kerak).")


def _user_filial_ids(user):
    return list(user.filials.values_list("id", flat=True))


def _check_filial_access(user, filial_id):
    if filial_id is None:
        return _bad_request("Obyekt filial_id null. Dostup tekshirib bo‘lmaydi.")
    if not user.filials.filter(id=filial_id).exists():
        return _forbidden("Sizda bu filialga tegishli ma’lumotga dostup yo‘q.")
    return None


# -----------------------------
# Field info
# -----------------------------
class DebtRepaymentFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in DebtRepayment._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, "max_length", None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info, status=status.HTTP_200_OK)


# -----------------------------
# Public list (sizdagi kabi qoldi)
# -----------------------------
class DebtRepaymentViewList(ListCreateAPIView):
    """
    Public list (faqat GET).
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = DebtRepaymentSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    ssearch_fields = ("client__full_name", "employee__full_name", "note", 'total_debt_client', 'summa_total_dollar')
    ordering = ["-pk"]
    http_method_names = ["get"]
    pagination_class = None

    def get_queryset(self):
        return DebtRepayment.objects.filter(is_delete=False)


# -----------------------------
# Grouped by date (logika o‘sha)
# -----------------------------
class DebtRepaymentGroupedByDateView(ListAPIView):
    serializer_class = DebtRepaymentListSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ("client__full_name", "employee__full_name", "note", 'total_debt_client', 'summa_total_dollar')
    ordering = ["-date", "-pk"]

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        user_filial_ids = _user_filial_ids(user)

        return (
            DebtRepayment.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related("filial", "client", "employee", "created_by")
            .order_by("-date", "-pk")
        )

    def _d(self, v) -> Decimal:
        if v in (None, "", "null"):
            return Decimal("0")
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0")

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        ser = self.get_serializer(qs, many=True)

        grouped = OrderedDict()

        for row in ser.data:
            d = row.get("date") or "no-date"

            if d not in grouped:
                grouped[d] = {
                    "date": d,
                    "count": 0,
                    "totals": {
                        "summa_total_dollar": "0.00",
                        "summa_dollar": "0.00",
                        "summa_naqt": "0.00",
                        "summa_kilik": "0.00",
                        "summa_terminal": "0.00",
                        "summa_transfer": "0.00",
                        "discount_amount": "0.00",
                        "zdacha_dollar": "0.00",
                        "zdacha_som": "0.00",
                    },
                    "items": []
                }

            g = grouped[d]
            g["items"].append(row)
            g["count"] += 1

            g_tot = g["totals"]
            g_tot["summa_total_dollar"] = str(self._d(g_tot["summa_total_dollar"]) + self._d(row.get("summa_total_dollar")))
            g_tot["summa_dollar"] = str(self._d(g_tot["summa_dollar"]) + self._d(row.get("summa_dollar")))
            g_tot["summa_naqt"] = str(self._d(g_tot["summa_naqt"]) + self._d(row.get("summa_naqt")))
            g_tot["summa_kilik"] = str(self._d(g_tot["summa_kilik"]) + self._d(row.get("summa_kilik")))
            g_tot["summa_terminal"] = str(self._d(g_tot["summa_terminal"]) + self._d(row.get("summa_terminal")))
            g_tot["summa_transfer"] = str(self._d(g_tot["summa_transfer"]) + self._d(row.get("summa_transfer")))
            g_tot["discount_amount"] = str(self._d(g_tot["discount_amount"]) + self._d(row.get("discount_amount")))
            g_tot["zdacha_dollar"] = str(self._d(g_tot["zdacha_dollar"]) + self._d(row.get("zdacha_dollar")))
            g_tot["zdacha_som"] = str(self._d(g_tot["zdacha_som"]) + self._d(row.get("zdacha_som")))

        for g in grouped.values():
            for k, v in g["totals"].items():
                g["totals"][k] = f"{self._d(v):.2f}"

        return Response(list(grouped.values()), status=status.HTTP_200_OK)


# -----------------------------
# Auth list + create (filial access sizdagi kabi)
# -----------------------------
class DebtRepaymentView(ListCreateAPIView):
    serializer_class = DebtRepaymentListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ("client__full_name", "employee__full_name", "note", 'total_debt_client', 'summa_total_dollar')
    ordering = ["-pk"]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = _user_filial_ids(user)

        return (
            DebtRepayment.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related("filial", "client", "employee", "created_by")
            .order_by("-pk")
        )

    def post(self, request, *args, **kwargs):
        serializer = DebtRepaymentAccountingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        filial = serializer.validated_data.get("filial") or request.user.order_filial
        if filial is None:
            return _bad_request("filial yuborilmadi va userda order_filial ham yo‘q.")

        if not request.user.filials.filter(id=filial.id).exists():
            return _forbidden("Sizda bu filial uchun qarz to‘lovi qilish huquqi yo‘q.")

        obj = serializer.save(created_by=request.user, filial=filial)
        return Response(DebtRepaymentListSerializer(obj).data, status=status.HTTP_201_CREATED)


# -----------------------------
# Detail (GET/PUT/DELETE) — endi filial dostup bor, Http404 yo‘q
# -----------------------------
class DebtRepaymentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DebtRepaymentAccountingSerializer
    permission_classes = [IsAuthenticated]

    def _get_obj(self, request, pk, *, require_not_deleted: bool | None = None, lock: bool = False):
        pk_int, err = _parse_int(pk, "id")
        if err:
            return None, err

        qs = DebtRepayment.objects.select_related("client", "filial")
        if lock:
            qs = qs.select_for_update(of=("self",))

        obj = qs.filter(id=pk_int).first()
        if not obj:
            return None, _not_found("DebtRepayment topilmadi.")

        # filial access
        err2 = _check_filial_access(request.user, obj.filial_id)
        if err2:
            return None, err2

        if require_not_deleted is True and obj.is_delete:
            return None, _not_found("DebtRepayment karzinkada (is_delete=True).")
        if require_not_deleted is False and (not obj.is_delete):
            return None, _not_found("DebtRepayment karzinkada emas (is_delete=False).")

        return obj, None

    def get(self, request, pk):
        obj, err = self._get_obj(request, pk, require_not_deleted=None, lock=False)
        if err:
            return err
        return Response(DebtRepaymentListSerializer(obj).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj, err = self._get_obj(request, pk, require_not_deleted=True, lock=False)
        if err:
            return err

        serializer = DebtRepaymentAccountingSerializer(
            obj,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        saved = serializer.save(updated_by=request.user)
        return Response(DebtRepaymentListSerializer(saved).data, status=status.HTTP_202_ACCEPTED)

    @transaction.atomic
    def delete(self, request, pk):
        """
        Soft delete:
        - Agar debt_status True bo'lsa rollback (client debtga pulni qaytarib qo'yadi)
        - keyin is_delete=True
        """
        dr, err = self._get_obj(request, pk, require_not_deleted=True, lock=True)
        if err:
            return err

        if dr.debt_status and dr.client_id:
            client = Client.objects.select_for_update().get(pk=dr.client_id)
            old_paid = dr.summa_total_dollar or Decimal("0")

            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") + old_paid)

        dr.is_delete = True
        dr.save(update_fields=["is_delete", "updated_time"])

        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)


# -----------------------------
# Karzinka list
# -----------------------------
class DebtRepaymentKarzinkaView(ListCreateAPIView):
    serializer_class = DebtRepaymentListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ("client__full_name", "employee__full_name", "note", 'total_debt_client', 'summa_total_dollar')
    ordering = ["-pk"]
    http_method_names = ["get"]

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = _user_filial_ids(user)

        return (
            DebtRepayment.objects
            .filter(is_delete=True, filial_id__in=user_filial_ids)
            .select_related("filial", "client", "employee", "created_by")
            .order_by("-pk")
        )


# -----------------------------
# Restore karzinka (filial dostup bor)
# -----------------------------
class DebtRepaymentRestoreKarzinkaView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DebtRepaymentSerializer
    http_method_names = ["put"]

    @transaction.atomic
    def put(self, request, pk: int):
        pk_int, err = _parse_int(pk, "id")
        if err:
            return err

        user_filial_ids = _user_filial_ids(request.user)

        dr = (
            DebtRepayment.objects
            .select_for_update()
            .select_related("client", "filial")
            .filter(pk=pk_int, is_delete=True, filial_id__in=user_filial_ids)
            .first()
        )
        if not dr:
            return _not_found("DebtRepayment topilmadi yoki sizda dostup yo‘q (yoki karzinkada emas).")

        dr.is_delete = False
        dr.save(update_fields=["is_delete", "updated_time"])

        return Response(DebtRepaymentListSerializer(dr).data, status=status.HTTP_200_OK)


# -----------------------------
# Karzinka detail: GET + HARD DELETE (filial dostup bor)
# -----------------------------
class DebtRepaymentDetailKarzinkaView(RetrieveUpdateDestroyAPIView):
    serializer_class = DebtRepaymentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["delete", "get"]

    def _get_obj(self, request, pk, *, lock: bool = False):
        pk_int, err = _parse_int(pk, "id")
        if err:
            return None, err

        qs = DebtRepayment.objects.select_related("client", "filial")
        if lock:
            qs = qs.select_for_update(of=("self",))

        dr = qs.filter(id=pk_int).first()
        if not dr:
            return None, _not_found("DebtRepayment topilmadi.")

        err2 = _check_filial_access(request.user, dr.filial_id)
        if err2:
            return None, err2

        return dr, None

    def get(self, request, pk):
        dr, err = self._get_obj(request, pk, lock=False)
        if err:
            return err
        return Response(DebtRepaymentListSerializer(dr).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, pk):
        dr, err = self._get_obj(request, pk, lock=True)
        if err:
            return err

        if dr.debt_status and dr.client_id:
            client = Client.objects.select_for_update().get(pk=dr.client_id)
            old_paid = dr.summa_total_dollar or Decimal("0")
            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") + old_paid)

        dr.delete()
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)