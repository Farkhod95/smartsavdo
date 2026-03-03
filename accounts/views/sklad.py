from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.filterset import SkladFilter
from accounts.models import Sklad
from accounts.serializers import SkladListSerializer, SkladSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class SkladFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in Sklad._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class SkladViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = SkladSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SkladFilter
    search_fields = ('name', 'phone_number', 'address', 'filial__name')
    ordering = ['sorting', '-id']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return Sklad.objects.filter(is_delete=False)


class SkladView(ListCreateAPIView):
    serializer_class = SkladListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SkladFilter
    search_fields = ('name', 'phone_number', 'address', 'filial__name')
    ordering = ['sorting', '-id']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            Sklad.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'region', 'district')
            .order_by('sorting', '-id')
        )

    def post(self, request, *args, **kwargs):
        serializer = SkladSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # requestda filial kelgan bo'lsa olamiz, bo'lmasa user.order_filial
        filial = serializer.validated_data.get('filial') or request.user.order_filial

        if filial is None:
            return Response(
                {"filial": "filial yuborilmadi va userda order_filial ham yo‘q."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # user shu filialda ishlaydimi?
        if not request.user.filials.filter(id=filial.id).exists():
            return Response(
                {"detail": "Sizda bu filial uchun sklad yaratish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(created_by=request.user, filial=filial)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SkladDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SkladSerializer

    def get_queryset(self):
        return Sklad.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(Sklad, id=pk)
        serializer = SkladListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(Sklad, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(Sklad, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


class ProductTypeSuggestSortingByModelView(APIView):
    """
    ProductType uchun sorting tavsiya (har bir madel kesimida).
    GET /product-type/<int:madel>/sorting
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, madel):
        used = (
            Sklad.objects
            .filter(
                is_delete=False,
                madel_id=madel,
                sorting__isnull=False
            )
            .order_by('sorting')
            .values_list('sorting', flat=True)
        )

        suggested = 1
        for s in used:
            try:
                s_int = int(s)
            except (TypeError, ValueError):
                continue

            if s_int < suggested:
                continue
            if s_int == suggested:
                suggested += 1
            else:
                break

        return Response(
            {
                "madel": madel,
                "suggested_sorting": suggested,
                "message": "Tavsiya etilgan tartib raqam."
            },
            status=status.HTTP_200_OK
        )