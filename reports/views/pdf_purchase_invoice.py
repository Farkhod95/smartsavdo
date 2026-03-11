from decimal import Decimal
from io import BytesIO

from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Paragraph,
)

from suppliers.models import PurchaseInvoice
from inventory.models import ProductHistory


class PurchaseInvoicePdfView(APIView):
    permission_classes = [IsAuthenticated]

    def _d(self, value):
        try:
            return Decimal(str(value or 0))
        except Exception:
            return Decimal("0")

    def _is_positive(self, value) -> bool:
        return self._d(value) > 0

    def _fmt_money(self, value, suffix=""):
        value = self._d(value)
        formatted = f"{value:,.2f}".replace(",", " ")
        return f"{formatted}{suffix}"

    def _fmt_int(self, value):
        try:
            return str(int(value or 0))
        except Exception:
            return "0"

    def _safe(self, value, default="-"):
        if value is None:
            return default
        value = str(value).strip()
        return value if value else default

    def _purchase_type_display(self, invoice: PurchaseInvoice):
        try:
            return invoice.get_type_display()
        except Exception:
            return self._safe(invoice.type)

    def _is_internal(self, invoice: PurchaseInvoice) -> bool:
        return (invoice.type or "").lower() == PurchaseInvoice.TYPE.INTERNAL

    def get_invoice(self, pk):
        invoice = (
            PurchaseInvoice.objects.select_related(
                "employee",
                "supplier",
                "sklad",
                "sklad_outgoing",
                "filial",
                "created_by",
                "updated_by",
            )
            .filter(pk=pk)
            .first()
        )
        if not invoice:
            raise Http404("PurchaseInvoice topilmadi.")
        return invoice

    def get_histories(self, invoice: PurchaseInvoice):
        return (
            ProductHistory.objects.select_related(
                "product",
                "filial",
                "sklad",
                "purchase_invoice",
                "branch",
                "branch_category",
                "model",
                "type",
                "size",
                "size__unit",
            )
            .filter(purchase_invoice_id=invoice.pk)
            .order_by("id")
        )

    def build_pdf(self, invoice: PurchaseInvoice, histories):
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
            title=f"Kirim ma'lumoti",
        )

        styles = getSampleStyleSheet()
        is_internal = self._is_internal(invoice)

        title_style = ParagraphStyle(
            "title_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=1,
        )

        type_style = ParagraphStyle(
            "type_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#16a34a"),
            spaceAfter=6,
        )

        info_label_style = ParagraphStyle(
            "info_label_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.black,
        )

        info_value_style = ParagraphStyle(
            "info_value_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.black,
        )

        table_header_style = ParagraphStyle(
            "table_header_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.black,
        )

        table_cell_style = ParagraphStyle(
            "table_cell_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            alignment=TA_LEFT,
            textColor=colors.black,
        )

        table_cell_center_style = ParagraphStyle(
            "table_cell_center_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.black,
        )

        orange_label_style = ParagraphStyle(
            "orange_label_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#f59e0b"),
        )

        orange_value_style = ParagraphStyle(
            "orange_value_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#f59e0b"),
        )

        blue_label_style = ParagraphStyle(
            "blue_label_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#3346cc"),
        )

        blue_value_style = ParagraphStyle(
            "blue_value_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#3346cc"),
        )

        red_total_label_style = ParagraphStyle(
            "red_total_label_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#ff0000"),
        )

        red_total_value_style = ParagraphStyle(
            "red_total_value_style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=17,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#ff0000"),
        )

        story = []

        # ===== HEADER =====
        created_dt = invoice.created_time
        created_str = timezone.localtime(created_dt).strftime("%d.%m.%Y") if created_dt else "-"
        type_str = self._purchase_type_display(invoice)

        story.append(Paragraph(created_str, title_style))
        story.append(Paragraph(f"({self._safe(type_str)})", type_style))
        story.append(Spacer(1, 6))

        # ===== TOP INFO =====
        top_info_data = [
            [
                Paragraph("Ombordan:", info_label_style),
                Paragraph(self._safe(getattr(invoice.sklad_outgoing, "name", None)), info_value_style),
                Paragraph("Omborga:", info_label_style),
                Paragraph(self._safe(getattr(invoice.sklad, "name", None)), info_value_style),
            ],
            [
                Paragraph("Xodim:", info_label_style),
                Paragraph(self._safe(getattr(invoice.employee, "full_name", None)), info_value_style),
                Paragraph("Mahsulotlar:", info_label_style),
                Paragraph(self._fmt_int(invoice.product_count), info_value_style),
            ],
        ]

        top_info_table = Table(
            top_info_data,
            colWidths=[28 * mm, 58 * mm, 28 * mm, 58 * mm],
            hAlign="LEFT",
        )
        top_info_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(top_info_table)
        story.append(Spacer(1, 10))

        # ===== PRODUCTS TABLE =====
        calculated_total = Decimal("0")
        count_total = 0

        if is_internal:
            table_data = [
                [
                    Paragraph("T/r", table_header_style),
                    Paragraph("MODEL", table_header_style),
                    Paragraph("NOMI", table_header_style),
                    Paragraph("SONI", table_header_style),
                    Paragraph("TIP", table_header_style),
                    Paragraph("Tasdiqlash", table_header_style),
                ]
            ]

            for idx, item in enumerate(histories, start=1):
                model_name = self._safe(getattr(item.model, "name", None))
                type_name = self._safe(getattr(item.type, "name", None))
                size_value = getattr(item.size, "size", None)

                if size_value not in (None, ""):
                    product_name = f"{type_name} ({size_value})"
                else:
                    product_name = type_name

                count = int(item.count or 0)
                count_total += count

                real_price = self._d(item.real_price)
                row_total = self._d(count) * real_price
                calculated_total += row_total

                tip_text = "-"
                if getattr(item, "size", None) and getattr(item.size, "unit", None):
                    tip_text = self._safe(
                        getattr(item.size.unit, "name", None) or getattr(item.size.unit, "code", None)
                    )

                table_data.append(
                    [
                        Paragraph(str(idx), table_cell_center_style),
                        Paragraph(model_name, table_cell_style),
                        Paragraph(product_name, table_cell_style),
                        Paragraph(str(count), table_cell_center_style),
                        Paragraph(tip_text, table_cell_center_style),
                        Paragraph("", table_cell_center_style),
                    ]
                )

            table_data.append(
                [
                    Paragraph("Jami", table_cell_style),
                    "",
                    "",
                    Paragraph(str(count_total), table_cell_center_style),
                    "",
                    "",
                ]
            )

            products_table = Table(
                table_data,
                colWidths=[10 * mm, 34 * mm, 50 * mm, 16 * mm, 18 * mm, 32 * mm],
                repeatRows=1,
                hAlign="LEFT",
            )
            products_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                        ("SPAN", (0, -1), (2, -1)),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ]
                )
            )

        else:
            table_data = [
                [
                    Paragraph("T/r", table_header_style),
                    Paragraph("MODEL", table_header_style),
                    Paragraph("NOMI", table_header_style),
                    Paragraph("SONI", table_header_style),
                    Paragraph("TIP", table_header_style),
                    Paragraph("NARXI ($)", table_header_style),
                    Paragraph("UMUMIY NARXI ($)", table_header_style),
                ]
            ]

            for idx, item in enumerate(histories, start=1):
                model_name = self._safe(getattr(item.model, "name", None))
                type_name = self._safe(getattr(item.type, "name", None))
                size_value = getattr(item.size, "size", None)

                if size_value not in (None, ""):
                    product_name = f"{type_name} ({size_value})"
                else:
                    product_name = type_name

                count = int(item.count or 0)
                count_total += count

                real_price = self._d(item.real_price)
                row_total = self._d(count) * real_price
                calculated_total += row_total

                tip_text = "-"
                if getattr(item, "size", None) and getattr(item.size, "unit", None):
                    tip_text = self._safe(
                        getattr(item.size.unit, "name", None) or getattr(item.size.unit, "code", None)
                    )

                table_data.append(
                    [
                        Paragraph(str(idx), table_cell_center_style),
                        Paragraph(model_name, table_cell_style),
                        Paragraph(product_name, table_cell_style),
                        Paragraph(str(count), table_cell_center_style),
                        Paragraph(tip_text, table_cell_center_style),
                        Paragraph(self._fmt_money(real_price), table_cell_center_style),
                        Paragraph(self._fmt_money(row_total), table_cell_center_style),
                    ]
                )

            jami_value = self._d(invoice.all_product_summa) if self._d(invoice.all_product_summa) > 0 else calculated_total

            table_data.append(
                [
                    Paragraph("Jami", table_cell_style),
                    "",
                    "",
                    Paragraph(str(count_total), table_cell_center_style),
                    "",
                    Paragraph("-", table_cell_center_style),
                    Paragraph(self._fmt_money(jami_value), table_cell_center_style),
                ]
            )

            products_table = Table(
                table_data,
                colWidths=[10 * mm, 34 * mm, 45 * mm, 16 * mm, 18 * mm, 22 * mm, 28 * mm],
                repeatRows=1,
                hAlign="LEFT",
            )
            products_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                        ("SPAN", (0, -1), (2, -1)),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ]
                )
            )

        story.append(products_table)
        story.append(Spacer(1, 12))

        # ===== SUMMARY =====
        if not is_internal:
            left_summary = [
                [
                    Paragraph("Ostatka ($):", orange_label_style),
                    Paragraph(self._fmt_money(invoice.total_debt_old, " $"), orange_value_style),
                ],
                [
                    Paragraph("Olingan tavarlar summasi ($):", orange_label_style),
                    Paragraph(self._fmt_money(invoice.all_product_summa, " $"), orange_value_style),
                ],
                [
                    Paragraph("Jami to'langan summa ($):", orange_label_style),
                    Paragraph(self._fmt_money(invoice.given_summa_total_dollar, " $"), orange_value_style),
                ],
                [
                    Paragraph("Qolgan qarz ($):", red_total_label_style),
                    Paragraph(self._fmt_money(invoice.total_debt, " $"), red_total_value_style),
                ],
            ]

            right_summary = []

            if self._is_positive(invoice.given_summa_dollar):
                right_summary.append(
                    [
                        Paragraph("Berilgan summa ($):", blue_label_style),
                        Paragraph(self._fmt_money(invoice.given_summa_dollar, " $"), blue_value_style),
                    ]
                )

            if self._is_positive(invoice.given_summa_naqt):
                right_summary.append(
                    [
                        Paragraph("Berilgan summa naqt:", blue_label_style),
                        Paragraph(self._fmt_money(invoice.given_summa_naqt), blue_value_style),
                    ]
                )

            if self._is_positive(invoice.given_summa_kilik):
                right_summary.append(
                    [
                        Paragraph("Berilgan summa kilik:", blue_label_style),
                        Paragraph(self._fmt_money(invoice.given_summa_kilik), blue_value_style),
                    ]
                )

            if self._is_positive(invoice.given_summa_terminal):
                right_summary.append(
                    [
                        Paragraph("Berilgan summa terminal:", blue_label_style),
                        Paragraph(self._fmt_money(invoice.given_summa_terminal), blue_value_style),
                    ]
                )

            if self._is_positive(invoice.given_summa_transfer):
                right_summary.append(
                    [
                        Paragraph("Berilgan summa transfer:", blue_label_style),
                        Paragraph(self._fmt_money(invoice.given_summa_transfer), blue_value_style),
                    ]
                )

            left_table = Table(
                left_summary,
                colWidths=[55 * mm, 34 * mm],
                hAlign="LEFT",
            )
            left_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (0, -1), "LEFT"),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 3), (-1, 3), 6),
                        ("BOTTOMPADDING", (0, 3), (-1, 3), 6),
                    ]
                )
            )

            if right_summary:
                right_table = Table(
                    right_summary,
                    colWidths=[50 * mm, 30 * mm],
                    hAlign="LEFT",
                )
                right_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("ALIGN", (0, 0), (0, -1), "LEFT"),
                            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )

                summary_table = Table(
                    [[left_table, "", right_table]],
                    colWidths=[82 * mm, 10 * mm, 82 * mm],
                    hAlign="LEFT",
                )
                summary_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ]
                    )
                )
                story.append(summary_table)
            else:
                story.append(left_table)

        doc.build(story)
        buffer.seek(0)
        return buffer

    def get(self, request, pk):
        invoice = self.get_invoice(pk)
        histories = self.get_histories(invoice)
        pdf_buffer = self.build_pdf(invoice, histories)

        filename = f"purchase_invoice_{invoice.pk}.pdf"
        return FileResponse(
            pdf_buffer,
            as_attachment=False,
            filename=filename,
            content_type="application/pdf",
        )