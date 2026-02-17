from collections import OrderedDict
from django.db.models.functions import TruncDate, Coalesce
from django.db.models import DateField
from django.db import transaction

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from sales.filterset import OrderHistoryFilter
from sales.models import OrderHistory, OrderHistoryProduct
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializer.order_history import OrderHistorySerializer, OrderHistoryListSerializer, \
    OrderHistoryUpdateSerializer


class OrderHistoryFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in OrderHistory._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class OrderHistoryViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = OrderHistorySerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryFilter
    search_fields = ('order__id', 'client__full_name', 'employee__username', 'note', 'driver_info')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return OrderHistory.objects.filter(is_delete=False)


class OrderHistorySelfView(ListCreateAPIView):
    serializer_class = OrderHistoryListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryFilter
    search_fields = ('order__id', 'client__full_name', 'employee__username', 'note', 'driver_info')
    ordering = ['-date', '-pk']
    http_method_names = ['get']

    def get_queryset(self):
        # tezlik uchun (serializer detail lar N+1 bo'lib ketmasin)
        return (
            OrderHistory.objects
            .filter(is_delete=False, created_by=self.request.user)
            .select_related('order', 'client', 'order_filial', 'created_by', 'employee')
        )

    def list(self, request, *args, **kwargs):
        # 1) filter/search/ordering lar ishlasin
        qs = self.filter_queryset(self.get_queryset())

        # 2) Guruh sanasi: date bo'lsa o'sha, bo'lmasa created_time sanasi
        qs = qs.annotate(
            group_date=Coalesce(
                'date',
                TruncDate('created_time'),
                output_field=DateField()
            )
        )

        # 3) Pagination faqat sanalar bo'yicha (date lar ro'yxati)
        dates_qs = (
            qs.values_list('group_date', flat=True)
            .distinct()
            .order_by('-group_date')
        )

        page_dates = self.paginate_queryset(dates_qs)
        if page_dates is None:
            page_dates = list(dates_qs)
        else:
            page_dates = list(page_dates)

        # 4) Shu sahifadagi sanalarga tegishli historylar
        items_qs = (
            qs.filter(group_date__in=page_dates)
              .order_by('-group_date', '-pk')  # har bir date ichida ham ko'rinish: yangisi yuqorida
        )

        serializer = self.get_serializer(items_qs, many=True)
        items = serializer.data

        # 5) page_dates tartibini saqlagan holda guruhlash
        grouped = OrderedDict((str(d), []) for d in page_dates)

        for row in items:
            # key: row['date'] bo'lsa shu, bo'lmasa created_time dan YYYY-MM-DD
            if row.get('date'):
                key = row['date']
            else:
                ct = row.get('created_time')
                key = ct[:10] if ct else None

            if key in grouped:
                grouped[key].append(row)

        # 6) Har bir date ichida nomeratsiya 1 dan boshlansin,
        # lekin yuqorida katta raqam ko‘rinsin (N..1)
        results = []
        for date_str, rows in grouped.items():
            n = len(rows)

            # rows tartibi: yuqorida yangisi (biz -pk qilganmiz)
            # shuning uchun birinchi ko'rinadigan item = n, oxiri = 1
            for idx, r in enumerate(rows):
                r['number'] = n - idx  # N..1 (har date uchun alohida)

            results.append({
                "date": date_str,
                "count": n,
                "items": rows
            })

        return self.get_paginated_response(results)

class OrderHistoryView(ListCreateAPIView):
    serializer_class = OrderHistoryListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryFilter
    search_fields = ('order__id', 'client__full_name', 'employee__username', 'note', 'driver_info')
    ordering = ['pk']

    def get_queryset(self):
        # tezlik uchun (serializer detail lar N+1 bo'lib ketmasin)
        return (
            OrderHistory.objects
            .filter(is_delete=False)
            .select_related('order', 'client', 'order_filial', 'created_by', 'employee')
        )

    def list(self, request, *args, **kwargs):
        # 1) filter/search/ordering lar ishlasin
        qs = self.filter_queryset(self.get_queryset())

        # 2) Guruh sanasi: date bo'lsa o'sha, bo'lmasa created_time sanasi
        qs = qs.annotate(
            group_date=Coalesce(
                'date',
                TruncDate('created_time'),
                output_field=DateField()
            )
        )

        # 3) Pagination faqat sanalar bo'yicha (date lar ro'yxati)
        dates_qs = (
            qs.values_list('group_date', flat=True)
            .distinct()
            .order_by('-group_date')
        )

        page_dates = self.paginate_queryset(dates_qs)
        if page_dates is None:
            page_dates = list(dates_qs)
        else:
            page_dates = list(page_dates)

        # 4) Shu sahifadagi sanalarga tegishli historylar
        items_qs = (
            qs.filter(group_date__in=page_dates)
              .order_by('-group_date', '-pk')  # har bir date ichida ham ko'rinish: yangisi yuqorida
        )

        serializer = self.get_serializer(items_qs, many=True)
        items = serializer.data

        # 5) page_dates tartibini saqlagan holda guruhlash
        grouped = OrderedDict((str(d), []) for d in page_dates)

        for row in items:
            # key: row['date'] bo'lsa shu, bo'lmasa created_time dan YYYY-MM-DD
            if row.get('date'):
                key = row['date']
            else:
                ct = row.get('created_time')
                key = ct[:10] if ct else None

            if key in grouped:
                grouped[key].append(row)

        # 6) Har bir date ichida nomeratsiya 1 dan boshlansin,
        # lekin yuqorida katta raqam ko‘rinsin (N..1)
        results = []
        for date_str, rows in grouped.items():
            n = len(rows)

            # rows tartibi: yuqorida yangisi (biz -pk qilganmiz)
            # shuning uchun birinchi ko'rinadigan item = n, oxiri = 1
            for idx, r in enumerate(rows):
                r['number'] = n - idx  # N..1 (har date uchun alohida)

            results.append({
                "date": date_str,
                "count": n,
                "items": rows
            })

        return self.get_paginated_response(results)


    def post(self, request):
        serializer = OrderHistorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user, order_filial=self.request.user.order_filial)
        return Response(serializer.data, status.HTTP_201_CREATED)


class OrderHistoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderHistorySerializer

    def get_queryset(self):
        return OrderHistory.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(OrderHistory, id=pk)
        serializer = OrderHistoryListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(OrderHistory, id=pk, is_delete=False)

        serializer = OrderHistoryUpdateSerializer(
            instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(OrderHistory, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


# ============================== Karzinka  ===============================

class OrderHistoryKarzinkaView(ListCreateAPIView):
    serializer_class = OrderHistoryListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryFilter
    search_fields = ('order__id', 'client__full_name', 'employee__username', 'note', 'driver_info')
    ordering = ['-date', '-pk']
    http_method_names = ['get']

    def get_queryset(self):
        # tezlik uchun (serializer detail lar N+1 bo'lib ketmasin)
        return (
            OrderHistory.objects
            .filter(is_delete=True)
            .select_related('order', 'client', 'order_filial', 'created_by', 'employee')
        )

    def list(self, request, *args, **kwargs):
        # 1) filter/search/ordering lar ishlasin
        qs = self.filter_queryset(self.get_queryset())

        # 2) Guruh sanasi: date bo'lsa o'sha, bo'lmasa created_time sanasi
        qs = qs.annotate(
            group_date=Coalesce(
                'date',
                TruncDate('created_time'),
                output_field=DateField()
            )
        )

        # 3) Pagination faqat sanalar bo'yicha (date lar ro'yxati)
        dates_qs = (
            qs.values_list('group_date', flat=True)
            .distinct()
            .order_by('-group_date')
        )

        page_dates = self.paginate_queryset(dates_qs)
        if page_dates is None:
            page_dates = list(dates_qs)
        else:
            page_dates = list(page_dates)

        # 4) Shu sahifadagi sanalarga tegishli historylar
        items_qs = (
            qs.filter(group_date__in=page_dates)
              .order_by('-group_date', '-pk')  # har bir date ichida ham ko'rinish: yangisi yuqorida
        )

        serializer = self.get_serializer(items_qs, many=True)
        items = serializer.data

        # 5) page_dates tartibini saqlagan holda guruhlash
        grouped = OrderedDict((str(d), []) for d in page_dates)

        for row in items:
            # key: row['date'] bo'lsa shu, bo'lmasa created_time dan YYYY-MM-DD
            if row.get('date'):
                key = row['date']
            else:
                ct = row.get('created_time')
                key = ct[:10] if ct else None

            if key in grouped:
                grouped[key].append(row)

        # 6) Har bir date ichida nomeratsiya 1 dan boshlansin,
        # lekin yuqorida katta raqam ko‘rinsin (N..1)
        results = []
        for date_str, rows in grouped.items():
            n = len(rows)

            # rows tartibi: yuqorida yangisi (biz -pk qilganmiz)
            # shuning uchun birinchi ko'rinadigan item = n, oxiri = 1
            for idx, r in enumerate(rows):
                r['number'] = n - idx  # N..1 (har date uchun alohida)

            results.append({
                "date": date_str,
                "count": n,
                "items": rows
            })

        return self.get_paginated_response(results)


class OrderHistoryDetailKarzinkaView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderHistorySerializer
    http_method_names = ['delete', 'get']

    def get_queryset(self):
        return OrderHistory.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(OrderHistory, id=pk)
        serializer = OrderHistoryListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, pk):
        instance = get_object_or_404(OrderHistory, id=pk)

        OrderHistoryProduct.objects.filter(order_history_id=pk).delete()
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)