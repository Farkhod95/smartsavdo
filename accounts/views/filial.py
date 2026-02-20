from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.exceptions import APIException
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.filterset import FilialFilter
from accounts.models import Filial
from accounts.serializers import FilialListSerializer, FilialSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class FilialFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in Filial._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class FilialViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = FilialSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = FilialFilter
    search_fields = ('name', 'phone_number', 'address')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return Filial.objects.filter(is_delete=False)


class FilialSelfView(ListCreateAPIView):
    serializer_class = FilialListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = FilialFilter
    search_fields = ('name', 'phone_number', 'address')
    ordering = ['pk']
    http_method_names = ['get']

    def get_queryset(self):
        user = self.request.user
        return (
            Filial.objects
            .filter(is_delete=False, user_filials=user)  # related_name='user_company'
            .distinct()
            .order_by('pk')
        )


class FilialView(ListCreateAPIView):
    serializer_class = FilialListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = FilialFilter
    search_fields = ('name', 'phone_number', 'address')
    ordering = ['pk']

    def get_queryset(self):
        return Filial.objects.filter(is_delete=False)

    def post(self, request):
        serializer = FilialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class FilialDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = FilialSerializer

    def get_queryset(self):
        return Filial.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(Filial, id=pk)
        serializer = FilialListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(Filial, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(Filial, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
