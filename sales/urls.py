from django.urls import re_path, path

from sales.views.client import ClientView, ClientDetailView, ClientFieldInfoView
from sales.views.client_keshbek_history import ClientKeshbekHistoryView, ClientKeshbekHistoryDetailView, \
    ClientKeshbekHistoryFieldInfoView
from sales.views.order import OrderView, OrderDetailView, OrderFieldInfoView
from sales.views.order_history import OrderHistoryView, OrderHistoryFieldInfoView, OrderHistoryDetailView, \
    OrderHistorySelfView, OrderHistoryKarzinkaView, OrderHistoryDetailKarzinkaView
from sales.views.order_history_product import OrderHistoryProductView, OrderHistoryProductDetailView, \
    OrderHistoryProductFieldInfoView, OrderHistoryProductVozvratView
from sales.views.order_history_product_grouped import OrderHistoryProductByModelView
from sales.views.vozvrat_order import VozvratOrderView, VozvratOrderDetailView, VozvratOrderFieldInfoView

urlpatterns = [
    re_path(r'^client$', ClientView.as_view(), name='client_view'),
    path('client/<int:pk>', ClientDetailView.as_view(), name='client_detail_view'),
    path('client/fields', ClientFieldInfoView.as_view(), name='client_fields_info'),

    re_path(r'^client-keshbek-history$', ClientKeshbekHistoryView.as_view(), name='client_keshbek_history_view'),
    path('client-keshbek-history/<int:pk>', ClientKeshbekHistoryDetailView.as_view(),
         name='client_keshbek_history_detail_view'),
    path('client-keshbek-history/fields', ClientKeshbekHistoryFieldInfoView.as_view(),
         name='client_keshbek_history_fields_info'),

    re_path(r'^order$', OrderView.as_view(), name='order_view'),
    path('order/<int:pk>', OrderDetailView.as_view(), name='order_detail_view'),
    path('order/fields/', OrderFieldInfoView.as_view(), name='order_fields_info'),

    re_path(r'^order-history$', OrderHistoryView.as_view(), name='order_history_view'),
    path('order-history/self', OrderHistorySelfView.as_view(), name='order_history_self_view'),
    path('order-history/<int:pk>', OrderHistoryDetailView.as_view(), name='order_history_detail_view'),
    path('order-history/<int:pk>/product-by-model', OrderHistoryProductByModelView.as_view(), name='order_history_product_by_view'),
    path('order-history/fields', OrderHistoryFieldInfoView.as_view(), name='order_history_fields_info'),
    path('order-history/karzinka', OrderHistoryKarzinkaView.as_view(), name='order_history_karzinka_view'),
    path('order-history/karzinka/<int:pk>', OrderHistoryDetailKarzinkaView.as_view(), name='order_history_karzinka_detail_view'),

    re_path(r'^vozvrat-order$', VozvratOrderView.as_view(), name='vozvrat_order_view'),
    path('vozvrat-order/<int:pk>', VozvratOrderDetailView.as_view(), name='vozvrat_order_detail_view'),
    path('vozvrat-order/fields', VozvratOrderFieldInfoView.as_view(), name='vozvrat_order_fields_info'),

    re_path(r'^order-history-product$', OrderHistoryProductView.as_view(), name='order_history_product_view'),
    path('order-history-product/vozvrat', OrderHistoryProductVozvratView.as_view(),
         name='order_history_product_vozvrat_view'),
    path('order-history-product/<int:pk>', OrderHistoryProductDetailView.as_view(),
         name='order_history_product_detail_view'),
    path('order-history-product/fields', OrderHistoryProductFieldInfoView.as_view(),
         name='order_history_product_fields_info'),
]