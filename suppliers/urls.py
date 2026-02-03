from django.urls import re_path, path

from suppliers.views.purchase_invoice import PurchaseInvoiceView, PurchaseInvoiceDetailView, \
    PurchaseInvoiceFieldInfoView
from suppliers.views.supplier import SupplierView, SupplierDetailView, SupplierFieldInfoView
from suppliers.views.supplier_account import SupplierAccountView, SupplierAccountDetailView, \
    SupplierAccountFieldInfoView
from suppliers.views.supplier_debt_repayment import SupplierDebtRepaymentView, SupplierDebtRepaymentDetailView, \
    SupplierDebtRepaymentFieldInfoView

urlpatterns = [
    re_path(r'^supplier$', SupplierView.as_view(), name='supplier_view'),
    path('supplier/<int:pk>', SupplierDetailView.as_view(), name='supplier_detail_view'),
    path('supplier/fields', SupplierFieldInfoView.as_view(), name='supplier_fields_info'),

    re_path(r'^supplier-account$', SupplierAccountView.as_view(), name='supplier_account_view'),
    path('supplier-account/<int:pk>', SupplierAccountDetailView.as_view(), name='supplier_account_detail_view'),
    path('supplier-account/fields', SupplierAccountFieldInfoView.as_view(), name='supplier_account_fields_info'),

    re_path(r'^supplier-debt-repayment$', SupplierDebtRepaymentView.as_view(), name='supplier_debt_repayment_view'),
    path('supplier-debt-repayment/<int:pk>', SupplierDebtRepaymentDetailView.as_view(),
         name='supplier_debt_repayment_detail_view'),
    path('supplier-debt-repayment/fields', SupplierDebtRepaymentFieldInfoView.as_view(),
         name='supplier_debt_repayment_fields_info'),

    re_path(r'^purchase-invoice$', PurchaseInvoiceView.as_view(), name='purchase_invoice_view'),
    path('purchase-invoice/<int:pk>', PurchaseInvoiceDetailView.as_view(), name='purchase_invoice_detail_view'),
    path('purchase-invoice/fields', PurchaseInvoiceFieldInfoView.as_view(), name='purchase_invoice_fields_info'),
]