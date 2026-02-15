"""
Sentio MVP - Reference Database for Similarity-Based Classification

Maintains feature vectors from verified images to improve future predictions.
Uses k-nearest neighbors similarity comparison to adjust AI confidence scores.

How it works:
1. When images are verified (moved to Verified_Healthy/ or Verified_Sick/),
   their features are extracted and stored in this database
2. When analyzing new images, we compare their features to the reference database
3. Similarity to verified samples adjusts the confidence score

This creates a feedback loop where human verification improves future accuracy.
"""

import json
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

import yaml

from supabase_client import get_backend, is_supabase_active


def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    config_file = Path(__file__).parent / config_path
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


class ReferenceDatabase:
    """
    Maintains feature vectors for verified images.
    Used to compare new images against known healthy/sick samples.
    """

    # Features used for comparison and their normalization ranges
    # These ranges are based on typical values observed in the system
    FEATURE_RANGES = {
        'aspect_ratio': (0.3, 2.0),       # height/width ratio
        'avg_saturation': (0, 255),        # HSV saturation 0-255
        'avg_brightness': (0, 255),        # HSV value 0-255
        'texture_variance': (0, 5000),     # Grayscale variance
        'body_alignment': (0, 1.0),        # Pose alignment score
    }

    # Weights for each feature in similarity calculation
    FEATURE_WEIGHTS = {
        'aspect_ratio': 1.0,
        'avg_saturation': 1.0,
        'avg_brightness': 0.8,
        'texture_variance': 0.6,
        'body_alignment': 1.2,  # Pose is a strong health indicator
    }

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the reference database"""
        self.config = config or load_config()
        self.logger = logging.getLogger('sentio.reference_db')

        # Load reference comparison config
        self.ref_config = self.config.get('reference_comparison', {})
        self.enabled = self.ref_config.get('enabled', True)
        self.min_samples = self.ref_config.get('min_samples_per_class', 3)
        self.similarity_weight = self.ref_config.get('similarity_weight', 0.3)
        self.k_neighbors = self.ref_config.get('k_neighbors', 5)

        # Database storage
        self.healthy_features: List[Dict] = []
        self.sick_features: List[Dict] = []

        # Database file path
        db_file = self.ref_config.get('database_file', 'Data_Bank/reference_features.json')
        self.db_path = Path(__file__).parent / db_file

        # Load existing database
        self._load_database()

    def _load_database(self):
        """Load reference features from Supabase or disk"""
        if is_supabase_active():
            try:
                backend = get_backend()
                healthy_rows = backend.get_reference_samples('healthy')
                sick_rows = backend.get_reference_samples('sick')

                self.healthy_features = [
                    {'file': r['filename'], 'added': r.get('added_at', ''),
                     'features': r['features'] if isinstance(r['features'], dict) else {}}
                    for r in healthy_rows
                ]
                self.sick_features = [
                    {'file': r['filename'], 'added': r.get('added_at', ''),
                     'features': r['features'] if isinstance(r['features'], dict) else {}}
                    for r in sick_rows
                ]

                self.logger.info(
                    f"Loaded reference database from Supabase: "
                    f"{len(self.healthy_features)} healthy, "
                    f"{len(self.sick_features)} sick samples"
                )
                return
            except Exception as e:
                self.logger.warning(f"Failed to load from Supabase, falling back to disk: {e}")

        # Filesystem fallback
        if not self.db_path.exists():
            self.logger.info("No reference database found, starting fresh")
            return

        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)

            self.healthy_features = data.get('healthy', [])
            self.sick_features = data.get('sick', [])

            self.logger.info(
                f"Loaded reference database: "
                f"{len(self.healthy_features)} healthy, "
                f"{len(self.sick_features)} sick samples"
            )
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Failed to load reference database: {e}")
            self.healthy_features = []
            self.sick_features = []

    def _save_database(self):
        """Persist reference features to disk (no-op for Supabase)"""
        if is_supabase_active():
            return  # Supabase writes are atomic per-insert

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'healthy': self.healthy_features,
            'sick': self.sick_features,
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'total_samples': len(self.healthy_features) + len(self.sick_features)
            }
        }

        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        self.logger.info(f"Saved reference database to {self.db_path}")

    def add_sample(self, features: Dict, classification: str, filename: str) -> bool:
        """
        Add a new verified sample to the database.

        Args:
            features: Feature dictionary from analysis
            classification: 'HEALTHY' or 'SICK'
            filename: Original filename for reference

        Returns:
            True if sample was added successfully
        """
        # Extract only the features we use for comparison
        comparison_features = self._extract_comparison_features(features)

        # Skip if features are missing
        if not comparison_features:
            self.logger.warning(f"Skipping {filename}: no valid features")
            return False

        sample = {
            'file': filename,
            'added': datetime.now().isoformat(),
            'features': comparison_features
        }

        # Add to appropriate in-memory list
        if classification.upper() in ('HEALTHY', 'NORMAL'):
            if not any(s['file'] == filename for s in self.healthy_features):
                self.healthy_features.append(sample)
                self.logger.info(f"Added healthy reference: {filename}")
            else:
                self.logger.debug(f"Duplicate skipped: {filename}")
                return False
        else:
            if not any(s['file'] == filename for s in self.sick_features):
                self.sick_features.append(sample)
                self.logger.info(f"Added sick reference: {filename}")
            else:
                self.logger.debug(f"Duplicate skipped: {filename}")
                return False

        # Persist: Supabase table or local JSON file
        if is_supabase_active():
            backend = get_backend()
            backend.add_reference_sample(filename, classification, comparison_features)
        else:
            self._save_database()

        return True

    def _extract_comparison_features(self, features: Dict) -> Dict:
        """Extract only the features used for comparison"""
        comparison = {}
        for key in self.FEATURE_RANGES.keys():
            if key in features:
                comparison[key] = features[key]
        return comparison

    def has_sufficient_samples(self) -> bool:
        """Check if we have enough samples for reference comparison"""
        return (
            len(self.healthy_features) >= self.min_samples and
            len(self.sick_features) >= self.min_samples
        )

    def get_sample_counts(self) -> Tuple[int, int]:
        """Get counts of healthy and sick samples"""
        return len(self.healthy_features), len(self.sick_features)

    def calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        Calculate similarity between two feature sets.

        Uses weighted Euclidean distance, normalized to 0-1 range.
        Returns similarity score where 1 = identical, 0 = completely different.
        """
        if not features1 or not features2:
            return 0.0

        total_weight = 0.0
        weighted_distance = 0.0

        for key, (min_val, max_val) in self.FEATURE_RANGES.items():
            if key not in features1 or key not in features2:
                continue

            weight = self.FEATURE_WEIGHTS.get(key, 1.0)
            total_weight += weight

            # Normalize values to 0-1 range
            range_size = max_val - min_val
            if range_size == 0:
                continue

            norm1 = (features1[key] - min_val) / range_size
            norm2 = (features2[key] - min_val) / range_size

            # Clamp to valid range
            norm1 = max(0, min(1, norm1))
            norm2 = max(0, min(1, norm2))

            # Weighted squared difference
            diff = (norm1 - norm2) ** 2
            weighted_distance += weight * diff

        if total_weight == 0:
            return 0.0

        # Normalize by total weight and convert distance to similarity
        avg_distance = math.sqrt(weighted_distance / total_weight)
        similarity = 1.0 - min(avg_distance, 1.0)

        return similarity

    def find_k_nearest(self, new_features: Dict, k: int = None) -> List[Tuple[Dict, float, str]]:
        """
        Find k most similar images from the database.

        Args:
            new_features: Features of the new image
            k: Number of neighbors (defaults to config value)

        Returns:
            List of (sample, similarity, classification) tuples, sorted by similarity
        """
        if k is None:
            k = self.k_neighbors

        comparison_features = self._extract_comparison_features(new_features)
        if not comparison_features:
            return []

        all_similarities = []

        # Compare to healthy samples
        for sample in self.healthy_features:
            sim = self.calculate_similarity(comparison_features, sample['features'])
            all_similarities.append((sample, sim, 'HEALTHY'))

        # Compare to sick samples
        for sample in self.sick_features:
            sim = self.calculate_similarity(comparison_features, sample['features'])
            all_similarities.append((sample, sim, 'SICK'))

        # Sort by similarity (highest first)
        all_similarities.sort(key=lambda x: x[1], reverse=True)

        return all_similarities[:k]

    def get_confidence_adjustment(self, new_features: Dict) -> Tuple[float, Dict]:
        """
        Calculate how much to adjust AI confidence based on reference similarity.

        Args:
            new_features: Features of the new image being analyzed

        Returns:
            Tuple of (adjustment_value, details_dict)
            - Positive adjustment means more likely HEALTHY
            - Negative adjustment means more likely SICK
        """
        details = {
            'reference_used': False,
            'healthy_samples': len(self.healthy_features),
            'sick_samples': len(self.sick_features),
            'k_neighbors': [],
            'avg_healthy_similarity': 0.0,
            'avg_sick_similarity': 0.0,
            'adjustment': 0.0
        }

        # Check if we have enough samples
        if not self.has_sufficient_samples():
            details['reason'] = (
                f"Need {self.min_samples} samples per class. "
                f"Have: {len(self.healthy_features)} healthy, {len(self.sick_features)} sick"
            )
            return 0.0, details

        if not self.enabled:
            details['reason'] = "Reference comparison disabled in config"
            return 0.0, details

        # Find k nearest neighbors
        neighbors = self.find_k_nearest(new_features)
        if not neighbors:
            details['reason'] = "No valid features for comparison"
            return 0.0, details

        details['reference_used'] = True

        # Calculate average similarity to each class
        healthy_sims = [sim for _, sim, cls in neighbors if cls == 'HEALTHY']
        sick_sims = [sim for _, sim, cls in neighbors if cls == 'SICK']

        avg_healthy = sum(healthy_sims) / len(healthy_sims) if healthy_sims else 0.0
        avg_sick = sum(sick_sims) / len(sick_sims) if sick_sims else 0.0

        details['avg_healthy_similarity'] = round(avg_healthy, 3)
        details['avg_sick_similarity'] = round(avg_sick, 3)

        # Record neighbor details
        for sample, sim, cls in neighbors:
            details['k_neighbors'].append({
                'file': sample['file'],
                'similarity': round(sim, 3),
                'class': cls
            })

        # Calculate adjustment
        # Positive = more likely healthy, Negative = more likely sick
        raw_adjustment = (avg_healthy - avg_sick) * self.similarity_weight
        details['adjustment'] = round(raw_adjustment, 4)

        self.logger.debug(
            f"Reference adjustment: {raw_adjustment:.4f} "
            f"(healthy_sim={avg_healthy:.3f}, sick_sim={avg_sick:.3f})"
        )

        return raw_adjustment, details

    def get_statistics(self) -> Dict:
        """Get database statistics for UI display"""
        healthy_count = len(self.healthy_features)
        sick_count = len(self.sick_features)

        return {
            'healthy_samples': healthy_count,
            'sick_samples': sick_count,
            'total_samples': healthy_count + sick_count,
            'is_active': self.has_sufficient_samples() and self.enabled,
            'min_required': self.min_samples,
            'similarity_weight': self.similarity_weight,
            'k_neighbors': self.k_neighbors,
            'status_message': self._get_status_message()
        }

    def _get_status_message(self) -> str:
        """Generate human-readable status message"""
        healthy = len(self.healthy_features)
        sick = len(self.sick_features)

        if not self.enabled:
            return "Reference comparison disabled"

        if healthy >= self.min_samples and sick >= self.min_samples:
            return f"Active: Using {healthy + sick} verified samples"

        needed_healthy = max(0, self.min_samples - healthy)
        needed_sick = max(0, self.min_samples - sick)

        parts = []
        if needed_healthy > 0:
            parts.append(f"{needed_healthy} more healthy")
        if needed_sick > 0:
            parts.append(f"{needed_sick} more sick")

        return f"Need {' and '.join(parts)} samples to activate"


# Singleton instance for easy access
_instance: Optional[ReferenceDatabase] = None


def get_reference_database() -> ReferenceDatabase:
    """Get or create the singleton reference database instance"""
    global _instance
    if _instance is None:
        _instance = ReferenceDatabase()
    return _instance


def reload_reference_database() -> ReferenceDatabase:
    """Force reload of the reference database"""
    global _instance
    _instance = ReferenceDatabase()
    return _instance
