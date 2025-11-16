"""PDF validation utilities."""

from pathlib import Path

from app.config import settings

# Optional import for MIME type detection
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


def validate_pdf_file(file_path: Path) -> tuple[bool, str | None]:
    """Validate PDF file.
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        (is_valid, error_message)
    """
    # Check file exists
    if not file_path.exists():
        return False, "File does not exist"

    # Check file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > settings.max_pdf_size_mb:
        return False, f"File too large: {file_size_mb:.2f}MB > {settings.max_pdf_size_mb}MB"

    # Check MIME type (if python-magic is available)
    if HAS_MAGIC:
        try:
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_file(str(file_path))
            if detected_mime != "application/pdf":
                return False, f"Invalid MIME type: {detected_mime} (expected application/pdf)"
        except Exception:
            # Fallback if python-magic fails
            if file_path.suffix.lower() != ".pdf":
                return False, f"Invalid file extension: {file_path.suffix}"
    else:
        # Fallback: check file extension
        if file_path.suffix.lower() != ".pdf":
            return False, f"Invalid file extension: {file_path.suffix}"

    # Basic PDF header check
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            if header != b"%PDF":
                return False, "Invalid PDF header"
    except Exception as e:
        return False, f"Error reading file: {e}"

    return True, None


def scan_pdf_basic(file_path: Path) -> tuple[bool, str | None]:
    """Basic PDF scan (lightweight).
    
    Checks for:
    - Valid PDF structure
    - File size limits
    - Basic security flags (if available)
    
    Returns:
        (is_safe, warning_message)
    """
    is_valid, error = validate_pdf_file(file_path)
    if not is_valid:
        return False, error

    # Additional checks can be added here:
    # - Check for embedded JavaScript
    # - Check for suspicious objects
    # - Check for encryption

    return True, None

