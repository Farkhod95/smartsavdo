from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from sales.filterset import ClientKeshbekHistoryFilter
from sales.models import ClientKeshbekHistory
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializer.client_keshbek_history import ClientKeshbekHistorySerializer, ClientKeshbekHistoryListSerializer


class ClientKeshbekHistoryFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in ClientKeshbekHistory._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class ClientKeshbekHistoryViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = ClientKeshbekHistorySerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ClientKeshbekHistoryFilter
    search_fields = ('client__full_name', 'order_history')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return ClientKeshbekHistory.objects.all()


class ClientKeshbekHistoryView(ListCreateAPIView):
    serializer_class = ClientKeshbekHistoryListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ClientKeshbekHistoryFilter
    search_fields = ('client__full_name', 'order_history')
    ordering = ['pk']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            ClientKeshbekHistory.objects
            .filter(client__isnull=False, client__filial_id__in=user_filial_ids)
            .select_related('client', 'client__filial')
            .order_by('pk')
        )

    def post(self, request, *args, **kwargs):
        serializer = ClientKeshbekHistorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # (tavsiya) user faqat o'z filialidagi clientga keshbek history qo'sha olsin
        client = serializer.validated_data.get('client')
        if client and client.filial_id:
            if not request.user.filials.filter(id=client.filial_id).exists():
                return Response(
                    {"detail": "Sizda bu client (filial) bo‘yicha amal qilish huquqi yo‘q."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ClientKeshbekHistoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ClientKeshbekHistorySerializer

    def get_queryset(self):
        return ClientKeshbekHistory.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(ClientKeshbekHistory, id=pk)
        serializer = ClientKeshbekHistoryListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(ClientKeshbekHistory, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(ClientKeshbekHistory, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
