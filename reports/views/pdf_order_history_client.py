from io import BytesIO
from decimal import Decimal, InvalidOperation
import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

# ReportLab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

# Modellar
from sales.models import OrderHistory, OrderHistoryProduct
from finance.models import ExchangeRate


class OrderHistoryInvoicePdfView(APIView):
    """
    GET /api/v1/pdf/order-history/<id>/client/

    Berilgan OrderHistory bo'yicha PDF invoice qaytaradi.
    DejaVuSans ishlatilmaydi, standart Helvetica ishlatiladi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        # OrderHistory ni client va filial bilan birga olib kelamiz
        order_history = get_object_or_404(
            OrderHistory.objects.select_related(
                "client",
                "order_filial",
            ),
            pk=pk,
            is_delete=False,
        )

        # PDF ni memory ichida yasash uchun buffer
        buffer = BytesIO()

        # PDF build
        self.build_pdf(buffer, order_history)

        # Byte ko'rinishga o'tkazamiz
        pdf = buffer.getvalue()
        buffer.close()

        # Response qaytaramiz
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="mijoz_buyurtmasi.pdf"'
        return response

    # =========================================================
    # HELPERS
    # =========================================================
    def d(self, value):
        """
        Qiymatni xavfsiz Decimal ga aylantiradi.
        """
        try:
            return Decimal(str(value or 0))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")

    def fmt_money(self, value):
        """
        4000 -> 4 000,00 ko'rinishiga o'tkazadi
        """
        value = self.d(value)
        formatted = f"{value:,.2f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", " ")
        return formatted

    def fmt_plain_number(self, value):
        """
        3805.00 -> 3805
        3805.50 -> 3 805,50
        """
        value = self.d(value)

        if value == value.to_integral():
            return str(int(value))

        formatted = f"{value:,.2f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", " ")
        return formatted

    def fmt_date(self, value):
        """
        Sana formatlash: 10.03.2026
        """
        if not value:
            return timezone.localdate().strftime("%d.%m.%Y")
        return value.strftime("%d.%m.%Y")

    def safe(self, value, default=""):
        """
        None yoki bo'sh qiymat bo'lsa default qaytaradi.
        """
        if value is None:
            return default
        value = str(value).strip()
        return value if value else default

    def logo_path(self, filial):
        """
        Filial logosining fizik yo'lini topadi.
        """
        if not filial or not filial.logo:
            return None

        # 1-usul: ImageField.path
        try:
            if hasattr(filial.logo, "path") and os.path.exists(filial.logo.path):
                return filial.logo.path
        except Exception:
            pass

        # 2-usul: MEDIA_ROOT bilan yasash
        try:
            path = os.path.join(settings.MEDIA_ROOT, str(filial.logo))
            if os.path.exists(path):
                return path
        except Exception:
            pass

        return None

    def size_to_str(self, size_value):
        """
        8.0 -> 8
        4.5 -> 4.5
        """
        if size_value is None:
            return ""

        try:
            f = float(size_value)
            if f.is_integer():
                return str(int(f))
            return str(size_value)
        except Exception:
            return str(size_value)

    def get_filial_exchange_rate(self, filial):
        """
        ExchangeRate dan filial bo'yicha birinchi aktiv kursni oladi.
        Topilmasa 0 qaytaradi.
        """
        if not filial or not filial.id:
            return Decimal("0")

        exchange = (
            ExchangeRate.objects
            .filter(filial_id=filial.id, is_active=True)
            .first()
        )

        if not exchange:
            return Decimal("0")

        return self.d(exchange.dollar)

    def is_non_zero(self, value):
        """
        Qiymat 0 emasligini tekshiradi.
        """
        return self.d(value) != Decimal("0")

    # =========================================================
    # PDF BUILDER
    # =========================================================
    def build_pdf(self, buffer, order_history):
        """
        PDF ni to'liq yasovchi metod.
        """
        # Bu yerda standart ReportLab font ishlatiladi
        base_font = "Helvetica"
        bold_font = "Helvetica-Bold"

        # Asosiy document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
            title="Mijoz buyurtmasi",
            author="Smart Savdo",
            subject="Mijoz buyurtmasi PDF",
        )

        styles = getSampleStyleSheet()

        # =========================
        # STYLE LAR
        # =========================
        style_title_date = ParagraphStyle(
            name="TitleDate",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=14,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=2,
        )

        style_client_line = ParagraphStyle(
            name="ClientLine",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=11.5,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=6,
        )

        style_text = ParagraphStyle(
            name="Text",
            parent=styles["Normal"],
            fontName=base_font,
            fontSize=9.5,
            leading=10.5,
            alignment=TA_LEFT,
            textColor=colors.black,
        )

        style_text_bold = ParagraphStyle(
            name="TextBold",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9.5,
            leading=10.5,
            alignment=TA_LEFT,
            textColor=colors.black,
        )

        style_text_dollar_kurs = ParagraphStyle(
            name="TextDollarKurs",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9.5,
            leading=10.5,
            alignment=TA_LEFT,
            textColor=colors.green,
        )

        style_center = ParagraphStyle(
            name="Center",
            parent=styles["Normal"],
            fontName=base_font,
            fontSize=8.8,
            leading=10.5,
            alignment=TA_CENTER,
            textColor=colors.black,
        )

        style_center_bold = ParagraphStyle(
            name="CenterBold",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=8.8,
            leading=10.5,
            alignment=TA_CENTER,
            textColor=colors.black,
        )

        style_orange = ParagraphStyle(
            name="Orange",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9.5,
            leading=11.5,
            alignment=TA_LEFT,
            textColor=colors.orange,
        )

        style_orange_right = ParagraphStyle(
            name="OrangeRight",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9.5,
            leading=11.5,
            alignment=TA_RIGHT,
            textColor=colors.orange,
        )

        style_blue_right = ParagraphStyle(
            name="BlueRight",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9.5,
            leading=11.5,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#3C49B0"),
        )

        style_red_big = ParagraphStyle(
            name="RedBig",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=12.8,
            leading=14.5,
            alignment=TA_RIGHT,
            textColor=colors.red,
        )

        # Story
        story = []

        # =========================================================
        # CLIENT INFO
        # =========================================================
        client_name = self.safe(getattr(order_history.client, "full_name", None), "-")
        client_phone = self.safe(getattr(order_history.client, "phone_number", None), "")
        filial = order_history.order_filial

        # Dollar kursi ExchangeRate dan olinadi
        exchange_rate_value = self.get_filial_exchange_rate(filial)

        # Fullname + phone bitta qatorda
        if client_phone:
            client_line = (
                f'<font color="red"><b>{client_name}</b></font> '
                f'<font color="black"><b>({client_phone})</b></font>'
            )
        else:
            client_line = f'<font color="red"><b>{client_name}</b></font>'

        # =========================================================
        # TOP TITLE
        # =========================================================
        story.append(
            Paragraph(f"{self.fmt_date(order_history.date)}", style_title_date)
        )
        story.append(
            Paragraph(client_line, style_client_line)
        )
        story.append(Spacer(1, 2 * mm))

        # =========================================================
        # HEADER: LOGO + FILIAL INFO
        # =========================================================
        logo_file_path = self.logo_path(filial)
        if logo_file_path:
            try:
                logo = Image(logo_file_path, width=30 * mm, height=24 * mm)
            except Exception:
                logo = Paragraph("LOGO", style_center_bold)
        else:
            logo = Paragraph("LOGO", style_center_bold)

        # O'ng tarafdagi info jadvali
        info_rows = [
            [
                Paragraph("Do'kon:", style_text_bold),
                Paragraph(self.safe(getattr(filial, "name", None), "-"), style_text_bold),
                Paragraph("Telefon nomer1:", style_text_bold),
                Paragraph(self.safe(getattr(filial, "phone_number", None), "-"), style_text_bold),
            ],
            [
                Paragraph("Manzil:", style_text_bold),
                Paragraph(self.safe(getattr(filial, "address", None), "-"), style_text_bold),
                Paragraph("Dollar kursi:", style_text_dollar_kurs),
                Paragraph(self.fmt_plain_number(exchange_rate_value), style_text_dollar_kurs),
            ],
        ]

        info_table = Table(
            info_rows,
            colWidths=[22 * mm, 62 * mm, 34 * mm, 44 * mm]
        )
        info_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("FONTNAME", (0, 0), (-1, -1), base_font),
        ]))

        # Logo chapda, info o'ngda
        header_table = Table(
            [[logo, info_table]],
            colWidths=[36 * mm, 146 * mm]
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEABOVE", (0, 0), (-1, 0), 0.6, colors.grey),
        ]))

        story.append(header_table)
        story.append(Spacer(1, 7 * mm))

        # =========================================================
        # PRODUCTS TABLE
        # =========================================================
        items = (
            OrderHistoryProduct.objects
            .filter(order_history=order_history, is_delete=False)
            .select_related(
                "model",
                "type",
                "size",
                "size__unit",
            )
            .order_by("id")
        )

        table_data = [
            [
                Paragraph("T/r", style_center_bold),
                Paragraph("MODEL", style_center_bold),
                Paragraph("NOMI", style_center_bold),
                Paragraph("SONI", style_center_bold),
                Paragraph("TIP", style_center_bold),
                Paragraph("NARXI ($)", style_center_bold),
                Paragraph("UMUMIY<br/>NARXI ($)", style_center_bold),
            ]
        ]

        calc_total = Decimal("0")

        # Har bir mahsulotni jadvalga qo'shamiz
        for i, item in enumerate(items, start=1):
            model_name = self.safe(getattr(item.model, "name", None), "-")
            type_name = self.safe(getattr(item.type, "name", None), "-")
            size_value = getattr(item.size, "size", None)
            size_str = self.size_to_str(size_value)
            unit_name = self.safe(getattr(getattr(item.size, "unit", None), "name", None), "-")

            if size_str:
                nomi = f"{type_name} ( {size_str} )"
            else:
                nomi = type_name

            count = item.count or 0
            price = self.d(item.price_dollar)
            line_total = price * Decimal(count)
            calc_total += line_total

            table_data.append([
                Paragraph(str(i), style_center_bold),
                Paragraph(model_name, style_text_bold),
                Paragraph(nomi, style_text_bold),
                Paragraph(str(count), style_center_bold),
                Paragraph(unit_name, style_center_bold),
                Paragraph(self.fmt_plain_number(price), style_center_bold),
                Paragraph(f"= {self.fmt_plain_number(line_total)}", style_text_bold),
            ])

        total_for_footer = self.d(order_history.all_product_summa or calc_total)

        # Jami qatori
        table_data.append([
            Paragraph("Jami", style_text_bold),
            "",
            "",
            "",
            "",
            Paragraph("-", style_center_bold),
            Paragraph(self.fmt_plain_number(total_for_footer), style_center_bold),
        ])

        col_widths = [
            8 * mm,    # №
            40 * mm,   # MODEL
            58 * mm,   # NOMI
            17 * mm,   # SONI
            20 * mm,   # TIP
            20 * mm,   # NARXI
            28 * mm,   # UMUMIY
        ]

        products_table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1
        )
        products_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.1, colors.black),
            ("GRID", (0, 0), (-1, -1), 0.7, colors.black),

            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),

            ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 1), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 2),

            ("ALIGN", (0, 1), (0, -2), "CENTER"),
            ("ALIGN", (1, 1), (2, -2), "LEFT"),
            ("ALIGN", (3, 1), (5, -2), "CENTER"),
            ("ALIGN", (6, 1), (6, -2), "LEFT"),

            ("SPAN", (0, -1), (4, -1)),
            ("ALIGN", (0, -1), (0, -1), "LEFT"),
            ("ALIGN", (5, -1), (6, -1), "CENTER"),

            ("FONTNAME", (0, 0), (-1, -1), base_font),
            ("TOPPADDING", (0, -1), (-1, -1), 2),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 2),
        ]))

        # =========================================================
        # TOTALS
        # =========================================================
        all_product_summa = self.d(order_history.all_product_summa)
        total_paid = self.d(order_history.summa_total_dollar)
        discount_amount = self.d(order_history.discount_amount)
        total_debt = self.d(order_history.total_debt_client)
        today_debt = self.d(order_history.total_debt_today_client)

        # Chap blok qatorlari
        left_rows = [
            [
                Paragraph("Ostatka ($):", style_orange),
                Paragraph(f"{self.fmt_money(today_debt)} $", style_orange_right),
            ],
            [
                Paragraph("Olingan tavarlar summasi ($):", style_orange),
                Paragraph(f"{self.fmt_money(all_product_summa)} $", style_orange_right),
            ],
            [
                Paragraph("Jami to'langan summa ($):", style_orange),
                Paragraph(f"{self.fmt_money(total_paid)} $", style_orange_right),
            ],
        ]

        # Chegirma 0 bo'lmasa chiqadi
        if self.is_non_zero(discount_amount):
            left_rows.append([
                Paragraph("Chegirma ($):", style_orange),
                Paragraph(f"{self.fmt_money(discount_amount)} $", style_orange_right),
            ])

        # Qolgan qarz doim chiqadi
        left_rows.append([
            Paragraph("Qolgan qarz ($):", style_orange),
            Paragraph(f"{self.fmt_money(total_debt)} $", style_red_big),
        ])

        left_block = Table(
            left_rows,
            colWidths=[48 * mm, 33 * mm]
        )
        left_block.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        # O'ng blok qatorlari
        paid_dollar = self.d(order_history.summa_dollar)
        paid_naqt = self.d(order_history.summa_naqt)
        paid_kilik = self.d(order_history.summa_kilik)
        paid_terminal = self.d(order_history.summa_terminal)
        paid_transfer = self.d(order_history.summa_transfer)

        right_rows = []

        if self.is_non_zero(paid_dollar):
            right_rows.append([
                Paragraph("To'langan summa ($):", style_blue_right),
                Paragraph(f"{self.fmt_money(paid_dollar)} $", style_blue_right),
            ])

        if self.is_non_zero(paid_naqt):
            right_rows.append([
                Paragraph("To'langan summa naqt:", style_blue_right),
                Paragraph(f"{self.fmt_money(paid_naqt)}", style_blue_right),
            ])

        if self.is_non_zero(paid_kilik):
            right_rows.append([
                Paragraph("To'langan summa kilik:", style_blue_right),
                Paragraph(f"{self.fmt_money(paid_kilik)}", style_blue_right),
            ])

        if self.is_non_zero(paid_terminal):
            right_rows.append([
                Paragraph("To'langan summa terminal:", style_blue_right),
                Paragraph(f"{self.fmt_money(paid_terminal)}", style_blue_right),
            ])

        if self.is_non_zero(paid_transfer):
            right_rows.append([
                Paragraph("To'langan summa transfer:", style_blue_right),
                Paragraph(f"{self.fmt_money(paid_transfer)}", style_blue_right),
            ])

        if right_rows:
            right_block = Table(
                right_rows,
                colWidths=[45 * mm, 28 * mm]
            )
            right_block.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
        else:
            right_block = Paragraph("", style_blue_right)

        totals_table = Table(
            [[left_block, right_block]],
            colWidths=[83 * mm, 92 * mm]
        )
        totals_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        # Jadval + totals ni bir blok qilamiz
        combined_block = Table(
            [
                [products_table],
                [Spacer(1, 6 * mm)],   # <-- shu joy jadval bilan pastki text orasini ochadi
                [totals_table],
            ],
            colWidths=[191 * mm]
        )
        combined_block.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        story.append(combined_block)

        # =========================================================
        # PDF META
        # =========================================================
        def add_pdf_meta(canvas, doc):
            canvas.setTitle("Mijoz buyurtmasi")
            canvas.setAuthor("Smart Savdo")
            canvas.setSubject("Mijoz buyurtmasi PDF")
            canvas.setCreator("Smart Savdo")
            canvas.setKeywords("mijoz,buyurtma,pdf,invoice")

        doc.build(
            story,
            onFirstPage=add_pdf_meta,
            onLaterPages=add_pdf_meta,
        )