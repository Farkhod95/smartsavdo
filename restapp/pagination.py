from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from urllib.parse import urlparse, urlunparse


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

    def _force_https(self, url: str | None) -> str | None:
        if not url:
            return url

        # agar allaqachon https bo'lsa o'zgartirmaymiz
        parsed = urlparse(url)
        if parsed.scheme == "https":
            return url

        # faqat scheme'ni https ga almashtiramiz
        return urlunparse(parsed._replace(scheme="https"))

    def get_grouped_response(self, grouped_results):
        next_link = self._force_https(self.get_next_link())
        prev_link = self._force_https(self.get_previous_link())

        return Response({
            "count": self.page.paginator.count,  # product count (original)
            "next": next_link,
            "previous": prev_link,
            "group_count": len(grouped_results),  # page ichidagi group count
            "results": grouped_results,
        })