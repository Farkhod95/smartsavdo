from collections import OrderedDict
from django.db.models.functions import TruncDate, Coalesce
from django.db.models import DateField
from decimal import Decimal
from django.db import transaction
from django.db.models import F

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404, GenericAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from sales.filterset import OrderHistoryFilter
from sales.models import OrderHistory, OrderHistoryProduct, Order, Client, ClientKeshbekHistory
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializer.order_history import OrderHistorySerializer, OrderHistoryListSerializer, \
    OrderHistoryUpdateSerializer, OrderHistorySellSerializer


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
        user = self.request.user

        # agar userda order_filial bo'lmasa - bo'sh queryset
        if not getattr(user, "order_filial_id", None):
            return OrderHistory.objects.none()

        return (
            OrderHistory.objects
            .filter(
                is_delete=False,
                order_filial_id=user.order_filial_id,  # <-- tuzatildi
            )
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



class OrderHistoryDebtorProductView(ListCreateAPIView):
    serializer_class = OrderHistoryListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryFilter
    search_fields = ('order__id', 'client__full_name', 'employee__username', 'note', 'driver_info')
    ordering = ['-date', '-pk']
    http_method_names = ['get']

    def get_queryset(self):
        user = self.request.user

        # agar userda order_filial bo'lmasa - bo'sh queryset
        if not getattr(user, "order_filial_id", None):
            return OrderHistory.objects.none()

        return (
            OrderHistory.objects
            .filter(
                is_delete=False,
                is_debtor_product=True,
                is_karzinka=False,
                order_filial_id=user.order_filial_id,  # <-- tuzatildi
            )
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


class OrderHistoryCreateUpdate(CreateAPIView):
    serializer_class = OrderHistorySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client = serializer.validated_data.get('client')

        if client is None:
            return Response(
                {"message": "client majburiy."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order_filial = serializer.validated_data.get('order_filial') or getattr(request.user, 'order_filial', None)
        if order_filial is None:
            return Response(
                {"message": "order_filial yuborilmadi va userda order_filial ham yo‘q."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.filials.filter(id=order_filial.id).exists():
            return Response(
                {"message": "Sizda bu filial uchun order history yaratish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        existing = (
            OrderHistory.objects
            .filter(
                client=client,
                is_karzinka=True,
                is_delete=False,
                created_by=request.user,  # kerak bo'lmasa olib tashlang
            )
            .order_by('-pk')
            .first()
        )

        if existing:
            return Response(
                {
                    "message": "Bu mijozda tugallanmagan buyurtma mavjud",
                    "data": OrderHistorySerializer(existing).data
                },
                status=status.HTTP_200_OK
            )

        obj = serializer.save(
            created_by=request.user,
            order_filial=order_filial,
            is_karzinka=True,
        )

        return Response(
            {
                "message": "Savdo muvaffaqiyatli yaratildi",
                "data": OrderHistorySerializer(obj).data
            },
            status=status.HTTP_200_OK   # <-- endi bu ham 200
        )


class OrderHistoryAppView(ListCreateAPIView):
    serializer_class = OrderHistoryListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryFilter
    search_fields = ('order__id', 'client__full_name', 'employee__username', 'note', 'driver_info')
    ordering = ['pk']
    http_method_names = ['get']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        # tezlik uchun (serializer detail lar N+1 bo'lib ketmasin)
        return (
            OrderHistory.objects
            .filter(is_delete=False, order_filial_id__in=user_filial_ids, is_karzinka=False)
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
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryFilter
    search_fields = ('order__id', 'client__full_name', 'employee__username', 'note', 'driver_info')
    ordering = ['pk']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        # tezlik uchun (serializer detail lar N+1 bo'lib ketmasin)
        return (
            OrderHistory.objects
            .filter(is_delete=False, order_filial_id__in=user_filial_ids)
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

    def post(self, request, *args, **kwargs):
        serializer = OrderHistorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # requestda order_filial kelgan bo'lsa olamiz, bo'lmasa user.order_filial
        order_filial = serializer.validated_data.get('order_filial') or request.user.order_filial

        if order_filial is None:
            return Response(
                {"order_filial": "order_filial yuborilmadi va userda order_filial ham yo‘q."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # user shu filialda ishlaydimi?
        if not request.user.filials.filter(id=order_filial.id).exists():
            return Response(
                {"detail": "Sizda bu filial uchun order history yaratish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(created_by=request.user, order_filial=order_filial)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderHistorySellView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderHistorySerializer
    http_method_names = ['put']

    def put(self, request, pk):
        instance = get_object_or_404(OrderHistory, id=pk, is_delete=False)

        serializer = OrderHistorySellSerializer(
            instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class OrderHistoryEditView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderHistorySerializer
    http_method_names = ['put']

    def put(self, request, pk):
        instance = get_object_or_404(OrderHistory, id=pk, is_delete=False)

        serializer = OrderHistorySellSerializer(
            instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


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
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryFilter
    search_fields = ('order__id', 'client__full_name', 'employee__username', 'note', 'driver_info')
    ordering = ['-date', '-pk']
    http_method_names = ['get']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        # tezlik uchun (serializer detail lar N+1 bo'lib ketmasin)
        return (
            OrderHistory.objects
            .filter(is_delete=True, order_filial_id__in=user_filial_ids)
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

            for idx, r in enumerate(rows):
                r['number'] = n - idx  # N..1 (har date uchun alohida)

            results.append({
                "date": date_str,
                "count": n,
                "items": rows
            })

        return self.get_paginated_response(results)


class OrderHistoryRestoreKarzinkaView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderHistoryListSerializer
    http_method_names = ['put']  # faqat PUT

    @transaction.atomic
    def put(self, request, pk: int):
        user = request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        oh = get_object_or_404(
            OrderHistory.objects.select_for_update(),
            pk=pk,
            is_delete=True,
            order_filial_id__in=user_filial_ids
        )

        oh.is_delete = False
        oh.save(update_fields=['is_delete'])

        return Response(self.get_serializer(oh).data, status=status.HTTP_200_OK)


class OrderHistoryDetailKarzinkaView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderHistorySerializer
    http_method_names = ['delete', 'get']

    def get_queryset(self):
        return OrderHistory.objects.all()

    def get(self, request, pk):
        instance = get_object_or_404(OrderHistory, id=pk)
        serializer = OrderHistoryListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, pk):
        """
        HARD DELETE:
        - Agar OrderHistory posted bo'lsa (order_status=True) -> Order, Client, Cashback hisoblarini rollback qiladi
        - Keyin OrderHistoryProduct larni hard delete qiladi
        - Keyin OrderHistory ni hard delete qiladi
        """

        # 1) OrderHistory ni lock qilib olamiz
        oh = get_object_or_404(
            OrderHistory.objects.select_for_update().select_related("order", "client"),
            id=pk
        )

        # 2) Agar posted bo'lsa: rollback
        if oh.order_status:
            old_profit = oh.all_profit_dollar or Decimal("0")
            old_debt_today = oh.total_debt_today_client or Decimal("0")
            old_product_sum = oh.all_product_summa or Decimal("0")
            old_paid_total = oh.summa_total_dollar or Decimal("0")

            # Order rollback
            if oh.order_id:
                order = Order.objects.select_for_update().get(pk=oh.order_id)
                Order.objects.filter(pk=order.pk).update(
                    all_profit_dollar=F("all_profit_dollar") - old_profit,
                    total_debt_old_client=F("total_debt_client"),
                    total_debt_client=F("total_debt_client") - old_debt_today,
                    all_product_summa=F("all_product_summa") - old_product_sum,
                    summa_total_dollar=F("summa_total_dollar") - old_paid_total,
                )

            # Client rollback
            if oh.client_id:
                client = Client.objects.select_for_update().get(pk=oh.client_id)
                Client.objects.filter(pk=client.pk).update(
                    total_debt=F("total_debt") - old_debt_today
                )

            # Cashback rollback
            ClientKeshbekHistory.objects.filter(order_history=oh.id).delete()

        # 3) OrderHistoryProduct larni hard delete
        OrderHistoryProduct.objects.filter(order_history_id=pk).delete()

        # 4) OrderHistory ni hard delete
        oh.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)