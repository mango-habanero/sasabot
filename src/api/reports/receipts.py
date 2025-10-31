import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.configuration import app_logger

router = APIRouter(prefix="/reports")


@router.get("/receipts/{filename}")
async def get_receipt(filename: str) -> FileResponse:
    if not filename.startswith("receipt_") or not filename.endswith(".pdf"):
        app_logger.warning("Invalid receipt filename requested", filename=filename)
        raise HTTPException(status_code=400, detail="Invalid filename format")

    filepath = Path(tempfile.gettempdir()) / filename

    if not filepath.exists():
        app_logger.warning(
            "Receipt file not found", filename=filename, filepath=str(filepath)
        )
        raise HTTPException(status_code=404, detail="Receipt not found")

    app_logger.info("Serving receipt file", filename=filename)

    return FileResponse(
        path=str(filepath),
        media_type="application/pdf",
        filename=filename,
    )
