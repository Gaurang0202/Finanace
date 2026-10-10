"""
routes/reports.py
------------------
Report generation page and download endpoints for CSV / Excel / PDF.
"""

from datetime import date
from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user

from services.report_generator import generate_csv, generate_excel, generate_pdf

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports")
@login_required
def index():
    today = date.today()
    years = list(range(today.year - 4, today.year + 1))
    return render_template("reports.html", years=years, current_year=today.year, current_month=today.month)


@reports_bp.route("/reports/download/<fmt>")
@login_required
def download(fmt):
    year = request.args.get("year", date.today().year, type=int)
    month = request.args.get("month", type=int)  # None = full year
    uid = current_user.id
    period = f"{year}-{month:02d}" if month else f"{year}"

    if fmt == "csv":
        buf = generate_csv(uid, year, month)
        return send_file(buf, mimetype="text/csv", as_attachment=True, download_name=f"finance-report-{period}.csv")
    if fmt == "excel":
        buf = generate_excel(uid, year, month)
        return send_file(
            buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True, download_name=f"finance-report-{period}.xlsx"
        )
    if fmt == "pdf":
        buf = generate_pdf(uid, year, month, current_user.name)
        return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=f"finance-report-{period}.pdf")

    return "Unsupported format", 400
