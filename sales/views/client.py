from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from sales.filterset import ClientFilter
from sales.models import Client
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializer.client import ClientSerializer, ClientListSerializer


class ClientFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in Client._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class ClientViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = ClientSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ClientFilter
    search_fields = ('full_name', 'phone_number', 'telegram_id')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return Client.objects.filter(is_delete=False, is_active=True)


class ClientView(ListCreateAPIView):
    serializer_class = ClientListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ClientFilter
    search_fields = ('full_name', 'phone_number', 'telegram_id')
    ordering = ['pk']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            Client.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'region', 'district')
            .order_by('pk')
        )

    def post(self, request, *args, **kwargs):
        serializer = ClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # user faqat o'zi ishlaydigan filialga client qo'sha olsin
        filial = serializer.validated_data.get('filial')
        if filial and not request.user.filials.filter(id=filial.id).exists():
            return Response(
                {"detail": "Sizda bu filialga client qo‘shish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ClientDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ClientSerializer

    def get_queryset(self):
        return Client.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(Client, id=pk)
        serializer = ClientListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(Client, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(Client, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
