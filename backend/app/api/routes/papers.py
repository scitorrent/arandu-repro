"""Paper hosting APIs."""

import shutil
import tempfile
from pathlib import Path

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func

from app.config import settings
from app.db.session import SessionLocal
from app.models import (
    Claim,
    Paper,
    PaperVersion,
    PaperVisibility,
    QualityScore,
)
from app.utils.pdf_validator import validate_pdf_file
from app.utils.storage import (
    ensure_paper_version_directory,
    generate_secure_aid,
    get_paper_version_path,
    validate_papers_base,
)

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])


@router.post("", status_code=201)
async def create_paper(
    request: Request,
    pdf: UploadFile | None = File(None),
    url: str | None = Form(None),
    title: str | None = Form(None),
    repo_url: str | None = Form(None),
    license: str | None = Form(None),
    visibility: PaperVisibility = Form(PaperVisibility.PRIVATE),
):
    """Create a new paper with version 1.

    Either `pdf` (multipart) or `url` must be provided.
    """
    db = SessionLocal()
    try:
        # Validate input
        if not pdf and not url:
            raise HTTPException(status_code=400, detail="Either 'pdf' or 'url' must be provided")

        if pdf and url:
            raise HTTPException(status_code=400, detail="Provide either 'pdf' or 'url', not both")

        # Generate AID
        aid = generate_secure_aid()

        # Handle PDF upload
        if pdf:
            # Validate file
            if not pdf.filename or not pdf.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="File must be a PDF")

            # Save to temp file first
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                shutil.copyfileobj(pdf.file, tmp_file)
                tmp_path = Path(tmp_file.name)

            # Validate PDF
            is_valid, error = validate_pdf_file(tmp_path)
            if not is_valid:
                tmp_path.unlink()
                raise HTTPException(status_code=400, detail=f"Invalid PDF: {error}")

            # Move to final location
            pdf_file_path = ensure_paper_version_directory(aid, 1)
            shutil.move(str(tmp_path), str(pdf_file_path))

        # Handle URL
        elif url:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(response.content)
                        tmp_path = Path(tmp_file.name)

                    # Validate PDF
                    is_valid, error = validate_pdf_file(tmp_path)
                    if not is_valid:
                        tmp_path.unlink()
                        raise HTTPException(status_code=400, detail=f"Invalid PDF from URL: {error}")

                    # Move to final location
                    pdf_file_path = ensure_paper_version_directory(aid, 1)
                    shutil.move(str(tmp_path), str(pdf_file_path))
            except httpx.HTTPError as e:
                raise HTTPException(status_code=400, detail=f"Failed to download PDF from URL: {str(e)}")

        # Create Paper
        paper = Paper(
            aid=aid,
            title=title,
            repo_url=repo_url,
            license=license,
            visibility=visibility,
        )
        db.add(paper)
        db.flush()

        # Create PaperVersion v1
        rel_path = get_paper_version_path(aid, 1)
        version = PaperVersion(
            aid=paper.aid,
            version=1,
            pdf_path=str(rel_path),
        )
        db.add(version)
        db.commit()
        db.refresh(paper)
        db.refresh(version)

        base_url = settings.api_base_url
        return {
            "aid": aid,
            "version": 1,
            "viewer_url": f"{base_url}/api/v1/papers/{aid}/viewer",
            "paper_url": f"{base_url}/api/v1/papers/{aid}",
        }
    finally:
        db.close()


