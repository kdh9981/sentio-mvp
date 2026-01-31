"""
Sentio MVP - Feedback Loop Test Suite

Tests the human feedback data collection, storage, and threshold tuning system.
Run with: python3 test_feedback_loop.py

Test modes:
  python3 test_feedback_loop.py           # Verify production data (non-destructive)
  python3 test_feedback_loop.py --unit    # Run unit tests (uses test subfolder)
  python3 test_feedback_loop.py --all     # Run both

Tests cover:
1. CSV logging functionality
2. Threshold history updates
3. File movement to verified folders
4. Threshold calculation logic
5. End-to-end feedback flow
"""

import os
import sys
import json
import csv
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestResult:
    """Simple test result tracker"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  ✓ {name}")

    def fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  ✗ {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"Results: {self.passed}/{total} passed")
        if self.errors:
            print(f"\nFailures:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        return self.failed == 0


def test_production_data():
    """Verify production data is accessible and correctly structured (non-destructive)"""
    print("=" * 50)
    print("Production Data Verification")
    print("=" * 50)

    # Import modules here to get fresh state
    from data_pipeline import get_statistics, get_pending_reviews

    results = TestResult()

    # Test 1: Staging log exists and is readable
    print("\n[Test 1] Staging Log")
    staging_log = PROJECT_ROOT / "Data_Bank" / "Staging" / "staging_log.csv"
    if staging_log.exists():
        try:
            with open(staging_log, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Verify required columns exist
            if rows:
                required_cols = ['timestamp', 'ai_classification', 'human_validated', 'modality']
                missing = [c for c in required_cols if c not in rows[0]]
                if missing:
                    results.fail("CSV structure", f"Missing columns: {missing}")
                else:
                    results.ok(f"Staging log valid ({len(rows)} records)")
            else:
                results.ok("Staging log exists (empty)")
        except Exception as e:
            results.fail("Staging log", str(e))
    else:
        results.ok("Staging log not yet created (normal for new install)")

    # Test 2: Threshold history JSON is valid
    print("\n[Test 2] Threshold History")
    history_file = PROJECT_ROOT / "Data_Bank" / "threshold_history.json"
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)

            # Verify structure
            if 'vision' not in history or 'audio' not in history:
                results.fail("History structure", "Missing 'vision' or 'audio' keys")
            else:
                vision_samples = len(history.get('vision', {}).get('feedback', []))
                audio_samples = len(history.get('audio', {}).get('feedback', []))
                results.ok(f"Threshold history valid (vision: {vision_samples}, audio: {audio_samples})")

                # Check for threshold suggestions
                vision_suggested = history['vision'].get('suggested_threshold')
                audio_suggested = history['audio'].get('suggested_threshold')
                if vision_suggested:
                    results.ok(f"Vision threshold suggestion: {vision_suggested}")
                if audio_suggested:
                    results.ok(f"Audio threshold suggestion: {audio_suggested}")

        except json.JSONDecodeError as e:
            results.fail("Threshold history", f"Invalid JSON: {e}")
        except Exception as e:
            results.fail("Threshold history", str(e))
    else:
        results.ok("Threshold history not yet created (normal for new install)")

    # Test 3: Verified folders exist
    print("\n[Test 3] Verified Folders")
    for folder in ["Verified_Healthy", "Verified_Sick"]:
        folder_path = PROJECT_ROOT / "Data_Bank" / folder
        if folder_path.exists():
            files = [f for f in folder_path.iterdir() if not f.name.startswith('.')]
            results.ok(f"{folder}/ exists ({len(files)} files)")
        else:
            results.fail(folder, "Folder not found")

    # Test 4: Statistics function works
    print("\n[Test 4] Statistics Function")
    try:
        stats = get_statistics()
        results.ok(f"Total staged: {stats['total_staged']}")
        results.ok(f"Validated: {stats['validated']}")
        results.ok(f"Accuracy: {stats['accuracy']:.1%}")

        if stats['by_modality']:
            for mod, data in stats['by_modality'].items():
                acc = data['correct'] / data['total'] if data['total'] > 0 else 0
                results.ok(f"  {mod}: {data['total']} files, {acc:.1%} accuracy")
    except Exception as e:
        results.fail("Statistics", str(e))

    # Test 5: Pending reviews function works
    print("\n[Test 5] Pending Reviews")
    try:
        pending = get_pending_reviews()
        results.ok(f"Pending reviews: {len(pending)} items")
    except Exception as e:
        results.fail("Pending reviews", str(e))

    return results.summary()


def test_threshold_tuner_logic():
    """Unit tests for ThresholdTuner calculation logic (isolated, no file I/O)"""
    print("=" * 50)
    print("ThresholdTuner Unit Tests")
    print("=" * 50)

    from threshold_tuner import ThresholdTuner

    results = TestResult()

    # Test 1: Boundary error detection
    print("\n[Test 1] Boundary Error Detection")
    try:
        # Create a tuner with mock config
        class MockTuner(ThresholdTuner):
            def __init__(self):
                self.config = {
                    'vision': {'thresholds': {'health_score_threshold': 0.5}},
                    'audio': {'thresholds': {'distress_score_threshold': 0.5}},
                    'threshold_tuning': {
                        'enabled': True,
                        'min_samples_before_update': 10,
                        'learning_rate': 0.1
                    }
                }
                self.min_samples = 10
                self.learning_rate = 0.1
                self.history = {
                    'vision': {'feedback': [], 'current_threshold': 0.5, 'suggested_threshold': None},
                    'audio': {'feedback': [], 'current_threshold': 0.5, 'suggested_threshold': None}
                }
                self.history_file = Path("/dev/null")  # Don't save

            def _save_history(self):
                pass  # Don't save during tests

        tuner = MockTuner()

        # Add boundary errors (scores near 0.5 threshold)
        for i in range(12):
            tuner.record_feedback(
                modality='vision',
                score=0.52 + (i * 0.01),  # 0.52 to 0.63 (all in boundary region)
                ai_prediction='HEALTHY',
                human_agrees=False  # AI was wrong
            )

        current, suggested, samples = tuner.get_suggested_threshold('vision')
        if samples >= 10:
            results.ok(f"Collected {samples} samples")
        else:
            results.fail("Sample collection", f"Expected >=10, got {samples}")

        if suggested is not None:
            results.ok(f"Suggestion generated: {suggested}")
        else:
            results.fail("Suggestion", "No suggestion generated")

        if suggested and suggested > current:
            results.ok(f"Direction correct: {current} → {suggested} (raised for false positives)")
        elif suggested:
            results.fail("Direction", f"Expected higher, got {suggested}")

    except Exception as e:
        results.fail("Boundary detection", str(e))

    # Test 2: Opposite direction (threshold too high)
    print("\n[Test 2] Threshold Too High Detection")
    try:
        tuner = MockTuner()

        # AI said SICK but was wrong (threshold too high)
        for i in range(12):
            tuner.record_feedback(
                modality='vision',
                score=0.45 - (i * 0.01),  # 0.45 down to 0.34 (below threshold)
                ai_prediction='SICK',
                human_agrees=False
            )

        current, suggested, samples = tuner.get_suggested_threshold('vision')

        if suggested and suggested < current:
            results.ok(f"Direction correct: {current} → {suggested} (lowered for false negatives)")
        elif suggested:
            results.fail("Direction", f"Expected lower, got {suggested}")

    except Exception as e:
        results.fail("Threshold too high", str(e))

    # Test 3: No suggestion with insufficient samples
    print("\n[Test 3] Minimum Sample Requirement")
    try:
        tuner = MockTuner()

        # Only 5 samples
        for i in range(5):
            tuner.record_feedback('vision', 0.52, 'HEALTHY', False)

        _, suggested, samples = tuner.get_suggested_threshold('vision')

        if samples == 5:
            results.ok("Sample count correct")
        if suggested is None:
            results.ok("No suggestion with insufficient samples")
        else:
            results.fail("Early suggestion", f"Got suggestion with only {samples} samples")

    except Exception as e:
        results.fail("Minimum samples", str(e))

    # Test 4: Statistics calculation
    print("\n[Test 4] Statistics Calculation")
    try:
        tuner = MockTuner()

        # Add mixed feedback
        tuner.record_feedback('vision', 0.6, 'HEALTHY', True)   # Correct
        tuner.record_feedback('vision', 0.7, 'HEALTHY', True)   # Correct
        tuner.record_feedback('vision', 0.52, 'HEALTHY', False) # Wrong (boundary)
        tuner.record_feedback('vision', 0.3, 'SICK', True)      # Correct
        tuner.record_feedback('vision', 0.2, 'SICK', False)     # Wrong (not boundary)

        stats = tuner.get_statistics('vision')

        if stats['total_samples'] == 5:
            results.ok("Total samples correct")
        else:
            results.fail("Total samples", f"Expected 5, got {stats['total_samples']}")

        if stats['correct'] == 3:
            results.ok("Correct count accurate")
        else:
            results.fail("Correct count", f"Expected 3, got {stats['correct']}")

        expected_accuracy = 3/5
        if abs(stats['accuracy'] - expected_accuracy) < 0.01:
            results.ok(f"Accuracy: {stats['accuracy']:.1%}")
        else:
            results.fail("Accuracy", f"Expected {expected_accuracy:.1%}, got {stats['accuracy']:.1%}")

        # Only one boundary error (0.52)
        if stats['boundary_errors'] == 1:
            results.ok("Boundary error count correct")
        else:
            results.fail("Boundary errors", f"Expected 1, got {stats['boundary_errors']}")

    except Exception as e:
        results.fail("Statistics", str(e))

    # Test 5: Threshold bounds
    print("\n[Test 5] Threshold Bounds")
    try:
        tuner = MockTuner()
        tuner.learning_rate = 1.0  # Aggressive for testing bounds

        # Try to push threshold very high
        for i in range(20):
            tuner.record_feedback('vision', 0.65, 'HEALTHY', False)

        _, suggested, _ = tuner.get_suggested_threshold('vision')

        if suggested and 0.3 <= suggested <= 0.7:
            results.ok(f"Threshold bounded: {suggested} (within 0.3-0.7)")
        elif suggested:
            results.fail("Threshold bounds", f"Out of bounds: {suggested}")

    except Exception as e:
        results.fail("Threshold bounds", str(e))

    # Test 6: Export summary function
    print("\n[Test 6] Export Summary")
    try:
        tuner = MockTuner()
        for i in range(5):
            tuner.record_feedback('vision', 0.6, 'HEALTHY', True)
            tuner.record_feedback('vision', 0.55, 'HEALTHY', False)

        summary = tuner.export_summary('vision')

        if 'modalities' in summary and 'vision' in summary['modalities']:
            results.ok("Export summary structure valid")
        else:
            results.fail("Export summary", "Missing expected keys")

        vision_data = summary['modalities']['vision']
        if 'error_analysis' in vision_data:
            results.ok(f"Error analysis included: {vision_data['error_analysis']['error_tendency']}")
        else:
            results.fail("Error analysis", "Missing from summary")

    except Exception as e:
        results.fail("Export summary", str(e))

    # Test 7: Visualization data function
    print("\n[Test 7] Visualization Data")
    try:
        tuner = MockTuner()
        for i in range(10):
            tuner.record_feedback('vision', 0.4 + (i * 0.05), 'HEALTHY', i % 2 == 0)

        viz_data = tuner.get_visualization_data('vision')

        if len(viz_data['timestamps']) == 10:
            results.ok("Timestamps extracted")
        else:
            results.fail("Timestamps", f"Expected 10, got {len(viz_data['timestamps'])}")

        if len(viz_data['rolling_accuracy']) == 10:
            results.ok("Rolling accuracy calculated")
        else:
            results.fail("Rolling accuracy", "Missing or wrong length")

        if 'boundary_analysis' in viz_data:
            results.ok("Boundary analysis included")
        else:
            results.fail("Boundary analysis", "Missing from viz data")

    except Exception as e:
        results.fail("Visualization data", str(e))

    # Test 8: Input validation
    print("\n[Test 8] Input Validation")
    try:
        tuner = MockTuner()

        # Test invalid modality
        is_valid, msg = tuner.validate_feedback('invalid', 0.5, 'HEALTHY')
        if not is_valid and 'modality' in msg.lower():
            results.ok("Rejects invalid modality")
        else:
            results.fail("Modality validation", f"Should reject 'invalid' modality")

        # Test out-of-range score
        is_valid, msg = tuner.validate_feedback('vision', 1.5, 'HEALTHY')
        if not is_valid and 'range' in msg.lower():
            results.ok("Rejects out-of-range score")
        else:
            results.fail("Score validation", f"Should reject score > 1")

        # Test invalid prediction
        is_valid, msg = tuner.validate_feedback('vision', 0.5, 'UNKNOWN')
        if not is_valid and 'prediction' in msg.lower():
            results.ok("Rejects invalid prediction")
        else:
            results.fail("Prediction validation", f"Should reject 'UNKNOWN' prediction")

        # Test valid input
        is_valid, msg = tuner.validate_feedback('vision', 0.5, 'HEALTHY')
        if is_valid:
            results.ok("Accepts valid input")
        else:
            results.fail("Valid input", f"Should accept valid parameters")

    except Exception as e:
        results.fail("Input validation", str(e))

    return results.summary()


def test_data_pipeline_integration():
    """Integration tests using a test subfolder (cleaned up after)"""
    print("=" * 50)
    print("Data Pipeline Integration Tests")
    print("=" * 50)

    results = TestResult()

    # Create test subfolder in Data_Bank
    test_folder = PROJECT_ROOT / "Data_Bank" / "_test_temp"

    try:
        # Setup test folders
        test_staging = test_folder / "Staging"
        test_healthy = test_folder / "Verified_Healthy"
        test_sick = test_folder / "Verified_Sick"

        for folder in [test_staging, test_healthy, test_sick]:
            folder.mkdir(parents=True, exist_ok=True)

        print("\n[Test 1] CSV Writing")
        # Create test staging log
        test_log = test_staging / "staging_log.csv"

        test_record = {
            'timestamp': datetime.now().isoformat(),
            'original_file': 'test.jpg',
            'original_path': '/test/path/test.jpg',
            'staged_file': 'staged_test.jpg',
            'modality': 'vision',
            'ai_classification': 'HEALTHY',
            'confidence': 0.75,
            'features': '{"health_score": 0.75}',
            'human_validated': 'False',
            'human_agrees': '',
            'final_classification': '',
            'validated_at': ''
        }

        with open(test_log, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=test_record.keys())
            writer.writeheader()
            writer.writerow(test_record)

        if test_log.exists():
            results.ok("CSV file created")
        else:
            results.fail("CSV creation", "File not created")

        # Verify content
        with open(test_log, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if len(rows) == 1 and rows[0]['ai_classification'] == 'HEALTHY':
            results.ok("CSV content correct")
        else:
            results.fail("CSV content", f"Unexpected content: {rows}")

        print("\n[Test 2] JSON Writing")
        test_history = test_folder / "threshold_history.json"

        history_data = {
            'vision': {
                'feedback': [
                    {'score': 0.5, 'ai_prediction': 'HEALTHY', 'human_agrees': True}
                ],
                'current_threshold': 0.5,
                'suggested_threshold': None
            }
        }

        with open(test_history, 'w') as f:
            json.dump(history_data, f, indent=2)

        if test_history.exists():
            results.ok("JSON file created")

        with open(test_history, 'r') as f:
            loaded = json.load(f)

        if loaded['vision']['feedback'][0]['score'] == 0.5:
            results.ok("JSON content correct")
        else:
            results.fail("JSON content", "Data mismatch")

        print("\n[Test 3] File Operations")
        # Create a test file
        test_file = test_staging / "test_image.jpg"
        test_file.write_bytes(b"fake image data")

        if test_file.exists():
            results.ok("Test file created in staging")

        # Move to verified
        dest = test_healthy / "test_image.jpg"
        shutil.move(str(test_file), str(dest))

        if dest.exists() and not test_file.exists():
            results.ok("File moved to verified folder")
        else:
            results.fail("File movement", "File not moved correctly")

    except Exception as e:
        results.fail("Integration test", str(e))

    finally:
        # Cleanup
        if test_folder.exists():
            shutil.rmtree(test_folder)
            print("\n[Cleanup] Test folder removed")

    return results.summary()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the Sentio feedback loop system")
    parser.add_argument("--unit", "-u", action="store_true",
                       help="Run unit tests for ThresholdTuner")
    parser.add_argument("--integration", "-i", action="store_true",
                       help="Run integration tests (uses temp folder)")
    parser.add_argument("--all", "-a", action="store_true",
                       help="Run all tests")
    args = parser.parse_args()

    success = True

    # Default: run production verification
    if not any([args.unit, args.integration, args.all]):
        success = test_production_data()

    if args.unit or args.all:
        print("\n")
        success = test_threshold_tuner_logic() and success

    if args.integration or args.all:
        print("\n")
        success = test_data_pipeline_integration() and success

    if args.all or not any([args.unit, args.integration]):
        print("\n")
        success = test_production_data() and success

    sys.exit(0 if success else 1)
