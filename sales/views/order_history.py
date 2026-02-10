from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from sales.filterset import OrderHistoryFilter
from sales.models import OrderHistory
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializers import OrderHistorySerializer, OrderHistoryListSerializer, OrderHistoryUpdateSerializer


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


class OrderHistoryView(ListCreateAPIView):
    serializer_class = OrderHistoryListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryFilter
    search_fields = ('order__id', 'client__full_name', 'employee__username', 'note', 'driver_info')
    ordering = ['pk']

    def get_queryset(self):
        return OrderHistory.objects.filter(is_delete=False)

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
