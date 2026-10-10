"""
services/report_generator.py
-----------------------------
Builds downloadable financial reports in CSV, Excel (via openpyxl/pandas)
and PDF (via reportlab) formats. Each function returns an in-memory
BytesIO/StringIO buffer so Flask can stream it straight to the browser
without writing temp files to disk.
"""

import io
from datetime import date
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from models import Income, Expense


def _collect_transactions(user_id: int, year: int, month: int | None = None):
    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()

    def _filter(items):
        out = []
        for i in items:
            if i.date.year != year:
                continue
            if month and i.date.month != month:
                continue
            out.append(i)
        return out

    incomes = _filter(incomes)
    expenses = _filter(expenses)

    rows = []
    for i in incomes:
        rows.append({
            "Date": i.date.isoformat(), "Type": "Income",
            "Category": i.category.name if i.category else "Others",
            "Description": i.description or "", "Amount": float(i.amount),
        })
    for e in expenses:
        rows.append({
            "Date": e.date.isoformat(), "Type": "Expense",
            "Category": e.category.name if e.category else "Others",
            "Description": e.description or "", "Amount": float(e.amount),
        })
    rows.sort(key=lambda r: r["Date"])
    return rows


def generate_csv(user_id: int, year: int, month: int | None = None) -> io.BytesIO:
    rows = _collect_transactions(user_id, year, month)
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Date", "Type", "Category", "Description", "Amount"])
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf


def generate_excel(user_id: int, year: int, month: int | None = None) -> io.BytesIO:
    rows = _collect_transactions(user_id, year, month)
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Date", "Type", "Category", "Description", "Amount"])

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")

        if not df.empty:
            summary = df.groupby(["Type", "Category"])["Amount"].sum().reset_index()
            summary.to_excel(writer, index=False, sheet_name="Category Summary")

            totals = df.groupby("Type")["Amount"].sum()
            total_income = totals.get("Income", 0)
            total_expense = totals.get("Expense", 0)
            overview = pd.DataFrame({
                "Metric": ["Total Income", "Total Expense", "Net Savings"],
                "Amount": [total_income, total_expense, total_income - total_expense],
            })
            overview.to_excel(writer, index=False, sheet_name="Overview")

    buf.seek(0)
    return buf


def generate_pdf(user_id: int, year: int, month: int | None, user_name: str) -> io.BytesIO:
    rows = _collect_transactions(user_id, year, month)
    total_income = sum(r["Amount"] for r in rows if r["Type"] == "Income")
    total_expense = sum(r["Amount"] for r in rows if r["Type"] == "Expense")
    net = total_income - total_expense

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], textColor=colors.HexColor("#2d3436"))
    elements = []

    period_label = f"{month:02d}/{year}" if month else f"Year {year}"
    elements.append(Paragraph("Personal Finance Dashboard - Financial Report", title_style))
    elements.append(Paragraph(f"Account holder: {user_name}", styles["Normal"]))
    elements.append(Paragraph(f"Period: {period_label}", styles["Normal"]))
    elements.append(Paragraph(f"Generated on: {date.today().isoformat()}", styles["Normal"]))
    elements.append(Spacer(1, 16))

    summary_data = [
        ["Total Income", f"Rs. {total_income:,.2f}"],
        ["Total Expense", f"Rs. {total_expense:,.2f}"],
        ["Net Savings", f"Rs. {net:,.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[8 * cm, 8 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f2f6")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe6e9")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Transactions", styles["Heading2"]))
    table_data = [["Date", "Type", "Category", "Description", "Amount"]]
    for r in rows:
        table_data.append([r["Date"], r["Type"], r["Category"], (r["Description"] or "")[:30], f"{r['Amount']:,.2f}"])

    if len(table_data) == 1:
        table_data.append(["-", "-", "-", "No transactions in this period", "-"])

    tx_table = Table(table_data, colWidths=[2.3 * cm, 2 * cm, 3 * cm, 6 * cm, 2.7 * cm], repeatRows=1)
    tx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6c5ce7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dfe6e9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9fb")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(tx_table)

    doc.build(elements)
    buf.seek(0)
    return buf
