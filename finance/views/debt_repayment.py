from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal
from django.db import transaction
from django.db.models import F

from finance.filterset import DebtRepaymentFilter
from finance.models import DebtRepayment
from finance.serializer.debt_repayment import DebtRepaymentSerializer, DebtRepaymentListSerializer, \
    DebtRepaymentAccountingSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.models import Client


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
    ordering = ['-pk']
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
    ordering = ['-pk']

    def get_queryset(self):
        return DebtRepayment.objects.filter(is_delete=False)

    def post(self, request):
        serializer = DebtRepaymentAccountingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class DebtRepaymentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DebtRepaymentAccountingSerializer

    def get_queryset(self):
        return DebtRepayment.objects.all()

    def get(self, request, pk):
        instance = get_object_or_404(DebtRepayment, id=pk)
        serializer = DebtRepaymentListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(DebtRepayment, id=pk, is_delete=False)

        serializer = DebtRepaymentAccountingSerializer(
            instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @transaction.atomic
    def delete(self, request, pk):
        """
        Soft delete:
        - Agar debt_status True bo'lsa rollback (client debtga pulni qaytarib qo'yadi)
        - keyin is_delete=True
        """
        dr = get_object_or_404(
            DebtRepayment.objects.select_for_update(of=("self",)),
            id=pk,
            is_delete=False
        )

        # rollback if confirmed
        if dr.debt_status and dr.client_id:
            client = Client.objects.select_for_update().get(pk=dr.client_id)
            old_paid = dr.summa_total_dollar or Decimal("0")

            # debt back
            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") + old_paid)

        dr.is_delete = True
        dr.save(update_fields=["is_delete", "updated_time"])

        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)



class DebtRepaymentKarzinkaView(ListCreateAPIView):
    serializer_class = DebtRepaymentListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['-pk']
    http_method_names = ['get']

    def get_queryset(self):
        return DebtRepayment.objects.filter(is_delete=True)


class DebtRepaymentDetailKarzinkaView(RetrieveUpdateDestroyAPIView):
    serializer_class = DebtRepaymentSerializer
    http_method_names = ['delete', 'get']

    def get_queryset(self):
        return DebtRepayment.objects.all()

    def get(self, request, pk):
        instance = get_object_or_404(DebtRepayment, id=pk)
        serializer = DebtRepaymentListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, pk):
        dr = get_object_or_404(
            DebtRepayment.objects.select_for_update(of=("self",)),
            id=pk
        )

        if dr.debt_status and dr.client_id:
            client = Client.objects.select_for_update().get(pk=dr.client_id)
            old_paid = dr.summa_total_dollar or Decimal("0")
            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") + old_paid)

        dr.delete()
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)