@router.post("/{aid}/versions", status_code=201)
async def create_paper_version(
    aid: str,
    request: Request,
    pdf: UploadFile | None = File(None),
    url: str | None = Form(None),
):
    """Create a new version of an existing paper."""
    db = SessionLocal()
    try:
        # Get paper
        paper = db.query(Paper).filter(Paper.aid == aid, Paper.deleted_at.is_(None)).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Get latest version
        latest_version = (
            db.query(PaperVersion)
            .filter(PaperVersion.aid == aid, PaperVersion.deleted_at.is_(None))
            .order_by(PaperVersion.version.desc())
            .first()
        )
        new_version = (latest_version.version + 1) if latest_version else 1

        # Validate input
        if not pdf and not url:
            raise HTTPException(status_code=400, detail="Either 'pdf' or 'url' must be provided")

        # Handle PDF upload (same logic as create_paper)
        if pdf:
            if not pdf.filename or not pdf.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="File must be a PDF")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                shutil.copyfileobj(pdf.file, tmp_file)
                tmp_path = Path(tmp_file.name)

            is_valid, error = validate_pdf_file(tmp_path)
            if not is_valid:
                tmp_path.unlink()
                raise HTTPException(status_code=400, detail=f"Invalid PDF: {error}")

            pdf_file_path = ensure_paper_version_directory(aid, new_version)
            shutil.move(str(tmp_path), str(pdf_file_path))

        elif url:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(response.content)
                        tmp_path = Path(tmp_file.name)

                    is_valid, error = validate_pdf_file(tmp_path)
                    if not is_valid:
                        tmp_path.unlink()
                        raise HTTPException(status_code=400, detail=f"Invalid PDF from URL: {error}")

                    pdf_file_path = ensure_paper_version_directory(aid, new_version)
                    shutil.move(str(tmp_path), str(pdf_file_path))
            except httpx.HTTPError as e:
                raise HTTPException(status_code=400, detail=f"Failed to download PDF from URL: {str(e)}")

        # Create PaperVersion
        rel_path = get_paper_version_path(aid, new_version)
        version = PaperVersion(
            aid=paper.aid,
            version=new_version,
            pdf_path=str(rel_path),
        )
        db.add(version)
        db.commit()
        db.refresh(version)

        base_url = settings.api_base_url
        return {
            "aid": aid,
            "version": new_version,
            "viewer_url": f"{base_url}/api/v1/papers/{aid}/viewer?v={new_version}",
        }
    finally:
        db.close()


@router.get("/{aid}")
async def get_paper(
    aid: str,
):
    """Get paper metadata."""
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.aid == aid, Paper.deleted_at.is_(None)).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Get latest version
        latest_version = (
            db.query(PaperVersion)
            .filter(PaperVersion.aid == aid, PaperVersion.deleted_at.is_(None))
            .order_by(PaperVersion.version.desc())
            .first()
        )

        # Get counts
        claims_count = (
            db.query(func.count(Claim.id))
            .join(PaperVersion)
            .filter(PaperVersion.aid == aid, PaperVersion.deleted_at.is_(None))
            .scalar() or 0
        )

        scores_count = (
            db.query(func.count(QualityScore.id))
            .filter(
                (QualityScore.paper_id == paper.id) | (QualityScore.paper_version_id.in_(
                    db.query(PaperVersion.id).filter(PaperVersion.aid == aid)
                ))
            )
            .scalar() or 0
        )

        versions_count = (
            db.query(func.count(PaperVersion.id))
            .filter(PaperVersion.aid == aid, PaperVersion.deleted_at.is_(None))
            .scalar() or 0
        )

        # Get latest score
        latest_score = (
            db.query(QualityScore)
            .filter(
                (QualityScore.paper_id == paper.id) | (QualityScore.paper_version_id.in_(
                    db.query(PaperVersion.id).filter(PaperVersion.aid == aid)
                ))
            )
            .order_by(QualityScore.created_at.desc())
            .first()
        )

        return {
            "aid": paper.aid,
            "title": paper.title,
            "visibility": paper.visibility.value,
            "latest_version": latest_version.version if latest_version else None,
            "approved_public": paper.approved_public_at is not None,
            "approved_public_at": paper.approved_public_at.isoformat() if paper.approved_public_at else None,
            "latest_score": latest_score.score if latest_score else None,
            "counts": {
                "claims": claims_count,
                "scores": scores_count,
                "versions": versions_count,
            },
        }
    finally:
        db.close()


