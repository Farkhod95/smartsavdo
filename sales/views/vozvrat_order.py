from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal
from django.db import transaction
from django.db.models import Q

from sales.filterset import VozvratOrderFilter
from sales.models import VozvratOrder, OrderHistoryProduct, Order, Client
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializer.vozvrat_order import VozvratOrderSerializer, VozvratOrderListSerializer, \
    VozvratOrderUpdateSerializer


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
        instance = get_object_or_404(VozvratOrder, id=pk, is_delete=False)

        serializer = VozvratOrderUpdateSerializer(
            instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(VozvratOrder, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


class VozvratOrderHardDeleteView(APIView):
    """
    Faqat is_delete=True bo'lgan VozvratOrder ni DB'dan butunlay o'chiradi.
    O'chirishdan oldin Order va Client balanslarini orqaga qaytaradi.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, pk: int):
        # 1) Faqat soft delete qilinganini o'chiramiz
        vozvrat = get_object_or_404(VozvratOrder.objects.select_for_update(), pk=pk)

        if vozvrat.is_delete is False:
            return Response(
                {"detail": "Avval soft delete qiling (is_delete=True) keyin hard delete qilish mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2) Hisob-kitoblarni qaytarish faqat is_karzinka=False bo'lsa (ya'ni balansga ta'sir qilgan bo'lsa)
        # effect = new_total_debt_client - old_total_debt_client
        # delete paytida: balanslardan effect ni AYIRAMIZ (teskari qilamiz)
        if vozvrat.is_karzinka is False:
            if vozvrat.client_id is None:
                return Response({"detail": "VozvratOrder.client null. Balansni qaytarib bo'lmaydi."},
                                status=status.HTTP_400_BAD_REQUEST)

            if vozvrat.filial_id is None:
                return Response({"detail": "VozvratOrder.filial null. Order topib bo'lmaydi."},
                                status=status.HTTP_400_BAD_REQUEST)

            client = Client.objects.select_for_update().filter(pk=vozvrat.client_id).first()
            if not client:
                return Response({"detail": "Client topilmadi."}, status=status.HTTP_404_NOT_FOUND)

            order = Order.objects.select_for_update().filter(client_id=vozvrat.client_id, filial_id=vozvrat.filial_id).first()
            if not order:
                return Response({"detail": "Order topilmadi (client+filial bo'yicha)."}, status=status.HTTP_404_NOT_FOUND)

            old_debt = vozvrat.old_total_debt_client or Decimal("0")
            new_debt = vozvrat.total_debt_client or Decimal("0")
            effect = new_debt - old_debt  # balansga qo'shilgan delta

            # Reversal (teskari)
            order.total_debt_old_client = order.total_debt_client
            order.total_debt_client = (order.total_debt_client or Decimal("0")) - effect
            order.save(update_fields=["total_debt_old_client", "total_debt_client"])

            client.total_debt = (client.total_debt or Decimal("0")) - effect
            client.save(update_fields=["total_debt"])

        # 3) Shu vozvratga bog'langan mahsulotlarni ham hard delete qilamiz
        # FK SET_NULL bo'lsa ham, “tozalash” uchun o'chirib yuboramiz
        OrderHistoryProduct.objects.filter(vozvrat_order_id=vozvrat.id).delete()

        # 4) VozvratOrder ni butunlay o'chiramiz
        vozvrat.delete()

        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)