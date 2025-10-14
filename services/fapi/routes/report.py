from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
import matplotlib.pyplot as plt

from fapi.db import get_db
from fapi.models.model_predictions import ModelPrediction
from fapi.models.risk_predictions import RiskPrediction
from fapi.models.anomaly_signals import AnomalySignal

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{city}.pdf")
def get_report(city: str, db: Session = Depends(get_db)):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"Housing Insights Report — {city}", styles["Title"]))
    elements.append(Spacer(1, 20))

    # --------------------
    # Forecast section
    # --------------------
    forecasts = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.city == city, ModelPrediction.target == "price")
        .order_by(ModelPrediction.predict_date.asc())
        .all()
    )

    if forecasts:
        elements.append(Paragraph("📈 Forecast", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        # Get data for chart
        dates = [f.predict_date for f in forecasts]
        values = [float(f.yhat) for f in forecasts]
        lowers = [float(f.yhat_lower) if f.yhat_lower else None for f in forecasts]
        uppers = [float(f.yhat_upper) if f.yhat_upper else None for f in forecasts]

        # Plot chart with Matplotlib
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(dates, values, label="Forecast", color="blue")
        ax.fill_between(
            dates, lowers, uppers, color="blue", alpha=0.2, label="Confidence"
        )
        ax.set_title(f"Price Forecast — {city}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Predicted Value")
        ax.legend()

        # Save chart to BytesIO
        chart_buffer = BytesIO()
        plt.savefig(chart_buffer, format="PNG", bbox_inches="tight")
        plt.close(fig)
        chart_buffer.seek(0)

        # Embed chart into PDF
        elements.append(Image(chart_buffer, width=400, height=200))
        elements.append(Spacer(1, 20))

    # --------------------
    # Risk section
    # --------------------
    risks = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.city == city)
        .order_by(RiskPrediction.predict_date.desc())
        .all()
    )
    if risks:
        elements.append(Paragraph("⚠️ Risk Indices", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        data = [["Risk Type", "Value"]]
        for r in risks:
            data.append([r.risk_type, f"{float(r.risk_value):.2f}"])

        table = Table(data, colWidths=[200, 150])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 20))

    # --------------------
    # Anomalies section
    # --------------------
    anomalies = (
        db.query(AnomalySignal)
        .filter(AnomalySignal.city == city, AnomalySignal.is_anomaly == True)
        .order_by(AnomalySignal.detect_date.desc())
        .limit(3)
        .all()
    )
    if anomalies:
        elements.append(Paragraph("🚨 Recent Anomalies", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        data = [["Date", "Target", "Score"]]
        for a in anomalies:
            data.append([a.detect_date.isoformat(), a.target, f"{a.anomaly_score:.2f}"])

        table = Table(data, colWidths=[120, 150, 100])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkred),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 20))

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(
        Paragraph(
            "Generated by Housing Insights & Risk Dashboard — © 2025", styles["Normal"]
        )
    )

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    return Response(content=buffer.read(), media_type="application/pdf")
