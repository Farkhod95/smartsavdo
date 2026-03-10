from io import BytesIO
from decimal import Decimal, InvalidOperation

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
)

# Modellar
from sales.models import OrderHistory, OrderHistoryProduct


class OrderHistoryInvoicePdfWorkerView(APIView):
    """
    GET /api/v1/pdf/order-history/<id>/worker

    Ombor/ishchi uchun alohida PDF qaytaradi.
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

        # Memory ichida PDF yasash uchun buffer
        buffer = BytesIO()

        # PDF build
        self.build_pdf(buffer, order_history)

        # Byte ko‘rinishidagi PDF
        pdf = buffer.getvalue()
        buffer.close()

        # Response
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="buyurtma_hodim_uchun.pdf"'
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

    def safe(self, value, default=""):
        """
        None yoki bo'sh qiymat bo'lsa default qaytaradi.
        """
        if value is None:
            return default
        value = str(value).strip()
        return value if value else default

    def fmt_datetime(self, order_history):
        """
        Buyurtma sanasi uchun:
        10.03.2026 09:00

        Agar created_time bo'lsa o'shani ishlatadi,
        bo'lmasa date field dan 00:00 qiladi.
        """
        created_time = getattr(order_history, "created_time", None)
        if created_time:
            try:
                local_dt = timezone.localtime(created_time)
                return local_dt.strftime("%d.%m.%Y %H:%M")
            except Exception:
                pass

        order_date = getattr(order_history, "date", None)
        if order_date:
            try:
                return order_date.strftime("%d.%m.%Y") + " 00:00"
            except Exception:
                return str(order_date)

        return timezone.localtime().strftime("%d.%m.%Y %H:%M")

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

    # =========================================================
    # PDF BUILDER
    # =========================================================
    def build_pdf(self, buffer, order_history):
        """
        Worker uchun PDF yasaydi.
        """
        base_font = "Helvetica"
        bold_font = "Helvetica-Bold"

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title="Hodim uchun",
            author="Smart Savdo",
            subject="Worker order PDF",
        )

        styles = getSampleStyleSheet()

        # =========================
        # STYLE LAR
        # =========================
        style_center_black = ParagraphStyle(
            name="CenterBlack",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.black,
        )

        style_center_red = ParagraphStyle(
            name="CenterRed",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.red,
        )

        style_center_black_big = ParagraphStyle(
            name="CenterBlackBig",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=12,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.black,
        )

        style_left = ParagraphStyle(
            name="Left",
            parent=styles["Normal"],
            fontName=base_font,
            fontSize=9.5,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.black,
        )

        style_left_bold = ParagraphStyle(
            name="LeftBold",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=11,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.black,
        )

        style_center_table = ParagraphStyle(
            name="CenterTable",
            parent=styles["Normal"],
            fontName=bold_font,
            fontSize=8.8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.black,
        )

        story = []

        # =========================================================
        # TOP INFO
        # =========================================================
        client_name = self.safe(getattr(order_history.client, "full_name", None), "-")
        client_phone = self.safe(getattr(order_history.client, "phone_number", None), "-")
        order_datetime = self.fmt_datetime(order_history)

        # 1-qator: Buyurtma sanasi
        buyurtma_line = (
            f'<font color="black"><b>Buyurtma sanasi:</b></font> '
            f'<font color="red"><b>{order_datetime}</b></font>'
        )
        story.append(Paragraph(buyurtma_line, style_center_black_big))

        # 2-qator: Mijoz
        mijoz_line = (
            f'<font color="black"><b>Mijoz:</b></font> '
            f'<font color="red"><b>{client_name}</b></font>'
        )
        story.append(Paragraph(mijoz_line, style_center_black_big))

        # 3-qator: Mijoz telefon raqami
        tel_line = (
            f'<font color="black"><b>Mijoz telefon raqami:</b></font> '
            f'<font color="black"><b>{client_phone}</b></font>'
        )
        story.append(Paragraph(tel_line, style_center_black_big))

        story.append(Spacer(1, 8 * mm))

        # =========================================================
        # TABLE DATA
        # =========================================================
        items = (
            OrderHistoryProduct.objects
            .filter(order_history=order_history, is_delete=False)
            .select_related(
                "model",
                "type",
                "size",
                "size__unit",
                "sklad",
            )
            .order_by("id")
        )

        # Header
        table_data = [
            [
                Paragraph("JOY", style_center_table),
                Paragraph("MODEL", style_center_table),
                Paragraph("NOMI", style_center_table),
                Paragraph("TIP", style_center_table),
                Paragraph("SONI", style_center_table),
            ]
        ]

        total_count = 0

        for item in items:
            # JOY
            joy_name = "Ombor"
            if getattr(item, "sklad", None) and getattr(item.sklad, "name", None):
                joy_name = self.safe(item.sklad.name, "Ombor")

            # MODEL
            model_name = self.safe(getattr(item.model, "name", None), "-")

            # NOMI
            type_name = self.safe(getattr(item.type, "name", None), "-")
            size_value = getattr(item.size, "size", None)
            size_str = self.size_to_str(size_value)

            if size_str:
                nomi = f"{type_name} ( {size_str} )"
            else:
                nomi = type_name

            # TIP
            unit_name = self.safe(getattr(getattr(item.size, "unit", None), "name", None), "-")

            # SONI
            count = int(item.count or 0)
            total_count += count

            table_data.append([
                Paragraph(joy_name, style_left_bold),
                Paragraph(model_name, style_left_bold),
                Paragraph(nomi, style_left_bold),
                Paragraph(unit_name, style_left_bold),
                Paragraph(str(count), style_center_table),
            ])

        # Jami qatori
        table_data.append([
            Paragraph("Jami", style_left_bold),
            "",
            "",
            "",
            Paragraph(str(total_count), style_center_table),
        ])

        # Jadval kengliklari
        col_widths = [
            38 * mm,   # JOY
            50 * mm,   # MODEL
            56 * mm,   # NOMI
            22 * mm,   # TIP
            18 * mm,   # SONI
        ]

        worker_table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1
        )

        # Rasmga yaqin style
        worker_table.setStyle(TableStyle([
            # Tashqi border
            ("BOX", (0, 0), (-1, -1), 0.9, colors.black),

            # Ichki chiziqlar
            ("GRID", (0, 0), (-1, -1), 0.6, colors.black),

            # Header background
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#b7dbe8")),

            # Body background (jami qatoridan oldingi qatorlargacha)
            ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#79ab8e")),

            # Jami qatori oq
            ("BACKGROUND", (0, -1), (-1, -1), colors.white),

            # Alignments
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (4, 1), (4, -1), "CENTER"),  # SONI

            # Padding
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),

            # Jami qatorida birlashtirish
            ("SPAN", (0, -1), (3, -1)),
            ("ALIGN", (0, -1), (0, -1), "LEFT"),

            # Font
            ("FONTNAME", (0, 0), (-1, -1), base_font),
        ]))

        story.append(worker_table)
        story.append(Spacer(1, 12 * mm))

        # SHAFYOR LINE
        # =========================================================
        # OrderHistory ichidagi driver_info ni olamiz
        driver_info = self.safe(getattr(order_history, "driver_info", None), "")

        # Chiziq ustida ko'rinadigan text:
        # agar driver_info bo'lsa chiqadi, bo'lmasa bo'sh turadi
        driver_text = driver_info if driver_info else "&nbsp;"

        # O'ng tomonda 2 qator:
        # 1-qator: driver_info (yoki bo'sh)
        # 2-qator: chiziq
        driver_block = Table(
            [
                [Paragraph(driver_text, style_left_bold)],
                [Paragraph("____________________________________", style_left)],
            ],
            colWidths=[130 * mm]
        )
        driver_block.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        # Chap tomonda "Shafyor:", o'ng tomonda text + chiziq
        shafyor_table = Table(
            [
                [
                    Paragraph("Shafyor:", style_left),
                    driver_block,
                ]
            ],
            colWidths=[30 * mm, 130 * mm]
        )
        shafyor_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        story.append(shafyor_table)

        # =========================================================
        # PDF META
        # =========================================================
        def add_pdf_meta(canvas, doc):
            canvas.setTitle("Hodim uchun")
            canvas.setAuthor("Smart Savdo")
            canvas.setSubject("Worker order PDF")
            canvas.setCreator("Smart Savdo")
            canvas.setKeywords("worker,order,pdf")

        doc.build(
            story,
            onFirstPage=add_pdf_meta,
            onLaterPages=add_pdf_meta,
        )