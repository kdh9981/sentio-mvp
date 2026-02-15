"""
Sentio MVP - Non-Destructive Data Pipeline

Key Features:
- Stages files for review (copies, never moves originals)
- Tracks AI classifications via backend (Supabase or local CSV)
- Supports human validation before final classification
- Maintains audit trail of all decisions
- Auto-populates reference database when files are verified

This prevents data loss during the human-in-the-loop training process.
"""

import os
import shutil
import json
import csv
from datetime import datetime
from pathlib import Path
import yaml
import logging

# Import reference database for auto-adding verified samples
from reference_database import get_reference_database
from supabase_client import get_backend, is_supabase_active


# Load configuration
def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    config_file = Path(__file__).parent / config_path
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


# Global config (loaded once)
_config = None


def get_config():
    """Get or load configuration"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_staging_log_path():
    """Get the path to the staging log CSV"""
    config = get_config()
    staging_folder = Path(__file__).parent / config['paths']['staging_folder']
    return staging_folder / 'staging_log.csv'


def ensure_directories():
    """Create all necessary directories from config"""
    config = get_config()
    project_root = Path(__file__).parent

    paths = [
        config['paths']['staging_folder'],
        config['paths']['healthy_images_folder'],
        config['paths']['sick_images_folder'],
        config['paths']['healthy_audio_folder'],
        config['paths']['sick_audio_folder'],
    ]

    for path in paths:
        full_path = project_root / path
        full_path.mkdir(parents=True, exist_ok=True)


def stage_classification(file_path, modality, ai_classification, confidence, features):
    """
    Stage a file for human review (non-destructive).

    Args:
        file_path: Original file path
        modality: 'vision' or 'audio'
        ai_classification: AI's prediction ('HEALTHY', 'SICK', 'NORMAL', 'DISTRESS')
        confidence: Confidence score (0-1)
        features: Dict of extracted features

    Returns:
        dict: The staged record
    """
    ensure_directories()
    backend = get_backend()

    file_path = Path(file_path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    staged_filename = f"{timestamp}_{file_path.name}"

    # Ensure features is a dict (not JSON string) for Supabase JSONB
    if isinstance(features, str):
        try:
            features = json.loads(features)
        except json.JSONDecodeError:
            features = {}

    record = {
        'timestamp': datetime.now().isoformat(),
        'original_file': file_path.name,
        'original_path': str(file_path.absolute()),
        'staged_file': staged_filename,
        'modality': modality,
        'ai_classification': ai_classification,
        'confidence': round(confidence, 4),
        'features': features,
        'human_validated': False,
        'human_agrees': None,
        'final_classification': None,
        'validated_at': None,
    }

    if is_supabase_active():
        # Upload file to cloud storage, then insert record
        storage_path = f"staging/{staged_filename}"
        backend.upload_file(str(file_path), storage_path)
        record['storage_path'] = storage_path
        backend.insert_staging_record(record)
    else:
        # Local: copy file to staging folder, append to CSV
        config = get_config()
        project_root = Path(__file__).parent
        staging_folder = project_root / config['paths']['staging_folder']
        shutil.copy2(file_path, staging_folder / staged_filename)
        backend.insert_staging_record(record)

    return record


def get_pending_reviews():
    """
    Get all files pending human review.

    Returns:
        list: List of records awaiting validation
    """
    backend = get_backend()
    return backend.get_pending_reviews()


def _determine_final_classification(ai_classification, human_agrees,
                                    human_classification=None):
    """Determine final classification based on human feedback."""
    if human_agrees:
        return ai_classification

    if human_classification:
        return human_classification

    # Auto-flip logic
    flip = {
        'HEALTHY': 'SICK',
        'SICK': 'HEALTHY',
        'NORMAL': 'DISTRESS',
        'DISTRESS': 'NORMAL',
    }
    return flip.get(ai_classification, human_classification or 'UNKNOWN')


def _get_verified_storage_prefix(modality, final_class):
    """Get the storage bucket prefix for verified files."""
    if modality == 'audio':
        if final_class in ('HEALTHY', 'NORMAL'):
            return 'verified/healthy_audio'
        return 'verified/sick_audio'
    else:
        if final_class in ('HEALTHY', 'NORMAL'):
            return 'verified/healthy_images'
        return 'verified/sick_images'


def finalize_classification(staged_file, human_agrees, human_classification=None):
    """
    Move file to final location after human validation.

    Args:
        staged_file: The staged filename (not original)
        human_agrees: True if human agrees with AI, False otherwise
        human_classification: Override classification if human disagrees

    Returns:
        bool: True if successful, False otherwise
    """
    backend = get_backend()
    config = get_config()
    project_root = Path(__file__).parent

    if is_supabase_active():
        # Find the record to get AI classification for flip logic
        pending = backend.get_pending_reviews()
        target = None
        for r in pending:
            if r['staged_file'] == staged_file:
                target = r
                break

        if target is None:
            return False

        final_class = _determine_final_classification(
            target['ai_classification'], human_agrees, human_classification
        )

        # Update the record in Supabase
        backend.finalize_staging_record(staged_file, human_agrees, final_class)

        # Move file in cloud storage
        storage_path = target.get('storage_path', f"staging/{staged_file}")
        dest_prefix = _get_verified_storage_prefix(
            target.get('modality', 'vision'), final_class
        )
        dest_path = f"{dest_prefix}/{target['original_file']}"
        try:
            backend.move_file(storage_path, dest_path)
        except Exception as e:
            logger = logging.getLogger('sentio.pipeline')
            logger.warning(f"Failed to move file in storage: {e}")

        # Build a record dict for _add_to_reference_database
        target['final_classification'] = final_class
        _add_to_reference_database(target)
        return True

    else:
        # Filesystem path: read CSV, update, move file locally
        staging_log = get_staging_log_path()
        if not staging_log.exists():
            return False

        records = []
        target_record = None

        with open(staging_log, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['staged_file'] == staged_file and row['human_validated'] == 'False':
                    row['human_validated'] = 'True'
                    row['human_agrees'] = str(human_agrees)
                    row['validated_at'] = datetime.now().isoformat()
                    row['final_classification'] = _determine_final_classification(
                        row['ai_classification'], human_agrees, human_classification
                    )
                    target_record = row
                records.append(row)

        if target_record is None:
            return False

        with open(staging_log, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        # Move file to final folder
        staging_folder = project_root / config['paths']['staging_folder']
        staging_path = staging_folder / staged_file

        final_class = target_record['final_classification']
        modality = target_record.get('modality', 'vision')

        if modality == 'audio':
            if final_class in ('HEALTHY', 'NORMAL'):
                final_folder = project_root / config['paths']['healthy_audio_folder']
            else:
                final_folder = project_root / config['paths']['sick_audio_folder']
        else:
            if final_class in ('HEALTHY', 'NORMAL'):
                final_folder = project_root / config['paths']['healthy_images_folder']
            else:
                final_folder = project_root / config['paths']['sick_images_folder']

        final_path = final_folder / target_record['original_file']

        if final_path.exists():
            stem = final_path.stem
            suffix = final_path.suffix
            counter = 1
            while final_path.exists():
                final_path = final_folder / f"{stem}_{counter}{suffix}"
                counter += 1

        if staging_path.exists():
            shutil.move(staging_path, final_path)

        _add_to_reference_database(target_record)
        return True


def _add_to_reference_database(record: dict):
    """
    Add verified sample to the reference database.

    This is called automatically when a file is finalized (moved to
    Verified_Healthy/ or Verified_Sick/). The features are extracted
    from the staging log record.
    """
    logger = logging.getLogger('sentio.pipeline')

    # Only process vision modality for now
    if record.get('modality') != 'vision':
        return

    # Parse features from JSON string if needed
    features = record.get('features', {})
    if isinstance(features, str):
        try:
            features = json.loads(features)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse features for {record.get('original_file')}")
            return

    if not features:
        logger.warning(f"No features available for {record.get('original_file')}")
        return

    final_classification = record.get('final_classification', '')
    original_file = record.get('original_file', 'unknown')

    try:
        reference_db = get_reference_database()
        added = reference_db.add_sample(
            features=features,
            classification=final_classification,
            filename=original_file
        )
        if added:
            logger.info(
                f"Added to reference database: {original_file} ({final_classification})"
            )
    except Exception as e:
        logger.warning(f"Failed to add to reference database: {e}")


def get_statistics():
    """
    Get statistics about the validation pipeline.

    Returns:
        dict: Statistics about staged, validated, and classified files
    """
    backend = get_backend()
    all_records = backend.get_all_staging_records()

    stats = {
        'total_staged': 0,
        'pending_review': 0,
        'validated': 0,
        'ai_correct': 0,
        'ai_incorrect': 0,
        'by_modality': {},
        'by_classification': {},
        'accuracy': 0.0,
    }

    for row in all_records:
        stats['total_staged'] += 1

        modality = row.get('modality', 'unknown')
        if modality not in stats['by_modality']:
            stats['by_modality'][modality] = {'total': 0, 'correct': 0}
        stats['by_modality'][modality]['total'] += 1

        # Normalize validated flag (bool from Supabase, string from CSV)
        validated = row.get('human_validated')
        is_validated = validated is True or validated == 'True'

        if not is_validated:
            stats['pending_review'] += 1
        else:
            stats['validated'] += 1
            agrees = row.get('human_agrees')
            is_agrees = agrees is True or agrees == 'True'
            if is_agrees:
                stats['ai_correct'] += 1
                stats['by_modality'][modality]['correct'] += 1
            else:
                stats['ai_incorrect'] += 1

            final = row.get('final_classification', 'unknown')
            stats['by_classification'][final] = \
                stats['by_classification'].get(final, 0) + 1

    if stats['validated'] > 0:
        stats['accuracy'] = stats['ai_correct'] / stats['validated']

    return stats


# CLI interface for human validation
if __name__ == "__main__":
    import sys

    def print_usage():
        print("Sentio Data Pipeline - Human Validation Interface")
        print("-" * 50)
        print("Commands:")
        print("  python data_pipeline.py review   - Review pending files")
        print("  python data_pipeline.py stats    - Show statistics")
        print("  python data_pipeline.py list     - List pending reviews")

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'stats':
        stats = get_statistics()
        print("\nPipeline Statistics")
        print("=" * 40)
        print(f"Total Staged:    {stats['total_staged']}")
        print(f"Pending Review:  {stats['pending_review']}")
        print(f"Validated:       {stats['validated']}")
        print(f"AI Correct:      {stats['ai_correct']}")
        print(f"AI Incorrect:    {stats['ai_incorrect']}")
        print(f"Accuracy:        {stats['accuracy']:.1%}")

        if stats['by_modality']:
            print("\nBy Modality:")
            for mod, data in stats['by_modality'].items():
                acc = data['correct'] / data['total'] if data['total'] > 0 else 0
                print(f"  {mod}: {data['total']} files, {acc:.1%} accuracy")

    elif command == 'list':
        pending = get_pending_reviews()
        if not pending:
            print("No files pending review.")
        else:
            print(f"\n{len(pending)} files pending review:")
            print("-" * 60)
            for record in pending:
                print(f"  {record['staged_file']}")
                print(f"    Original: {record['original_file']}")
                print(f"    AI says:  {record['ai_classification']} "
                      f"(confidence: {record['confidence']})")
                print()

    elif command == 'review':
        pending = get_pending_reviews()
        if not pending:
            print("No files pending review!")
            sys.exit(0)

        print(f"\n{len(pending)} files to review")
        print("=" * 50)

        for record in pending:
            print(f"\nFile: {record['original_file']}")
            print(f"Modality: {record['modality']}")
            print(f"AI Classification: {record['ai_classification']}")
            print(f"Confidence: {record['confidence']}")

            # Show key features
            features = record.get('features', {})
            if isinstance(features, dict):
                if record['modality'] == 'vision':
                    print(f"  - Health Score: {features.get('health_score', 'N/A')}")
                    print(f"  - Aspect Ratio: {features.get('aspect_ratio', 'N/A')}")
                elif record['modality'] == 'audio':
                    print(f"  - Distress Score: {features.get('distress_score', 'N/A')}")
                    print(f"  - Pitch: {features.get('pitch_mean', 'N/A')} Hz")

            # Get human input
            while True:
                response = input("\nIs AI correct? (y/n/s to skip): ").lower()
                if response == 'y':
                    finalize_classification(record['staged_file'], human_agrees=True)
                    print("-> Confirmed and moved to final location")
                    break
                elif response == 'n':
                    finalize_classification(record['staged_file'], human_agrees=False)
                    print("-> Corrected and moved to opposite category")
                    break
                elif response == 's':
                    print("-> Skipped")
                    break
                else:
                    print("Please enter 'y', 'n', or 's'")

        print("\nReview session complete!")
        stats = get_statistics()
        print(f"Current AI Accuracy: {stats['accuracy']:.1%}")

    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)
