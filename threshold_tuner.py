"""
Sentio MVP - Threshold Tuner

Automatically adjusts detection thresholds based on human feedback.
Uses weighted moving average to smooth adjustments and prevent overreaction
to individual corrections.

Key concepts:
- Tracks predictions near threshold boundaries
- Adjusts thresholds when AI consistently makes errors at certain score ranges
- Persists learning history to JSON for continuity across sessions
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from supabase_client import get_backend, is_supabase_active


def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    config_file = Path(__file__).parent / config_path
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


class ThresholdTuner:
    """
    Tracks human feedback and suggests threshold adjustments.

    The tuner watches for patterns like:
    - AI predicts HEALTHY at score 0.55, but human says SICK
    - If this happens repeatedly, the threshold should be raised

    Uses "boundary region" tracking - only scores within 0.15 of the
    threshold are considered for adjustment, since errors far from
    the boundary indicate model issues, not threshold issues.
    """

    def __init__(self, config=None):
        """Initialize the tuner with configuration"""
        self.config = config or load_config()
        self.project_root = Path(__file__).parent

        # Get threshold tuning config (with defaults)
        tuning_config = self.config.get('threshold_tuning', {})
        self.enabled = tuning_config.get('enabled', True)
        self.min_samples = tuning_config.get('min_samples_before_update', 10)
        self.learning_rate = tuning_config.get('learning_rate', 0.1)

        # History file path
        history_path = tuning_config.get(
            'history_file',
            'Data_Bank/threshold_history.json'
        )
        self.history_file = self.project_root / history_path

        # Load existing history or initialize empty
        self.history = self._load_history()

    def _load_history(self):
        """Load feedback history from Supabase or JSON file"""
        default = {
            'vision': {
                'feedback': [],
                'current_threshold': self.config['vision']['thresholds']['health_score_threshold'],
                'suggested_threshold': None,
                'last_updated': None
            },
            'audio': {
                'feedback': [],
                'current_threshold': self.config['audio']['thresholds']['distress_score_threshold'],
                'suggested_threshold': None,
                'last_updated': None
            }
        }

        if is_supabase_active():
            try:
                backend = get_backend()
                for mod in ('vision', 'audio'):
                    rows = backend.get_threshold_feedback(mod)
                    default[mod]['feedback'] = [
                        {
                            'timestamp': r.get('timestamp', ''),
                            'score': float(r['score']),
                            'ai_prediction': r['ai_prediction'],
                            'human_agrees': r['human_agrees'],
                            'current_threshold': float(r['current_threshold']),
                        }
                        for r in rows
                    ]
                    # Load threshold override from Supabase config table
                    tc = backend.get_threshold_config(mod)
                    if tc:
                        default[mod]['current_threshold'] = float(tc['current_threshold'])
                        default[mod]['suggested_threshold'] = (
                            float(tc['suggested_threshold'])
                            if tc.get('suggested_threshold') is not None
                            else None
                        )
                return default
            except Exception:
                pass  # fall through to filesystem

        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return default

    def _save_history(self):
        """Save feedback history to JSON file"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)

    def record_feedback(self, modality, score, ai_prediction, human_agrees):
        """
        Record a feedback instance for threshold analysis.

        Args:
            modality: 'vision' or 'audio'
            score: The health/distress score (0-1)
            ai_prediction: What the AI predicted ('HEALTHY', 'SICK', etc.)
            human_agrees: True if human confirmed AI was correct

        Returns:
            bool: True if feedback was recorded, False if validation failed
        """
        # Validate inputs
        is_valid, error_msg = self.validate_feedback(modality, score, ai_prediction)
        if not is_valid:
            # Log warning but don't crash - graceful degradation
            import logging
            logging.warning(f"Feedback validation failed: {error_msg}")
            return False

        if modality not in self.history:
            return False

        current_thresh = self._get_current_threshold(modality)
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'score': score,
            'ai_prediction': ai_prediction,
            'human_agrees': human_agrees,
            'current_threshold': current_thresh
        }

        self.history[modality]['feedback'].append(feedback_entry)

        # Persist to Supabase if active
        if is_supabase_active():
            try:
                backend = get_backend()
                backend.record_threshold_feedback({
                    'modality': modality,
                    **feedback_entry,
                })
            except Exception:
                pass  # non-critical, in-memory state is still correct

        # Recalculate suggested threshold
        self._update_suggested_threshold(modality)

        # Save after each feedback
        self._save_history()
        return True

    def _get_current_threshold(self, modality):
        """Get the current threshold for a modality (Supabase override first)"""
        # Check Supabase config table override
        if is_supabase_active():
            try:
                tc = get_backend().get_threshold_config(modality)
                if tc and tc.get('current_threshold') is not None:
                    return float(tc['current_threshold'])
            except Exception:
                pass

        # Fallback to config.yaml
        if modality == 'vision':
            return self.config['vision']['thresholds']['health_score_threshold']
        elif modality == 'audio':
            return self.config['audio']['thresholds']['distress_score_threshold']
        return 0.5

    def _update_suggested_threshold(self, modality):
        """
        Calculate a suggested threshold based on feedback patterns.

        Algorithm:
        1. Focus on feedback entries near the current threshold (boundary region)
        2. If AI is wrong and predicted HEALTHY/NORMAL, threshold should go UP
        3. If AI is wrong and predicted SICK/DISTRESS, threshold should go DOWN
        4. Use weighted moving average to smooth adjustments
        """
        feedback = self.history[modality]['feedback']
        current_threshold = self._get_current_threshold(modality)

        if len(feedback) < self.min_samples:
            self.history[modality]['suggested_threshold'] = None
            return

        # Define boundary region (within 0.15 of threshold)
        boundary_low = current_threshold - 0.15
        boundary_high = current_threshold + 0.15

        # Collect errors in boundary region
        boundary_errors = []
        for entry in feedback[-50:]:  # Last 50 entries
            score = entry['score']
            if boundary_low <= score <= boundary_high and not entry['human_agrees']:
                boundary_errors.append(entry)

        if len(boundary_errors) < 3:
            # Not enough boundary errors to suggest change
            self.history[modality]['suggested_threshold'] = current_threshold
            return

        # Calculate adjustment direction and magnitude
        adjustment = 0.0

        for error in boundary_errors:
            score = error['score']
            prediction = error['ai_prediction']

            # For vision: HEALTHY when should be SICK → raise threshold
            # For audio: NORMAL when should be DISTRESS → raise threshold
            if prediction in ('HEALTHY', 'NORMAL'):
                # AI said healthy but was wrong → threshold too low
                adjustment += (score - current_threshold) * self.learning_rate
            else:
                # AI said sick but was wrong → threshold too high
                adjustment -= (current_threshold - score) * self.learning_rate

        # Apply adjustment with bounds
        suggested = current_threshold + adjustment
        suggested = max(0.3, min(0.7, suggested))  # Keep threshold reasonable

        self.history[modality]['suggested_threshold'] = round(suggested, 3)
        self.history[modality]['last_updated'] = datetime.now().isoformat()

    def get_suggested_threshold(self, modality):
        """
        Get the suggested threshold for a modality.

        Returns:
            tuple: (current_threshold, suggested_threshold, sample_count)
        """
        if modality not in self.history:
            return None, None, 0

        data = self.history[modality]
        return (
            self._get_current_threshold(modality),
            data.get('suggested_threshold'),
            len(data.get('feedback', []))
        )

    def get_statistics(self, modality):
        """
        Get detailed statistics about feedback for a modality.

        Returns:
            dict: Statistics including accuracy, error patterns, etc.
        """
        if modality not in self.history:
            return {}

        feedback = self.history[modality]['feedback']
        if not feedback:
            return {
                'total_samples': 0,
                'accuracy': 0.0,
                'boundary_errors': 0
            }

        total = len(feedback)
        correct = sum(1 for f in feedback if f['human_agrees'])
        current_threshold = self._get_current_threshold(modality)

        # Count errors in boundary region
        boundary_errors = sum(
            1 for f in feedback
            if not f['human_agrees']
            and abs(f['score'] - current_threshold) < 0.15
        )

        return {
            'total_samples': total,
            'correct': correct,
            'incorrect': total - correct,
            'accuracy': correct / total if total > 0 else 0.0,
            'boundary_errors': boundary_errors,
            'current_threshold': current_threshold,
            'suggested_threshold': self.history[modality].get('suggested_threshold')
        }

    def apply_threshold_update(self, modality):
        """
        Apply the suggested threshold to Supabase config table or config.yaml.

        Returns:
            bool: True if update was applied, False otherwise
        """
        suggested = self.history[modality].get('suggested_threshold')
        if suggested is None:
            return False

        current = self._get_current_threshold(modality)
        if abs(suggested - current) < 0.01:
            return False  # No significant change

        if is_supabase_active():
            try:
                backend = get_backend()
                backend.update_threshold_config(modality, {
                    'current_threshold': suggested,
                    'suggested_threshold': suggested,
                })
                self.history[modality]['current_threshold'] = suggested
                self._save_history()
                return True
            except Exception:
                pass  # fall through to config.yaml

        # Filesystem: update config.yaml
        config_path = self.project_root / 'config.yaml'
        with open(config_path, 'r') as f:
            config_content = f.read()

        if modality == 'vision':
            old_line = f"health_score_threshold: {current}"
            new_line = f"health_score_threshold: {suggested}"
        else:
            old_line = f"distress_score_threshold: {current}"
            new_line = f"distress_score_threshold: {suggested}"

        if old_line in config_content:
            config_content = config_content.replace(old_line, new_line)
            with open(config_path, 'w') as f:
                f.write(config_content)

            self.config = load_config()
            self.history[modality]['current_threshold'] = suggested
            self._save_history()
            return True

        return False

    def reset_history(self, modality=None):
        """
        Reset feedback history for one or all modalities.

        Args:
            modality: 'vision', 'audio', or None for all
        """
        if modality:
            if modality in self.history:
                self.history[modality]['feedback'] = []
                self.history[modality]['suggested_threshold'] = None
        else:
            for mod in self.history:
                self.history[mod]['feedback'] = []
                self.history[mod]['suggested_threshold'] = None

        self._save_history()

    def export_summary(self, modality=None, format='dict'):
        """
        Export a comprehensive summary of feedback data for reports or analysis.

        Args:
            modality: 'vision', 'audio', or None for all
            format: 'dict' for Python dict, 'json' for JSON string

        Returns:
            Summary data in requested format
        """
        modalities = [modality] if modality else ['vision', 'audio']
        summary = {
            'export_timestamp': datetime.now().isoformat(),
            'modalities': {}
        }

        for mod in modalities:
            if mod not in self.history:
                continue

            stats = self.get_statistics(mod)
            feedback = self.history[mod].get('feedback', [])

            # Calculate additional insights
            recent_feedback = feedback[-20:] if feedback else []
            recent_accuracy = (
                sum(1 for f in recent_feedback if f['human_agrees']) / len(recent_feedback)
                if recent_feedback else 0
            )

            # Error pattern analysis
            errors = [f for f in feedback if not f['human_agrees']]
            healthy_errors = sum(1 for e in errors if e['ai_prediction'] in ('HEALTHY', 'NORMAL'))
            sick_errors = len(errors) - healthy_errors

            summary['modalities'][mod] = {
                'statistics': stats,
                'total_feedback': len(feedback),
                'recent_accuracy': round(recent_accuracy, 3),
                'error_analysis': {
                    'total_errors': len(errors),
                    'false_positives': healthy_errors,  # Said healthy but was sick
                    'false_negatives': sick_errors,      # Said sick but was healthy
                    'error_tendency': 'lenient' if healthy_errors > sick_errors else 'strict' if sick_errors > healthy_errors else 'balanced'
                },
                'threshold_status': {
                    'current': self._get_current_threshold(mod),
                    'suggested': self.history[mod].get('suggested_threshold'),
                    'last_updated': self.history[mod].get('last_updated'),
                    'needs_adjustment': (
                        self.history[mod].get('suggested_threshold') is not None and
                        abs(self.history[mod].get('suggested_threshold', 0) -
                            self._get_current_threshold(mod)) > 0.01
                    )
                }
            }

        if format == 'json':
            return json.dumps(summary, indent=2, default=str)
        return summary

    def get_visualization_data(self, modality):
        """
        Get data formatted for threshold history visualization.

        Returns data suitable for time-series charts showing:
        - Score distribution over time
        - Accuracy trends
        - Threshold boundary effectiveness

        Args:
            modality: 'vision' or 'audio'

        Returns:
            dict with visualization-ready data arrays
        """
        if modality not in self.history:
            return {
                'error': f'Unknown modality: {modality}',
                'timestamps': [],
                'scores': [],
                'predictions': [],
                'agreements': []
            }

        feedback = self.history[modality].get('feedback', [])
        current_threshold = self._get_current_threshold(modality)

        if not feedback:
            return {
                'timestamps': [],
                'scores': [],
                'predictions': [],
                'agreements': [],
                'threshold': current_threshold,
                'boundary_low': current_threshold - 0.15,
                'boundary_high': current_threshold + 0.15,
                'rolling_accuracy': []
            }

        # Extract time series data
        timestamps = [f.get('timestamp', '') for f in feedback]
        scores = [f.get('score', 0) for f in feedback]
        predictions = [f.get('ai_prediction', '') for f in feedback]
        agreements = [f.get('human_agrees', False) for f in feedback]

        # Calculate rolling accuracy (window of 5)
        rolling_accuracy = []
        window = 5
        for i in range(len(agreements)):
            start = max(0, i - window + 1)
            window_data = agreements[start:i + 1]
            acc = sum(1 for a in window_data if a) / len(window_data)
            rolling_accuracy.append(round(acc, 3))

        # Score distribution bins for histogram
        bins = [0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
        score_distribution = {f'{bins[i]}-{bins[i+1]}': 0 for i in range(len(bins)-1)}
        for score in scores:
            for i in range(len(bins)-1):
                if bins[i] <= score < bins[i+1]:
                    score_distribution[f'{bins[i]}-{bins[i+1]}'] += 1
                    break

        # Boundary region analysis
        boundary_low = current_threshold - 0.15
        boundary_high = current_threshold + 0.15
        boundary_scores = [s for s in scores if boundary_low <= s <= boundary_high]
        boundary_errors = sum(
            1 for f in feedback
            if boundary_low <= f['score'] <= boundary_high and not f['human_agrees']
        )

        return {
            'timestamps': timestamps,
            'scores': scores,
            'predictions': predictions,
            'agreements': agreements,
            'threshold': current_threshold,
            'boundary_low': boundary_low,
            'boundary_high': boundary_high,
            'rolling_accuracy': rolling_accuracy,
            'score_distribution': score_distribution,
            'boundary_analysis': {
                'total_in_boundary': len(boundary_scores),
                'errors_in_boundary': boundary_errors,
                'boundary_error_rate': (
                    boundary_errors / len(boundary_scores)
                    if boundary_scores else 0
                )
            }
        }

    def validate_feedback(self, modality, score, ai_prediction):
        """
        Validate feedback parameters before recording.

        Args:
            modality: 'vision' or 'audio'
            score: The score value (0-1)
            ai_prediction: The AI prediction string

        Returns:
            tuple: (is_valid, error_message or None)
        """
        # Validate modality
        if modality not in ('vision', 'audio'):
            return False, f"Invalid modality '{modality}'. Must be 'vision' or 'audio'."

        # Validate score
        if not isinstance(score, (int, float)):
            return False, f"Score must be a number, got {type(score).__name__}."
        if not 0 <= score <= 1:
            return False, f"Score {score} out of range. Must be between 0 and 1."

        # Validate prediction
        valid_predictions = {
            'vision': ('HEALTHY', 'SICK'),
            'audio': ('NORMAL', 'DISTRESS')
        }
        if ai_prediction not in valid_predictions.get(modality, ()):
            expected = valid_predictions.get(modality, ())
            return False, f"Invalid prediction '{ai_prediction}' for {modality}. Expected one of {expected}."

        return True, None


# Convenience functions for use from other modules
_tuner_instance = None


def get_tuner():
    """Get or create the global tuner instance"""
    global _tuner_instance
    if _tuner_instance is None:
        _tuner_instance = ThresholdTuner()
    return _tuner_instance


def record_feedback(modality, score, ai_prediction, human_agrees):
    """Record feedback using the global tuner"""
    get_tuner().record_feedback(modality, score, ai_prediction, human_agrees)


def get_suggested_threshold(modality):
    """Get suggested threshold using the global tuner"""
    return get_tuner().get_suggested_threshold(modality)


def export_summary(modality=None, format='dict'):
    """Export feedback summary using the global tuner"""
    return get_tuner().export_summary(modality, format)


def get_visualization_data(modality):
    """Get visualization data using the global tuner"""
    return get_tuner().get_visualization_data(modality)
