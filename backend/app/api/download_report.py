"""
download_report.py
==================
Serves generated PDF assessment reports as browser-downloadable attachments.

GET /api/download-report/{filename}

- Only bare filenames are accepted (no path separators).
- The server resolves the full path internally from the known reports directory.
- The browser receives the file as a Content-Disposition attachment.
"""

import pathlib
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

# ─── Path resolution ──────────────────────────────────────────────────────────
_API_DIR      = pathlib.Path(__file__).resolve().parent   # backend/app/api/
_BACKEND_DIR  = _API_DIR.parent.parent                    # backend/
_REPORTS_DIR  = _BACKEND_DIR / "generated_reports"

# Only allow filenames that look like our generated reports — no traversal tricks
_SAFE_FILENAME = re.compile(r"^assessment_report_\d{8}_\d{6}\.pdf$")


@router.get("/download-report/{filename}")
async def download_report(filename: str):
    """
    Stream a previously generated PDF report to the browser as an attachment.

    The filename must match the pattern  assessment_report_YYYYMMDD_HHMMSS.pdf
    Any other value (including path separators) is rejected with 400.
    """
    # 1. Validate filename to prevent path traversal
    if not _SAFE_FILENAME.match(filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid report filename. Expected format: assessment_report_YYYYMMDD_HHMMSS.pdf",
        )

    # 2. Resolve the full path inside the known reports directory
    report_path = (_REPORTS_DIR / filename).resolve()

    # 3. Double-check the resolved path is still inside _REPORTS_DIR (belt + braces)
    try:
        report_path.relative_to(_REPORTS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied.")

    # 4. Make sure the file actually exists
    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Report '{filename}' not found. It may still be generating.",
        )

    # 5. Stream it as an attachment
    return FileResponse(
        path=str(report_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
