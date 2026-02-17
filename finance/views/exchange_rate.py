from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.filterset import ExchangeRateFilter
from finance.models import ExchangeRate
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
    Public list (faqat GET), DistrictViewList kabi.
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
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ExchangeRateFilter
    search_fields = ('filial__name',)
    ordering = ['pk']

    def get_queryset(self):
        return ExchangeRate.objects.all()

    def post(self, request):
        serializer = ExchangeRateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class ExchangeRateDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ExchangeRateSerializer

    def get_queryset(self):
        return ExchangeRate.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(ExchangeRate, id=pk)
        serializer = ExchangeRateListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(ExchangeRate, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(ExchangeRate, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