@router.get("/{aid}/viewer")
async def get_paper_viewer(
    aid: str,
    request: Request,
    v: int | None = Query(None, description="Version number (default: latest)"),
):
    """Stream PDF with Range support (206 Partial Content)."""
    db = SessionLocal()
    try:
        # Get paper
        paper = db.query(Paper).filter(Paper.aid == aid, Paper.deleted_at.is_(None)).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Get version
        if v:
            version = (
                db.query(PaperVersion)
                .filter(PaperVersion.aid == aid, PaperVersion.version == v, PaperVersion.deleted_at.is_(None))
                .first()
            )
        else:
            version = (
                db.query(PaperVersion)
                .filter(PaperVersion.aid == aid, PaperVersion.deleted_at.is_(None))
                .order_by(PaperVersion.version.desc())
                .first()
            )

        if not version:
            raise HTTPException(status_code=404, detail="Paper version not found")

        # Get full path
        base = validate_papers_base()
        full_path = base / version.pdf_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")

        # Handle Range requests
        range_header = request.headers.get("range")
        file_size = full_path.stat().st_size

        if range_header:
            # Parse Range header (format: "bytes=start-end")
            try:
                if not range_header.startswith("bytes="):
                    raise HTTPException(status_code=400, detail="Invalid Range header format")

                range_spec = range_header.replace("bytes=", "").split("-")
                if len(range_spec) != 2:
                    raise HTTPException(status_code=400, detail="Invalid Range header format")

                start_str, end_str = range_spec
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1

                # Validate range
                if start < 0 or end < 0:
                    raise HTTPException(status_code=416, detail="Range Not Satisfiable")
                if start >= file_size or end >= file_size:
                    raise HTTPException(status_code=416, detail="Range Not Satisfiable")
                if start > end:
                    raise HTTPException(status_code=416, detail="Range Not Satisfiable")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid Range header: non-numeric values")

            # Read chunk
            with open(full_path, "rb") as f:
                f.seek(start)
                chunk = f.read(end - start + 1)

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(len(chunk)),
                "Content-Type": "application/pdf",
            }

            return Response(content=chunk, status_code=206, headers=headers)
        else:
            # Full file
            return FileResponse(
                path=full_path,
                media_type="application/pdf",
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(file_size),
                },
            )
    finally:
        db.close()


@router.head("/{aid}/viewer")
async def head_paper_viewer(
    aid: str,
    v: int | None = Query(None),
):
    """HEAD request for PDF viewer (metadata only)."""
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.aid == aid, Paper.deleted_at.is_(None)).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        if v:
            version = (
                db.query(PaperVersion)
                .filter(PaperVersion.aid == aid, PaperVersion.version == v, PaperVersion.deleted_at.is_(None))
                .first()
            )
        else:
            version = (
                db.query(PaperVersion)
                .filter(PaperVersion.aid == aid, PaperVersion.deleted_at.is_(None))
                .order_by(PaperVersion.version.desc())
                .first()
            )

        if not version:
            raise HTTPException(status_code=404, detail="Paper version not found")

        base = validate_papers_base()
        full_path = base / version.pdf_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")

        file_size = full_path.stat().st_size

        return Response(
            status_code=200,
            headers={
                "Content-Type": "application/pdf",
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
            },
        )
    finally:
        db.close()


@router.get("/{aid}/claims")
async def get_paper_claims(
    aid: str,
    version: int | None = Query(None, description="Version number (default: latest)"),
    section: str | None = Query(None, description="Filter by section"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get claims for a paper version."""
    db = SessionLocal()
    try:
        # Get paper
        paper = db.query(Paper).filter(Paper.aid == aid, Paper.deleted_at.is_(None)).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        # Get version
        if version:
            paper_version = (
                db.query(PaperVersion)
                .filter(PaperVersion.aid == aid, PaperVersion.version == version, PaperVersion.deleted_at.is_(None))
                .first()
            )
        else:
            paper_version = (
                db.query(PaperVersion)
                .filter(PaperVersion.aid == aid, PaperVersion.deleted_at.is_(None))
                .order_by(PaperVersion.version.desc())
                .first()
            )

        if not paper_version:
            raise HTTPException(status_code=404, detail="Paper version not found")

        # Query claims
        query = db.query(Claim).filter(Claim.paper_version_id == paper_version.id)

        if section:
            query = query.filter(Claim.section == section)

        total = query.count()
        claims = query.order_by(Claim.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "aid": aid,
            "version": paper_version.version,
            "total": total,
            "claims": [
                {
                    "id": str(claim.id),
                    "text": claim.text,
                    "section": claim.section,
                    "confidence": claim.confidence,
                    "created_at": claim.created_at.isoformat(),
                }
                for claim in claims
            ],
        }
    finally:
        db.close()
