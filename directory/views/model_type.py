from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from directory.filterset import ModelTypeFilter
from directory.models import ModelType
from directory.serializers import ModelTypeSerializer, ModelTypeListSerializer

from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class ModelTypeFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in ModelType._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class ModelTypeViewList(ListCreateAPIView):
    serializer_class = ModelTypeListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    search_fields = ('name', 'sorting')
    permission_classes = (AllowAny,)
    ordering = ['pk']
    http_method_names = ['get']

    def get_queryset(self):
        return ModelType.objects.all()


class ModelTypeView(ListCreateAPIView):
    serializer_class = ModelTypeListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ModelTypeFilter
    search_fields = ('name', 'sorting')
    ordering = ['pk']

    def get_queryset(self):
        return ModelType.objects.all()

    def post(self, request):
        serializer = ModelTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class ModelTypeDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ModelTypeSerializer

    def get_queryset(self):
        return ModelType.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(ModelType, id=pk)
        serializer = ModelTypeListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(ModelType, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(ModelType, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)



