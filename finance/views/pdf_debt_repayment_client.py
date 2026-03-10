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
from finance.models import DebtRepayment
from finance.models import ExchangeRate  # app nomini kerak bo'lsa moslang


class DebtRepaymentPdfClientView(APIView):
    """
    GET /api/v1/pdf/debt-repayment/<id>/client

    DebtRepayment bo'yicha klient uchun PDF qaytaradi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        # DebtRepayment ni client va filial bilan birga olib kelamiz
        debt = get_object_or_404(
            DebtRepayment.objects.select_related(
                "client",
                "filial",
            ),
            pk=pk,
            is_delete=False,
        )

        # Memory ichida PDF yasash uchun buffer
        buffer = BytesIO()

        # PDF build
        self.build_pdf(buffer, debt)

        # Tayyor pdf byte ko'rinishda
        pdf = buffer.getvalue()
        buffer.close()

        # Response
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="debt_repayment_client.pdf"'
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
        4000 -> 4 000,00
        """
        value = self.d(value)
        formatted = f"{value:,.2f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", " ")
        return formatted

    def fmt_plain_number(self, value):
        """
        12200.00 -> 12200
        12200.50 -> 12 200,50
        """
        value = self.d(value)

        if value == value.to_integral():
            return str(int(value))

        formatted = f"{value:,.2f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", " ")
        return formatted

    def fmt_date(self, value):
        """
        2026-03-10 -> 2026-03-10
        screenshotga yaqin ko'rinish uchun iso format qoldirildi
        """
        if not value:
            return timezone.localdate().strftime("%Y-%m-%d")
        try:
            return value.strftime("%Y-%m-%d")
        except Exception:
            return str(value)

    def safe(self, value, default=""):
        """
        None yoki bo'sh string bo'lsa default qaytaradi.
        """
        if value is None:
            return default
        value = str(value).strip()
        return value if value else default

    def logo_path(self, filial):
        """
        Filial logo faylining fizik path ini topadi.
        """
        if not filial or not filial.logo:
            return None

        try:
            if hasattr(filial.logo, "path") and os.path.exists(filial.logo.path):
                return filial.logo.path
        except Exception:
            pass

        try:
            path = os.path.join(settings.MEDIA_ROOT, str(filial.logo))
            if os.path.exists(path):
                return path
        except Exception:
            pass

        return None

    def get_filial_exchange_rate(self, filial):
        """
        ExchangeRate jadvalidan filial bo'yicha birinchi aktiv kursni oladi.
        Topilmasa DebtRepayment.exchange_rate ishlatiladi.
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
        0 emasligini tekshiradi.
        """
        return self.d(value) != Decimal("0")

    # =========================================================
    # PDF BUILDER
    # =========================================================
    def build_pdf(self, buffer, debt):
        """
        DebtRepayment uchun PDF yasaydi.
        """
        # DejaVuSans ishlatmaymiz, standart fontlar
        base_font = "Helvetica"
        bold_font = "Helvetica-Bold"

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
            title="Debt repayment client PDF",
            author="Smart Savdo",
            subject="Debt repayment PDF",
        )

        styles = getSampleStyleSheet()

        # =========================
        # STYLE LAR
        # =========================
        style_title_date = ParagraphStyle(
            name="TitleDate",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=13,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=2,
        )

        style_client_name = ParagraphStyle(
            name="ClientName",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=11.5,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.red,
            spaceAfter=8,
        )

        style_section_title = ParagraphStyle(
            name="SectionTitle",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=8,
        )

        style_text = ParagraphStyle(
            name="Text",
            parent=styles["Normal"],
            fontName=base_font,
            fontSize=9.5,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.black,
        )

        style_text_bold = ParagraphStyle(
            name="TextBold",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=9.5,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.black,
        )

        style_green_text = ParagraphStyle(
            name="GreenText",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=10,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.green,
        )

        style_orange = ParagraphStyle(
            name="Orange",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=11,
            leading=13,
            alignment=TA_LEFT,
            textColor=colors.orange,
        )

        style_orange_right = ParagraphStyle(
            name="OrangeRight",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=11,
            leading=13,
            alignment=TA_RIGHT,
            textColor=colors.orange,
        )

        style_blue_right = ParagraphStyle(
            name="BlueRight",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=10.5,
            leading=12.5,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#3C49B0"),
        )

        style_red_big = ParagraphStyle(
            name="RedBig",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=16,
            leading=18,
            alignment=TA_RIGHT,
            textColor=colors.red,
        )

        story = []

        # =========================================================
        # HEADER MA'LUMOTLARI
        # =========================================================
        filial = debt.filial
        client = debt.client

        client_name = self.safe(getattr(client, "full_name", None), "-")
        exchange_rate_value = self.get_filial_exchange_rate(filial)

        # Agar ExchangeRate topilmasa DebtRepayment dagi kursni ishlatamiz
        if not self.is_non_zero(exchange_rate_value):
            exchange_rate_value = self.d(debt.exchange_rate)

        # Sana
        story.append(Paragraph(self.fmt_date(debt.date), style_title_date))

        # Klient ismi
        story.append(Paragraph(client_name, style_client_name))

        story.append(Spacer(1, 4 * mm))

        # =========================================================
        # LOGO + FILIAL INFO BLOKI
        # =========================================================
        logo_file_path = self.logo_path(filial)
        if logo_file_path:
            try:
                logo = Image(logo_file_path, width=28 * mm, height=24 * mm)
            except Exception:
                logo = Paragraph("LOGO", style_text_bold)
        else:
            logo = Paragraph("LOGO", style_text_bold)

        # Firma uchun screenshotdagi kabi filial name yoki fixed text ishlatish mumkin
        firma_text = self.safe(getattr(filial, "name", None), "-")

        # Manzil
        address_text = self.safe(getattr(filial, "address", None), "-")

        # Telefonlar
        filial_phone = self.safe(getattr(filial, "phone_number", None), "-")

        # Info qatorlari
        info_rows = [
            [
                Paragraph("Do'kon:", style_text_bold),
                Paragraph(self.safe(getattr(filial, "name", None), "-"), style_text_bold),

                Paragraph("Telefon nomer:", style_text_bold),
                Paragraph(filial_phone, style_text_bold),
            ],
            [
                Paragraph("Manzil:", style_text_bold),
                Paragraph(address_text, style_text_bold),

                Paragraph("Dollar kursi:", style_green_text),
                Paragraph(f"{self.fmt_plain_number(exchange_rate_value)} so'm", style_green_text),
            ],
        ]

        info_table = Table(
            info_rows,
            colWidths=[28 * mm, 47 * mm, 28 * mm, 52 * mm]
        )
        info_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))

        header_table = Table(
            [[logo, info_table]],
            colWidths=[32 * mm, 160 * mm]
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),

            # Yuqori va pastki chiziq
            ("LINEABOVE", (0, 0), (-1, 0), 0.6, colors.grey),
            ("LINEBELOW", (0, 0), (-1, 0), 0.0, colors.white),
        ]))

        # Headerdan keyin bo'sh joyni kamaytiramiz
        story.append(header_table)
        story.append(Spacer(1, 2 * mm))

        # Pastki chiziq
        line_table = Table([[""]], colWidths=[192 * mm])
        line_table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.6, colors.grey),

            # chiziq atrofidagi ortiqcha paddinglarni olib tashlaymiz
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(line_table)

        # Chiziq bilan sarlavha orasidagi joy ham kichikroq
        story.append(Spacer(1, 2 * mm))

        # =========================================================
        # SECTION TITLE
        # =========================================================
        story.append(Paragraph("To'langan qarz hisobi:", style_section_title))
        story.append(Spacer(1, 1 * mm))

        # =========================================================
        # TOTALS BLOKI
        # =========================================================
        old_total_debt_client = self.d(debt.old_total_debt_client)
        total_paid = self.d(debt.summa_total_dollar)
        total_debt = self.d(debt.total_debt_client)

        discount_amount = self.d(debt.discount_amount)

        # Chap blok
        left_rows = [
            [
                Paragraph("Ostatka ($):", style_orange),
                Paragraph(f"{self.fmt_money(old_total_debt_client)} $,", style_orange_right),
            ],
            [
                Paragraph("Jami to'langan summa ($):", style_orange),
                Paragraph(f"{self.fmt_money(total_paid)} $,", style_orange_right),
            ],
        ]

        # Chegirma 0 bo'lmasa chiqadi
        if self.is_non_zero(discount_amount):
            left_rows.append([
                Paragraph("Chegirma ($):", style_orange),
                Paragraph(f"{self.fmt_money(discount_amount)} $,", style_orange_right),
            ])

        left_rows.append([
            Paragraph("Qolgan qarz ($):", style_orange),
            Paragraph(f"{self.fmt_money(total_debt)} $,", style_red_big),
        ])

        left_block = Table(
            left_rows,
            colWidths=[58 * mm, 38 * mm]
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

        # O'ng blok
        paid_dollar = self.d(debt.summa_dollar)
        paid_naqt = self.d(debt.summa_naqt)
        paid_kilik = self.d(debt.summa_kilik)
        paid_terminal = self.d(debt.summa_terminal)
        paid_transfer = self.d(debt.summa_transfer)

        right_rows = []

        if self.is_non_zero(paid_dollar):
            right_rows.append([
                Paragraph("To'langan summa dollarda ($):", style_blue_right),
                Paragraph(f"{self.fmt_money(paid_dollar)} $", style_blue_right),
            ])

        if self.is_non_zero(paid_naqt):
            right_rows.append([
                Paragraph("To'langan summa naqt:", style_blue_right),
                Paragraph(self.fmt_money(paid_naqt), style_blue_right),
            ])

        if self.is_non_zero(paid_kilik):
            right_rows.append([
                Paragraph("To'langan summa kilik:", style_blue_right),
                Paragraph(self.fmt_money(paid_kilik), style_blue_right),
            ])

        if self.is_non_zero(paid_terminal):
            right_rows.append([
                Paragraph("To'langan summa terminal:", style_blue_right),
                Paragraph(self.fmt_money(paid_terminal), style_blue_right),
            ])

        if self.is_non_zero(paid_transfer):
            right_rows.append([
                Paragraph("To'langan summa transfer:", style_blue_right),
                Paragraph(self.fmt_money(paid_transfer), style_blue_right),
            ])

        if right_rows:
            right_block = Table(
                right_rows,
                colWidths=[56 * mm, 30 * mm]
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
            colWidths=[96 * mm, 96 * mm]
        )
        totals_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        story.append(totals_table)

        # =========================================================
        # PDF META
        # =========================================================
        def add_pdf_meta(canvas, doc):
            canvas.setTitle("Debt repayment client PDF")
            canvas.setAuthor("Smart Savdo")
            canvas.setSubject("Debt repayment PDF")
            canvas.setCreator("Smart Savdo")
            canvas.setKeywords("debt,repayment,pdf")

        doc.build(
            story,
            onFirstPage=add_pdf_meta,
            onLaterPages=add_pdf_meta,
        )