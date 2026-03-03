from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.filterset import FilialAccountFilter
from accounts.models import FilialAccount
from accounts.serializers import FilialAccountListSerializer, FilialAccountSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


def _not_found(msg="Topilmadi."):
    return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)


def _forbidden(msg="Sizda dostup yo‘q."):
    return Response({"detail": msg}, status=status.HTTP_403_FORBIDDEN)


class FilialAccountFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in FilialAccount._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, "max_length", None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info, status=status.HTTP_200_OK)


class FilialAccountViewList(ListCreateAPIView):
    """
    Public list (faqat GET).
    Agar buni ham yopmoqchi bo‘lsangiz: AllowAny -> IsAuthenticated qiling.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = FilialAccountSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = FilialAccountFilter
    search_fields = ("filial__name",)
    ordering = ["pk"]
    http_method_names = ["get"]
    pagination_class = None

    def get_queryset(self):
        # public bo'lgani uchun hech qanday dostup cheklovi yo'q (sizning eski logikangiz)
        return FilialAccount.objects.all().select_related("filial")


class FilialAccountView(ListCreateAPIView):
    serializer_class = FilialAccountListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = FilialAccountFilter
    search_fields = ("filial__name",)
    ordering = ["pk"]

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list("id", flat=True)

        return (
            FilialAccount.objects
            .filter(filial_id__in=user_filial_ids)
            .select_related("filial")
            .order_by("pk")
        )

    def post(self, request, *args, **kwargs):
        serializer = FilialAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        filial = serializer.validated_data.get("filial")
        filial_id = filial.id if filial else None

        if not filial_id:
            return Response({"filial": "filial yuborish shart."}, status=status.HTTP_400_BAD_REQUEST)

        # dostup tekshiruvi
        if not request.user.filials.filter(id=filial_id).exists():
            return _forbidden("Sizda bu filial uchun FilialAccount yaratish huquqi yo‘q.")

        obj = serializer.save(created_by=request.user)

        # response list ko'rinish (detail bilan)
        return Response(FilialAccountListSerializer(obj).data, status=status.HTTP_201_CREATED)


class FilialAccountDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = FilialAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # DRF ichki ishlatadi, lekin biz o'zimiz _get_obj() bilan tekshiramiz
        return FilialAccount.objects.all().select_related("filial")

    def _get_obj(self, request, pk: int):
        try:
            pk_int = int(pk)
        except Exception:
            return None, Response({"detail": "id noto‘g‘ri (int bo‘lishi kerak)."}, status=status.HTTP_400_BAD_REQUEST)

        obj = FilialAccount.objects.select_related("filial").filter(id=pk_int).first()
        if not obj:
            return None, _not_found("FilialAccount topilmadi.")

        # dostup: user faqat o'z filiali
        if obj.filial_id is None:
            return None, Response({"detail": "FilialAccount.filial null. Dostup tekshirib bo‘lmaydi."},
                                  status=status.HTTP_400_BAD_REQUEST)

        if not request.user.filials.filter(id=obj.filial_id).exists():
            return None, _forbidden("Sizda bu filial accountiga dostup yo‘q.")

        return obj, None

    def get(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err
        return Response(FilialAccountListSerializer(obj).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err

        serializer = self.serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)

        # agar filialni o'zgartirmoqchi bo'lsa ham, yangi filial ham userga tegishli bo'lsin
        new_filial = serializer.validated_data.get("filial")
        if new_filial and (not request.user.filials.filter(id=new_filial.id).exists()):
            return _forbidden("Sizda bu filialga FilialAccountni o‘tkazish huquqi yo‘q.")

        saved = serializer.save(updated_by=request.user)
        return Response(self.serializer_class(saved).data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        obj, err = self._get_obj(request, pk)
        if err:
            return err

        # sizda FilialAccount da is_delete bo'lsa — soft delete
        obj.is_delete = True
        obj.save(update_fields=["is_delete", "updated_time"])
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)