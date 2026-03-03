from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from restapp.pagination import ResultsSetPagination
from accounts.filterset import NoteFilter
from accounts.models import Note
from accounts.serializers import NoteSerializer, NoteListSerializer


class NoteFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in Note._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class NoteView(ListCreateAPIView):
    serializer_class = NoteListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = NoteFilter
    search_fields = ('title', 'text')
    ordering = ['date', '-pk']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Faqat hozirgi user yaratgan note'lar
        return (
            Note.objects
            .filter(is_delete=False, created_by=self.request.user)
            .order_by('date', '-pk')
        )

    def post(self, request, **kwargs):
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class NoteDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Note.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        obj = get_object_or_404(Note, id=pk)
        serializer = NoteListSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj = get_object_or_404(Note, id=pk)
        serializer = self.serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)


class NoteAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        qs = Note.objects.filter(
            created_by=user,
            is_delete=False,
            is_read=False,  # faqat o'qilmaganlarini yangilaymiz
        )

        updated_count = qs.update(
            is_read=True,
            updated_time=timezone.now(),  # auto_now bor, lekin bulk update auto_now ni chaqirmaydi
            updated_by=user,              # bulk update save() chaqirmaydi, shuning uchun qo'lda beramiz
        )

        return Response(
            {
                "ok": True,
                "updated_count": updated_count,
            },
            status=200,
        )