import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pypdf import PdfReader

from app.api.deps import current_user
from app.pii.detector import detect
from app.storage import s3

api = APIRouter(prefix="/v1/files")


@api.post("")
async def upload(file: UploadFile = File(...), user: str = Depends(current_user)):
    data = await file.read()
    key = s3.put_file(user, file.filename or "upload.bin", data)

    text = ""
    if (file.filename or "").lower().endswith(".pdf"):
        try:
            text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
        except Exception as exc:  # PDF rusak / terenkripsi
            raise HTTPException(422, f"cannot parse PDF: {exc}")

    ents = detect(text)
    return {
        "key": key,
        "chars_extracted": len(text),
        "pii_found": {t: sum(1 for e in ents if e.type == t) for t in {e.type for e in ents}},
        "note": "PDF scan (tanpa teks) butuh OCR; belum diimplementasi.",
    }
