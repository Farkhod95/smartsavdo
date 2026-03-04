# finance/views/expense.py
from collections import OrderedDict
from decimal import Decimal, InvalidOperation

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404, ListAPIView
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.filterset import ExpenseFilter
from finance.models import Expense
from finance.serializer.expense import ExpenseSerializer, ExpenseListSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


D0 = Decimal("0.00")


def to_decimal(v) -> Decimal:
    if v in (None, "", "null"):
        return D0
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        return D0


class ExpenseFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in Expense._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class ExpenseViewList(ListCreateAPIView):
    """
    Public list (faqat GET)
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = ExpenseListSerializer   # ✅ yengilroq va foydaliroq
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ExpenseFilter
    search_fields = ('filial__name', 'category__name', 'note', 'employee__full_name', 'summa_total_dollar')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return Expense.objects.filter(is_delete=False)


class ExpenseGroupByDateView(ListAPIView):
    """
    GET /expense/group-by-date/?page=1&page_size=10&date_after=...&date_before=...&filial=...
    Natija: pagination qilingan itemlar date bo'yicha guruhlanadi.
    """
    serializer_class = ExpenseListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ExpenseFilter
    search_fields = ('filial__name', 'category__name', 'note', 'employee__full_name', 'summa_total_dollar')
    ordering = ['-date', '-pk']
    http_method_names = ['get']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            Expense.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'category', 'employee', 'created_by')
        )

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        # 1) pagination
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page, many=True)

        # 2) group by date (paged data ichida)
        grouped = OrderedDict()

        for row in ser.data:
            d = row.get("date") or "No date"

            if d not in grouped:
                grouped[d] = {
                    "date": d,
                    "totals": {
                        "summa_total_dollar": D0,
                        "summa_dollar": D0,
                        "summa_naqt": D0,
                        "summa_kilik": D0,
                        "summa_terminal": D0,
                        "summa_transfer": D0,
                    },
                    "items": []
                }

            g = grouped[d]
            g["items"].append(row)

            t = g["totals"]
            t["summa_total_dollar"] += to_decimal(row.get("summa_total_dollar"))
            t["summa_dollar"] += to_decimal(row.get("summa_dollar"))
            t["summa_naqt"] += to_decimal(row.get("summa_naqt"))
            t["summa_kilik"] += to_decimal(row.get("summa_kilik"))
            t["summa_terminal"] += to_decimal(row.get("summa_terminal"))
            t["summa_transfer"] += to_decimal(row.get("summa_transfer"))

        out = []
        for g in grouped.values():
            g["totals"] = {k: f"{v:.2f}" for k, v in g["totals"].items()}
            out.append(g)

        return self.get_paginated_response(out)


class ExpenseView(ListCreateAPIView):
    serializer_class = ExpenseListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ExpenseFilter
    search_fields = ('filial__name', 'category__name', 'note')
    ordering = ['-date', '-pk']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        # ✅ order_by('pk') olib tashlandi -> DRF ordering ishlaydi
        return (
            Expense.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'category', 'employee', 'created_by')
        )

    def post(self, request, *args, **kwargs):
        serializer = ExpenseSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        filial = serializer.validated_data.get('filial') or getattr(request.user, "order_filial", None)
        if filial is None:
            return Response(
                {"filial": "filial yuborilmadi va userda order_filial ham yo‘q."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.filials.filter(id=filial.id).exists():
            return Response(
                {"detail": "Sizda bu filial uchun xarajat kiritish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        obj = serializer.save(created_by=request.user, filial=filial)
        return Response(ExpenseListSerializer(obj).data, status=status.HTTP_201_CREATED)


class ExpenseDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ✅ xavfsizlik: user faqat o'z filialidagini
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            Expense.objects
            .filter(filial_id__in=user_filial_ids)
            .select_related('filial', 'category', 'employee', 'created_by')
        )

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk, is_delete=False)
        return Response(ExpenseListSerializer(instance).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk, is_delete=False)
        serializer = self.serializer_class(instance, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(updated_by=request.user)
        return Response(ExpenseListSerializer(obj).data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk, is_delete=False)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)