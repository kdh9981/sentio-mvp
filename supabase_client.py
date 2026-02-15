"""
Sentio MVP - Storage Backend Abstraction

Provides two interchangeable backends:
- SupabaseBackend: Persistent cloud storage via Supabase (tables + storage bucket)
- FilesystemBackend: Local CSV/JSON/file operations (existing behavior)

get_backend() returns whichever is available, preferring Supabase when credentials exist.
"""

import os
import json
import csv
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger('sentio.backend')


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _load_config(config_path='config.yaml'):
    config_file = Path(__file__).parent / config_path
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def _get_supabase_credentials():
    """Try to get Supabase URL + key from Streamlit secrets or env vars."""
    url = None
    key = None

    # 1. Try Streamlit secrets (preferred on Streamlit Cloud)
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        pass

    # 2. Fallback to environment variables
    if not url:
        url = os.environ.get("SUPABASE_URL")
    if not key:
        key = os.environ.get("SUPABASE_KEY")

    if url and key:
        return url, key
    return None, None


# ---------------------------------------------------------------------------
# SupabaseBackend
# ---------------------------------------------------------------------------

class SupabaseBackend:
    """All I/O goes to Supabase Postgres tables + Storage bucket."""

    BUCKET = "sentio-files"

    def __init__(self, url: str, key: str):
        from supabase import create_client
        self.client = create_client(url, key)
        self._config = _load_config()
        logger.info("SupabaseBackend initialized")

    # -- Staging records ----------------------------------------------------

    def insert_staging_record(self, record: dict) -> dict:
        """Insert a new staging record. *record* should NOT contain 'id'."""
        data = {
            'timestamp': record.get('timestamp', datetime.now().isoformat()),
            'original_file': record['original_file'],
            'original_path': record.get('original_path'),
            'staged_file': record['staged_file'],
            'storage_path': record.get('storage_path'),
            'modality': record['modality'],
            'ai_classification': record['ai_classification'],
            'confidence': float(record['confidence']),
            'features': record.get('features', {}),
            'human_validated': False,
            'human_agrees': None,
            'final_classification': None,
            'validated_at': None,
        }
        resp = self.client.table('staging_records').insert(data).execute()
        return resp.data[0] if resp.data else data

    def get_pending_reviews(self) -> List[dict]:
        """Return all records where human_validated = false."""
        resp = (self.client.table('staging_records')
                .select('*')
                .eq('human_validated', False)
                .order('timestamp')
                .execute())
        return resp.data or []

    def finalize_staging_record(self, staged_file: str, human_agrees: bool,
                                final_classification: str) -> Optional[dict]:
        """Mark a staging record as validated."""
        resp = (self.client.table('staging_records')
                .update({
                    'human_validated': True,
                    'human_agrees': human_agrees,
                    'final_classification': final_classification,
                    'validated_at': datetime.now().isoformat(),
                })
                .eq('staged_file', staged_file)
                .eq('human_validated', False)
                .execute())
        return resp.data[0] if resp.data else None

    def get_all_staging_records(self) -> List[dict]:
        """Return every staging record (for statistics)."""
        resp = (self.client.table('staging_records')
                .select('*')
                .order('timestamp')
                .execute())
        return resp.data or []

    # -- File storage -------------------------------------------------------

    def upload_file(self, local_path: str, storage_path: str) -> str:
        """Upload a local file to Supabase Storage. Returns the storage path."""
        local_path = str(local_path)
        with open(local_path, 'rb') as f:
            self.client.storage.from_(self.BUCKET).upload(
                storage_path, f.read(),
                file_options={"content-type": "application/octet-stream", "upsert": "true"}
            )
        return storage_path

    def download_file(self, storage_path: str) -> bytes:
        """Download file bytes from Supabase Storage."""
        return self.client.storage.from_(self.BUCKET).download(storage_path)

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Get a temporary signed URL for a stored file."""
        resp = self.client.storage.from_(self.BUCKET).create_signed_url(
            storage_path, expires_in
        )
        return resp.get('signedURL') or resp.get('signedUrl', '')

    def move_file(self, from_path: str, to_path: str):
        """Move a file within the storage bucket."""
        self.client.storage.from_(self.BUCKET).move(from_path, to_path)

    # -- Reference samples --------------------------------------------------

    def get_reference_samples(self, classification: str) -> List[dict]:
        """Get all reference samples for a classification."""
        # Normalize: HEALTHY/NORMAL -> healthy, SICK/DISTRESS -> sick
        cls = 'healthy' if classification.upper() in ('HEALTHY', 'NORMAL') else 'sick'
        resp = (self.client.table('reference_samples')
                .select('*')
                .eq('classification', cls)
                .execute())
        return resp.data or []

    def add_reference_sample(self, filename: str, classification: str,
                             features: dict) -> bool:
        """Insert a reference sample (upsert by filename+classification)."""
        cls = 'healthy' if classification.upper() in ('HEALTHY', 'NORMAL') else 'sick'
        data = {
            'filename': filename,
            'classification': cls,
            'features': features,
            'added_at': datetime.now().isoformat(),
        }
        try:
            self.client.table('reference_samples').upsert(
                data, on_conflict='filename,classification'
            ).execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to add reference sample: {e}")
            return False

    # -- Threshold feedback -------------------------------------------------

    def record_threshold_feedback(self, entry: dict):
        """Insert a threshold feedback entry."""
        data = {
            'modality': entry['modality'],
            'timestamp': entry.get('timestamp', datetime.now().isoformat()),
            'score': float(entry['score']),
            'ai_prediction': entry['ai_prediction'],
            'human_agrees': entry['human_agrees'],
            'current_threshold': float(entry['current_threshold']),
        }
        self.client.table('threshold_feedback').insert(data).execute()

    def get_threshold_feedback(self, modality: str) -> List[dict]:
        """Get all threshold feedback for a modality."""
        resp = (self.client.table('threshold_feedback')
                .select('*')
                .eq('modality', modality)
                .order('timestamp')
                .execute())
        return resp.data or []

    def get_all_threshold_feedback(self, modality: str) -> List[dict]:
        """Alias for get_threshold_feedback."""
        return self.get_threshold_feedback(modality)

    # -- Threshold config ---------------------------------------------------

    def get_threshold_config(self, modality: str) -> Optional[dict]:
        """Get the current threshold config for a modality."""
        resp = (self.client.table('threshold_config')
                .select('*')
                .eq('modality', modality)
                .maybe_single()
                .execute())
        return resp.data

    def update_threshold_config(self, modality: str, updates: dict):
        """Update threshold config for a modality."""
        updates['last_updated'] = datetime.now().isoformat()
        self.client.table('threshold_config').update(updates).eq('modality', modality).execute()


# ---------------------------------------------------------------------------
# FilesystemBackend
# ---------------------------------------------------------------------------

class FilesystemBackend:
    """Wraps existing CSV/JSON/shutil logic for local development."""

    def __init__(self):
        self._config = _load_config()
        self._project_root = Path(__file__).parent
        logger.info("FilesystemBackend initialized (local mode)")

    def _staging_folder(self) -> Path:
        p = self._project_root / self._config['paths']['staging_folder']
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _staging_log(self) -> Path:
        return self._staging_folder() / 'staging_log.csv'

    # -- Staging records ----------------------------------------------------

    def insert_staging_record(self, record: dict) -> dict:
        staging_log = self._staging_log()
        # Convert features dict to JSON string for CSV storage
        csv_record = dict(record)
        if isinstance(csv_record.get('features'), dict):
            csv_record['features'] = json.dumps(csv_record['features'], default=str)

        fieldnames = [
            'timestamp', 'original_file', 'original_path', 'staged_file',
            'storage_path', 'modality', 'ai_classification', 'confidence',
            'features', 'human_validated', 'human_agrees',
            'final_classification', 'validated_at'
        ]
        file_exists = staging_log.exists()
        with open(staging_log, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            if not file_exists:
                writer.writeheader()
            writer.writerow(csv_record)
        return record

    def get_pending_reviews(self) -> List[dict]:
        staging_log = self._staging_log()
        if not staging_log.exists():
            return []
        pending = []
        with open(staging_log, 'r') as f:
            for row in csv.DictReader(f):
                if row['human_validated'] == 'False':
                    try:
                        row['features'] = json.loads(row['features'])
                    except (json.JSONDecodeError, KeyError):
                        row['features'] = {}
                    pending.append(row)
        return pending

    def finalize_staging_record(self, staged_file: str, human_agrees: bool,
                                final_classification: str) -> Optional[dict]:
        staging_log = self._staging_log()
        if not staging_log.exists():
            return None

        records = []
        target = None
        with open(staging_log, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['staged_file'] == staged_file and row['human_validated'] == 'False':
                    row['human_validated'] = 'True'
                    row['human_agrees'] = str(human_agrees)
                    row['final_classification'] = final_classification
                    row['validated_at'] = datetime.now().isoformat()
                    target = dict(row)
                records.append(row)

        if target is None:
            return None

        with open(staging_log, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        return target

    def get_all_staging_records(self) -> List[dict]:
        staging_log = self._staging_log()
        if not staging_log.exists():
            return []
        with open(staging_log, 'r') as f:
            return list(csv.DictReader(f))

    # -- File storage (local filesystem) ------------------------------------

    def upload_file(self, local_path: str, storage_path: str) -> str:
        """Copy file to staging folder. storage_path is relative."""
        dest = self._staging_folder() / Path(storage_path).name
        if str(local_path) != str(dest):
            shutil.copy2(str(local_path), str(dest))
        return storage_path

    def download_file(self, storage_path: str) -> bytes:
        full = self._staging_folder() / Path(storage_path).name
        return full.read_bytes()

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """No URLs for local files - return empty string."""
        return ''

    def move_file(self, from_path: str, to_path: str):
        """Move file within the project tree."""
        src = self._project_root / from_path
        dst = self._project_root / to_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.move(str(src), str(dst))

    # -- Reference samples --------------------------------------------------

    def get_reference_samples(self, classification: str) -> List[dict]:
        db_path = self._get_ref_db_path()
        if not db_path.exists():
            return []
        with open(db_path, 'r') as f:
            data = json.load(f)
        cls = 'healthy' if classification.upper() in ('HEALTHY', 'NORMAL') else 'sick'
        return data.get(cls, [])

    def add_reference_sample(self, filename: str, classification: str,
                             features: dict) -> bool:
        db_path = self._get_ref_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        data = {'healthy': [], 'sick': [], 'metadata': {}}
        if db_path.exists():
            with open(db_path, 'r') as f:
                data = json.load(f)

        cls = 'healthy' if classification.upper() in ('HEALTHY', 'NORMAL') else 'sick'
        samples = data.get(cls, [])
        if any(s.get('file') == filename for s in samples):
            return False
        samples.append({
            'file': filename,
            'added': datetime.now().isoformat(),
            'features': features,
        })
        data[cls] = samples
        data['metadata'] = {
            'last_updated': datetime.now().isoformat(),
            'total_samples': len(data.get('healthy', [])) + len(data.get('sick', []))
        }
        with open(db_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True

    def _get_ref_db_path(self) -> Path:
        ref_cfg = self._config.get('reference_comparison', {})
        return self._project_root / ref_cfg.get('database_file', 'Data_Bank/reference_features.json')

    # -- Threshold feedback -------------------------------------------------

    def record_threshold_feedback(self, entry: dict):
        """Append to the JSON history file (legacy format)."""
        # This is a lightweight passthrough - ThresholdTuner already manages
        # its own history file.  The backend method exists for interface parity.
        pass  # handled by ThresholdTuner's own _save_history

    def get_threshold_feedback(self, modality: str) -> List[dict]:
        history_path = self._get_threshold_history_path()
        if not history_path.exists():
            return []
        with open(history_path, 'r') as f:
            data = json.load(f)
        return data.get(modality, {}).get('feedback', [])

    def get_all_threshold_feedback(self, modality: str) -> List[dict]:
        return self.get_threshold_feedback(modality)

    def _get_threshold_history_path(self) -> Path:
        cfg = self._config.get('threshold_tuning', {})
        return self._project_root / cfg.get('history_file', 'Data_Bank/threshold_history.json')

    # -- Threshold config ---------------------------------------------------

    def get_threshold_config(self, modality: str) -> Optional[dict]:
        """Read threshold from config.yaml."""
        if modality == 'vision':
            return {'modality': 'vision',
                    'current_threshold': self._config['vision']['thresholds']['health_score_threshold']}
        elif modality == 'audio':
            return {'modality': 'audio',
                    'current_threshold': self._config['audio']['thresholds']['distress_score_threshold']}
        return None

    def update_threshold_config(self, modality: str, updates: dict):
        """Update threshold in config.yaml (existing behavior)."""
        config_path = self._project_root / 'config.yaml'
        with open(config_path, 'r') as f:
            content = f.read()

        current = self.get_threshold_config(modality)
        if not current:
            return

        old_val = current['current_threshold']
        new_val = updates.get('current_threshold', old_val)

        if modality == 'vision':
            old_line = f"health_score_threshold: {old_val}"
            new_line = f"health_score_threshold: {new_val}"
        else:
            old_line = f"distress_score_threshold: {old_val}"
            new_line = f"distress_score_threshold: {new_val}"

        if old_line in content:
            content = content.replace(old_line, new_line)
            with open(config_path, 'w') as f:
                f.write(content)


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_backend_instance = None


def get_backend():
    """Return SupabaseBackend if credentials found, else FilesystemBackend."""
    global _backend_instance
    if _backend_instance is not None:
        return _backend_instance

    url, key = _get_supabase_credentials()
    if url and key:
        try:
            _backend_instance = SupabaseBackend(url, key)
        except Exception as e:
            logger.warning(f"Supabase init failed, falling back to filesystem: {e}")
            _backend_instance = FilesystemBackend()
    else:
        _backend_instance = FilesystemBackend()

    return _backend_instance


def is_supabase_active() -> bool:
    """Check whether the active backend is Supabase."""
    return isinstance(get_backend(), SupabaseBackend)
