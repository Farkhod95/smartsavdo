from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from suppliers.filterset import SupplierAccountFilter
from suppliers.models import SupplierAccount
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from suppliers.serializer.supplier_account import SupplierAccountSerializer, SupplierAccountListSerializer


class SupplierAccountFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in SupplierAccount._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class SupplierAccountViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = SupplierAccountSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SupplierAccountFilter
    search_fields = ('supplier__name',)
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return SupplierAccount.objects.all()


class SupplierAccountView(ListCreateAPIView):
    serializer_class = SupplierAccountListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SupplierAccountFilter
    search_fields = ('supplier__name',)
    ordering = ['pk']

    def get_queryset(self):
        return SupplierAccount.objects.all()

    def post(self, request):
        serializer = SupplierAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class SupplierAccountDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SupplierAccountSerializer

    def get_queryset(self):
        return SupplierAccount.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(SupplierAccount, id=pk)
        serializer = SupplierAccountListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(SupplierAccount, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(SupplierAccount, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
