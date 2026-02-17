from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.filterset import DebtRepaymentFilter
from finance.models import DebtRepayment
from finance.serializer.debt_repayment import DebtRepaymentSerializer, DebtRepaymentListSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class DebtRepaymentFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in DebtRepayment._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class DebtRepaymentViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = DebtRepaymentSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return DebtRepayment.objects.filter(is_delete=False)


class DebtRepaymentView(ListCreateAPIView):
    serializer_class = DebtRepaymentListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['pk']

    def get_queryset(self):
        return DebtRepayment.objects.filter(is_delete=False)

    def post(self, request):
        serializer = DebtRepaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class DebtRepaymentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DebtRepaymentSerializer

    def get_queryset(self):
        return DebtRepayment.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(DebtRepayment, id=pk)
        serializer = DebtRepaymentListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(DebtRepayment, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(DebtRepayment, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
