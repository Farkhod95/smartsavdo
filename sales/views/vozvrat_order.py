from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from sales.filterset import VozvratOrderFilter
from sales.models import VozvratOrder
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializer.vozvrat_order import VozvratOrderSerializer, VozvratOrderListSerializer


class VozvratOrderFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in VozvratOrder._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class VozvratOrderViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = VozvratOrderSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = VozvratOrderFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return VozvratOrder.objects.filter(is_delete=False)


class VozvratOrderView(ListCreateAPIView):
    serializer_class = VozvratOrderListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = VozvratOrderFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['pk']

    def get_queryset(self):
        return VozvratOrder.objects.filter(is_delete=False)

    def post(self, request):
        serializer = VozvratOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class VozvratOrderDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = VozvratOrderSerializer

    def get_queryset(self):
        return VozvratOrder.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(VozvratOrder, id=pk)
        serializer = VozvratOrderListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(VozvratOrder, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(VozvratOrder, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
