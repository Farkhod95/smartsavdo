from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from sales.models import OrderHistory
from sales.serializer.order_history import ReportOrderHistoryListSerializer


class ReportOrderHistoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ReportOrderHistoryListSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def get(self, request, pk):
        instance = get_object_or_404(OrderHistory, id=pk)
        serializer = ReportOrderHistoryListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)