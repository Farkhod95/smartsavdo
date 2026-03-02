from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.filterset import ExchangeRateFilter
from finance.models import ExchangeRate, ExchangeRateHistory
from finance.serializer.exchange_rate import ExchangeRateSerializer, ExchangeRateListSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class ExchangeRateFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in ExchangeRate._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class ExchangeRateViewList(ListCreateAPIView):
    """
    Public list (faqat GET)
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = ExchangeRateSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ExchangeRateFilter
    search_fields = ('filial__name',)
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return ExchangeRate.objects.all()


class ExchangeRateView(ListCreateAPIView):
    serializer_class = ExchangeRateListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ExchangeRateFilter
    search_fields = ('filial__name',)
    ordering = ['pk']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            ExchangeRate.objects
            .filter(filial_id__in=user_filial_ids)
            .select_related('filial')
            .order_by('pk')
        )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = ExchangeRateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # requestda filial kelgan bo'lsa olamiz, bo'lmasa user.order_filial
        filial = serializer.validated_data.get('filial') or getattr(request.user, 'order_filial', None)

        if filial is None:
            return Response(
                {"filial": "filial yuborilmadi va userda order_filial ham yo‘q."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # user shu filialda ishlaydimi?
        if not request.user.filials.filter(id=filial.id).exists():
            return Response(
                {"detail": "Sizda bu filial uchun kurs qo‘shish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Yangi ExchangeRate
        rate: ExchangeRate = serializer.save(created_by=request.user, updated_by=request.user, filial=filial)

        # History yozamiz (create bo'lgani uchun old=0)
        ExchangeRateHistory.objects.create(
            exchange_rate=rate,
            filial=filial,
            old_dollar=0,
            new_dollar=rate.dollar,
            created_by=request.user,
            updated_by=request.user,
        )

        # response list serializerda chiroyli chiqsin
        out = ExchangeRateListSerializer(rate).data
        return Response(out, status=status.HTTP_201_CREATED)


class ExchangeRateDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ExchangeRateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExchangeRate.objects.all()

    def get(self, request, pk):
        instance = get_object_or_404(ExchangeRate, id=pk)
        serializer = ExchangeRateListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, pk):
        # select_for_update -> parallel update'larda history aralashib ketmasin
        instance: ExchangeRate = get_object_or_404(
            ExchangeRate.objects.select_for_update(),
            id=pk
        )

        # (ixtiyoriy) filial huquqini tekshirish:
        if instance.filial_id and not request.user.filials.filter(id=instance.filial_id).exists():
            return Response(
                {"detail": "Sizda bu filial kursini o‘zgartirish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        old_dollar = instance.dollar

        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_rate: ExchangeRate = serializer.save(updated_by=request.user)

        # Agar qiymat o'zgargan bo'lsa history yozamiz
        if old_dollar != updated_rate.dollar:
            ExchangeRateHistory.objects.create(
                exchange_rate=updated_rate,
                filial=updated_rate.filial,
                old_dollar=old_dollar,
                new_dollar=updated_rate.dollar,
                created_by=request.user,
                updated_by=request.user,
            )

        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @transaction.atomic
    def delete(self, request, pk):
        instance = get_object_or_404(ExchangeRate, id=pk)

        # (ixtiyoriy) filial huquqini tekshirish:
        if instance.filial_id and not request.user.filials.filter(id=instance.filial_id).exists():
            return Response(
                {"detail": "Sizda bu filial kursini o‘chirish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        instance.delete()
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)