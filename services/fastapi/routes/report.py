from fastapi import APIRouter, Response

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{city}.pdf")
def get_report(city: str):
    # For MVP: return a fake PDF (hello world)
    pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
    return Response(content=pdf_bytes, media_type="application/pdf")
