from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ResultsSetPagination(PageNumberPagination):
    page_size = 50
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


class ResultsSetGroupPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200

    def get_grouped_response(self, grouped_results):
        return Response({
            "count": self.page.paginator.count,  # product count (original)
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "group_count": len(grouped_results),  # page ichidagi group count
            "results": grouped_results,
        })