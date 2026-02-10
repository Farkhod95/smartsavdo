from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from accounts.filterset import RegionssFilter
from accounts.models import Region
from accounts.serializers import RegionSerializer, RegionListSerializer

from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class RegionFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in Region._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class RegionViewList(ListCreateAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = RegionListSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    search_fields = ('name', 'code')

    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return Region.objects.all()


class RegionView(ListCreateAPIView):
    serializer_class = RegionListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = RegionssFilter
    search_fields = ('name', 'code')
    ordering = ['pk']

    def get_queryset(self):
        return Region.objects.all()

    def post(self, request):
        serializer = RegionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)
        # regions_data =[
        #     {
        #         "id": 1,
        #         "code": 17,
        #         "name": "Andijan region",
        #         "name_en": "Andijan region",
        #         "name_uz": "Andijon viloyati",
        #         "name_ru": "Андижанская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 2,
        #         "code": 20,
        #         "name": "Bukhara region",
        #         "name_en": "Bukhara region",
        #         "name_uz": "Buxoro viloyati",
        #         "name_ru": "Бухарская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 3,
        #         "code": 13,
        #         "name": "Jizzakh region",
        #         "name_en": "Jizzakh region",
        #         "name_uz": "Jizzax viloyati",
        #         "name_ru": "Джизакская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 4,
        #         "code": 18,
        #         "name": "Kashkadarya region",
        #         "name_en": "Kashkadarya region",
        #         "name_uz": "Qashqadaryo viloyati",
        #         "name_ru": "Кашкадарьинская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 5,
        #         "code": 21,
        #         "name": "Navoi region",
        #         "name_en": "Navoi region",
        #         "name_uz": "Navoiy viloyati",
        #         "name_ru": "Навоийская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 6,
        #         "code": 16,
        #         "name": "Namangan region",
        #         "name_en": "Namangan region",
        #         "name_uz": "Namangan viloyati",
        #         "name_ru": "Наманганская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 7,
        #         "code": 14,
        #         "name": "Samarkand region",
        #         "name_en": "Samarkand region",
        #         "name_uz": "Samarqand viloyati",
        #         "name_ru": "Самаркандская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 8,
        #         "code": 19,
        #         "name": "Surkhandarya region",
        #         "name_en": "Surkhandarya region",
        #         "name_uz": "Surxondaryo viloyati",
        #         "name_ru": "Сурхандарьинская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 9,
        #         "code": 12,
        #         "name": "Syrdarya region",
        #         "name_en": "Syrdarya region",
        #         "name_uz": "Sirdaryo viloyati",
        #         "name_ru": "Сырдарьинская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 10,
        #         "code": 10,
        #         "name": "Tashkent city",
        #         "name_en": "Tashkent city",
        #         "name_uz": "Toshkent shahri",
        #         "name_ru": "город Ташкент",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 11,
        #         "code": 11,
        #         "name": "Tashkent region",
        #         "name_en": "Tashkent region",
        #         "name_uz": "Toshkent viloyati",
        #         "name_ru": "Ташкентская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 12,
        #         "code": 15,
        #         "name": "Fergana region",
        #         "name_en": "Fergana region",
        #         "name_uz": "Farg'ona viloyati",
        #         "name_ru": "Ферганская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 13,
        #         "code": 22,
        #         "name": "Khorezm region",
        #         "name_en": "Khorezm region",
        #         "name_uz": "Xorazm viloyati",
        #         "name_ru": "Хорезмская область",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     },
        #     {
        #         "id": 14,
        #         "code": 23,
        #         "name": "Republic of Karakalpakstan",
        #         "name_en": "Republic of Karakalpakstan",
        #         "name_uz": "Qoraqalpog'iston Respublikasi",
        #         "name_ru": "Республика Каракалпакстан",
        #         "created_time": "2020-01-01 00:00:00+00:00",
        #         "updated_time": "2020-01-01 00:00:00+00:00",
        #         "created_by": 1
        #     }
        # ]
        #
        # for region in regions_data:
        #     region_data = {
        #         'code': region.get('code'),
        #         'name': region.get('name_uz'),
        #         'name_uz': region.get('name_uz'),
        #         'name_ru': region.get('name_ru'),
        #         'name_en': region.get('name_en'),
        #     }
        #
        #     # code bo‘yicha mavjudligini tekshiramiz
        #     region_obj = Region.objects.filter(code=region_data['code']).first()
        #
        #     if region_obj:
        #         # UPDATE
        #         serializer = RegionSerializer(region_obj, data=region_data, partial=True)
        #         action = "updated"
        #     else:
        #         # CREATE
        #         serializer = RegionSerializer(data=region_data)
        #         action = "created"
        #
        #     if serializer.is_valid():
        #         serializer.save()
        #         print(f"Region {region_data.get('name')} {action} successfully.")
        #     else:
        #         print(f"Validation errors for region {region_data.get('name')}: {serializer.errors}")
        #
        # return Response({}, status=status.HTTP_201_CREATED)


class RegionDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = RegionSerializer

    def get_queryset(self):
        return Region.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        region = get_object_or_404(Region, id=pk)
        serializer = RegionListSerializer(region)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        region = get_object_or_404(Region, id=pk)
        serializer = self.serializer_class(region, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        region = get_object_or_404(Region, id=pk)
        region.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)



