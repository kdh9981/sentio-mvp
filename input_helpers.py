"""
Sentio MVP - Input Helpers

Handles different input sources for the training app:
- File upload (images & audio)
- Clipboard paste (images only)
- Microphone recording (audio only)

Provides unified interface for saving files to temp location
and detecting input modality.
"""

import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Union

# Type hints for external objects
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None


# Image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}

# Audio extensions
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}


def get_temp_dir() -> Path:
    """Get or create a temp directory for uploaded files."""
    temp_dir = Path(tempfile.gettempdir()) / "sentio_uploads"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


def generate_filename(prefix: str, extension: str) -> str:
    """Generate a unique filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{timestamp}{extension}"


def detect_input_type(filename: str) -> Optional[str]:
    """
    Detect whether a file is an image or audio based on extension.

    Args:
        filename: Name of the file (with extension)

    Returns:
        'vision' for images, 'audio' for audio files, None if unknown
    """
    ext = Path(filename).suffix.lower()

    if ext in IMAGE_EXTENSIONS:
        return 'vision'
    elif ext in AUDIO_EXTENSIONS:
        return 'audio'
    else:
        return None


def save_uploaded_file(uploaded_file) -> Tuple[Optional[Path], Optional[str]]:
    """
    Save a Streamlit uploaded file to a temp location.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Tuple of (file_path, modality) or (None, None) if failed
    """
    if uploaded_file is None:
        return None, None

    try:
        # Detect modality from filename
        modality = detect_input_type(uploaded_file.name)
        if modality is None:
            return None, None

        # Get extension and create temp file
        ext = Path(uploaded_file.name).suffix.lower()
        filename = generate_filename("upload", ext)
        temp_path = get_temp_dir() / filename

        # Write file contents
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        return temp_path, modality

    except Exception as e:
        print(f"Error saving uploaded file: {e}")
        return None, None


def save_pasted_image(pil_image) -> Tuple[Optional[Path], str]:
    """
    Save a pasted PIL Image to a temp location.

    Args:
        pil_image: PIL Image object from clipboard paste

    Returns:
        Tuple of (file_path, 'vision') or (None, 'vision') if failed
    """
    if pil_image is None:
        return None, 'vision'

    try:
        filename = generate_filename("paste", ".png")
        temp_path = get_temp_dir() / filename

        # Save as PNG (lossless, good for analysis)
        pil_image.save(temp_path, format='PNG')

        return temp_path, 'vision'

    except Exception as e:
        print(f"Error saving pasted image: {e}")
        return None, 'vision'


def save_recorded_audio(audio_bytes) -> Tuple[Optional[Path], str]:
    """
    Save recorded audio bytes to a temp location.

    Streamlit's audio_input returns audio in WAV format.

    Args:
        audio_bytes: Raw audio bytes from st.audio_input()

    Returns:
        Tuple of (file_path, 'audio') or (None, 'audio') if failed
    """
    if audio_bytes is None:
        return None, 'audio'

    try:
        filename = generate_filename("recording", ".wav")
        temp_path = get_temp_dir() / filename

        # Write raw bytes (already in WAV format)
        with open(temp_path, 'wb') as f:
            f.write(audio_bytes.getvalue())

        return temp_path, 'audio'

    except Exception as e:
        print(f"Error saving recorded audio: {e}")
        return None, 'audio'


def cleanup_temp_files(max_age_hours: int = 24):
    """
    Clean up old temporary files.

    Args:
        max_age_hours: Delete files older than this many hours
    """
    try:
        temp_dir = get_temp_dir()
        if not temp_dir.exists():
            return

        import time
        now = time.time()
        max_age_seconds = max_age_hours * 3600

        for file_path in temp_dir.iterdir():
            if file_path.is_file():
                age = now - file_path.stat().st_mtime
                if age > max_age_seconds:
                    file_path.unlink()

    except Exception as e:
        print(f"Error cleaning temp files: {e}")


def get_supported_extensions(modality: str) -> Tuple[str, ...]:
    """
    Get supported file extensions for a modality.

    Args:
        modality: 'vision' or 'audio'

    Returns:
        Tuple of extensions like ('.jpg', '.png', ...)
    """
    if modality == 'vision':
        return tuple(IMAGE_EXTENSIONS)
    elif modality == 'audio':
        return tuple(AUDIO_EXTENSIONS)
    else:
        return tuple(IMAGE_EXTENSIONS | AUDIO_EXTENSIONS)
