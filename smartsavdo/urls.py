from django.urls import re_path, path

from smartsavdo.views.faq import FAQView, FAQDetailView, FAQFieldInfoView, FAQViewList
from smartsavdo.views.product import ProductView, ProductDetailView, ProductFieldInfoView
from smartsavdo.views.product_image import ProductImageView, ProductImageDetailView, ProductImageFieldInfoView

urlpatterns = [
    re_path(r'^product$', ProductView.as_view(), name='product-view'),
    path('product/<int:pk>', ProductDetailView.as_view(), name='product-detail-view'),
    path('product/fields/', ProductFieldInfoView.as_view(), name='product-fields-info'),

    re_path(r'^product-image$', ProductImageView.as_view(), name='product-image-view'),
    path('product-image/<int:pk>', ProductImageDetailView.as_view(), name='product-image-detail-view'),
    path('product-image/fields/', ProductImageFieldInfoView.as_view(), name='product-image-fields-info'),

    # FAQ
    re_path(r'^faq$', FAQView.as_view(), name='faq-list'),
    path('faq/<int:pk>', FAQDetailView.as_view(), name='faq-detail'),
    path('faq/fields/', FAQFieldInfoView.as_view(), name='faq-fields'),
    path('faq/public', FAQViewList.as_view(), name='faq-public-info'),
]
