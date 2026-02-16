from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 1000

    def __init__(self):
        super().__init__()
        self.filters = None

    def get_paginated_response(self, data):
        per_page = self.get_page_size(self.request) or self.page_size

        return Response({
            'pagination': {
                'currentPage': self.page.number,
                'lastPage': self.page.paginator.num_pages,
                'perPage': per_page,
                'total': self.page.paginator.count,
            },
            'results': data,
            'filters': self.filters
        })

    def set_filter(self, filters):
        self.filters = filters


class LargeResultsSetPagination(ResultsSetPagination):
    page_size = 1000
