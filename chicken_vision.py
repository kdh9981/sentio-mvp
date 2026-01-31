"""
Sentio MVP - Chicken Vision Analysis
Tier 1: YOLOv10n + MediaPipe Pose + Multi-Feature Health Scoring

Upgrades from baseline:
- YOLOv10n: 10% faster than YOLOv8n, better accuracy
- MediaPipe Pose: Body keypoint detection for posture analysis
- Multi-feature scoring: aspect ratio, color, texture, pose alignment
"""

import os
import numpy as np
import yaml
import logging
from pathlib import Path

# OpenCV import with graceful fallback
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    print("Warning: opencv-python not installed. Run: pip install opencv-python-headless")

# Optional imports with fallback
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Run: pip install ultralytics")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: mediapipe not installed. Run: pip install mediapipe")

# Import reference database for similarity-based classification
from reference_database import get_reference_database


# Load configuration
def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    config_file = Path(__file__).parent / config_path
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


class ChickenVisionAnalyzer:
    """Multi-feature chicken health analysis using YOLOv10n + MediaPipe"""

    def __init__(self, config=None):
        """Initialize the analyzer with configuration"""
        self.config = config or load_config()
        self.vision_config = self.config['vision']
        self.logger = logging.getLogger('sentio.vision')

        # Initialize detection model
        self.detection_model = None
        if YOLO_AVAILABLE:
            model_path = self.vision_config['detection_model']
            # Auto-download YOLOv10n if not present
            self.detection_model = YOLO(model_path)
            self.logger.info(f"Loaded detection model: {model_path}")

        # Initialize pose detector
        self.pose_detector = None
        if MEDIAPIPE_AVAILABLE and self.vision_config['use_pose_estimation']:
            mp_pose = mp.solutions.pose
            self.pose_detector = mp_pose.Pose(
                static_image_mode=True,
                min_detection_confidence=0.5,
                model_complexity=1  # 0=lite, 1=full, 2=heavy
            )
            self.logger.info("Initialized MediaPipe pose detector")

        # Initialize reference database for similarity-based classification
        self.reference_db = get_reference_database()
        ref_stats = self.reference_db.get_statistics()
        self.logger.info(
            f"Reference database: {ref_stats['status_message']}"
        )

    def analyze(self, image_path):
        """
        Analyze a chicken image for health indicators.

        Args:
            image_path: Path to the image file

        Returns:
            tuple: (status, details) where status is 'HEALTHY', 'SICK', or None
        """
        # Check if OpenCV is available
        if not CV2_AVAILABLE:
            return None, {"error": "OpenCV (cv2) not installed. Install with: pip install opencv-python-headless"}

        # Read image
        image = cv2.imread(str(image_path))
        if image is None:
            return None, {"error": f"Cannot read image: {image_path}"}

        if not YOLO_AVAILABLE or self.detection_model is None:
            return None, {"error": "Detection model not available"}

        # Step 1: Detect chicken with YOLO
        results = self.detection_model(image, device='cpu', verbose=False)

        bird_class_id = self.vision_config['bird_class_id']
        confidence_threshold = self.vision_config['confidence_threshold']

        for box in results[0].boxes:
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])

            # Filter for birds with sufficient confidence
            if class_id != bird_class_id:
                continue
            if confidence < confidence_threshold:
                continue

            # Extract region of interest
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            roi = image[y1:y2, x1:x2]

            if roi.size == 0:
                continue

            # Step 2: Extract health features
            features = self._extract_health_features(roi, image)
            features['detection_confidence'] = confidence
            features['bbox'] = [x1, y1, x2, y2]

            # Step 3: Calculate base health score
            base_health_score = self._calculate_health_score(features)
            features['base_health_score'] = base_health_score

            # Step 4: Apply reference-based adjustment
            ref_adjustment, ref_details = self.reference_db.get_confidence_adjustment(features)
            features['reference_adjustment'] = ref_adjustment
            features['reference_details'] = ref_details

            # Combine base score with reference adjustment
            # Clamp to valid 0-1 range
            health_score = max(0.0, min(1.0, base_health_score + ref_adjustment))
            features['health_score'] = health_score

            # Determine status
            threshold = self.vision_config['thresholds']['health_score_threshold']
            status = "HEALTHY" if health_score > threshold else "SICK"

            # Log reference impact if used
            if ref_details.get('reference_used'):
                self.logger.info(
                    f"Analysis complete: {status} (score: {health_score:.2f}, "
                    f"base: {base_health_score:.2f}, ref_adj: {ref_adjustment:+.3f})"
                )
            else:
                self.logger.info(f"Analysis complete: {status} (score: {health_score:.2f})")

            return status, features

        # FALLBACK: Analyze full image if no bird detected by YOLO
        # This handles cases where YOLO doesn't classify chickens as "bird" (class 14)
        self.logger.info("No bird detected by YOLO, using full image fallback")

        features = self._extract_health_features(image, image)
        features['detection_confidence'] = 0.0  # Indicates fallback was used
        features['bbox'] = [0, 0, image.shape[1], image.shape[0]]
        features['fallback_used'] = True

        # Calculate health score
        base_health_score = self._calculate_health_score(features)
        features['base_health_score'] = base_health_score

        # Reference adjustment
        ref_adjustment, ref_details = self.reference_db.get_confidence_adjustment(features)
        features['reference_adjustment'] = ref_adjustment
        features['reference_details'] = ref_details

        health_score = max(0.0, min(1.0, base_health_score + ref_adjustment))
        features['health_score'] = health_score

        threshold = self.vision_config['thresholds']['health_score_threshold']
        status = "HEALTHY" if health_score > threshold else "SICK"

        self.logger.info(f"Fallback analysis: {status} (score: {health_score:.2f})")
        return status, features

    def _extract_health_features(self, roi, full_image):
        """
        Extract multiple health indicators from the detected region.

        Features extracted:
        - Aspect ratio: Posture indicator (standing vs lying)
        - Color analysis: Comb health via saturation
        - Brightness: Alertness indicator
        - Texture variance: Feather condition
        - Pose alignment: Body posture from keypoints
        """
        features = {}

        # 1. Aspect ratio (basic posture)
        h, w = roi.shape[:2]
        features['aspect_ratio'] = h / w if w > 0 else 0

        # 2. Color analysis (HSV for comb health)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        features['avg_saturation'] = float(np.mean(hsv[:, :, 1]))
        features['avg_brightness'] = float(np.mean(hsv[:, :, 2]))

        # 3. Texture analysis (feather condition via variance)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        features['texture_variance'] = float(np.var(gray))

        # 4. Pose estimation (body posture)
        features['pose_detected'] = False
        features['body_alignment'] = 0.5  # Default neutral score

        if self.pose_detector and self.vision_config['use_pose_estimation']:
            try:
                # Convert ROI to RGB for MediaPipe
                roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
                pose_results = self.pose_detector.process(roi_rgb)

                if pose_results.pose_landmarks:
                    landmarks = pose_results.pose_landmarks.landmark
                    features['pose_detected'] = True
                    features['body_alignment'] = self._calculate_alignment(landmarks)
                    features['visible_landmarks'] = sum(
                        1 for lm in landmarks if lm.visibility > 0.5
                    )
            except Exception as e:
                self.logger.warning(f"Pose estimation failed: {e}")

        return features

    def _calculate_alignment(self, landmarks):
        """
        Calculate body alignment score from pose landmarks.

        A higher score indicates better posture (more upright, alert).
        """
        # Count visible landmarks (visibility > 0.5)
        visible_count = sum(1 for lm in landmarks if lm.visibility > 0.5)

        # Normalize: more visible landmarks generally means clearer posture
        # Max 33 landmarks in MediaPipe pose
        base_score = min(visible_count / 15, 1.0)

        # TODO: Add more sophisticated posture analysis here
        # Could check:
        # - Shoulder alignment (horizontal = good)
        # - Head position relative to body
        # - Overall body verticality

        return base_score

    def _calculate_health_score(self, features):
        """
        Combine features into a single health score (0-1).

        Higher score = healthier chicken.
        """
        weights = self.vision_config['weights']
        thresholds = self.vision_config['thresholds']
        score = 0.0

        # Aspect ratio: standing (>0.8) is healthier than lying
        if features['aspect_ratio'] > thresholds['aspect_ratio_healthy']:
            score += weights['aspect_ratio']
        elif features['aspect_ratio'] > thresholds['aspect_ratio_healthy'] * 0.8:
            score += weights['aspect_ratio'] * 0.5  # Partial credit

        # Saturation: vibrant colors indicate good health
        if features['avg_saturation'] > thresholds['saturation_healthy']:
            score += weights['saturation']
        elif features['avg_saturation'] > thresholds['saturation_healthy'] * 0.7:
            score += weights['saturation'] * 0.5

        # Brightness: good visibility suggests alertness
        if features['avg_brightness'] > thresholds['brightness_healthy']:
            score += weights['brightness']
        elif features['avg_brightness'] > thresholds['brightness_healthy'] * 0.7:
            score += weights['brightness'] * 0.5

        # Pose alignment: good posture suggests health
        score += weights['pose_alignment'] * features.get('body_alignment', 0.5)

        return min(score, 1.0)


def analyze_chicken(image_path, config=None):
    """
    Convenience function for single image analysis.

    Args:
        image_path: Path to the image file
        config: Optional configuration dict

    Returns:
        tuple: (status, details)
    """
    analyzer = ChickenVisionAnalyzer(config)
    return analyzer.analyze(image_path)


# Main execution for batch processing
if __name__ == "__main__":
    from utils.logging_config import setup_logging
    from data_pipeline import stage_classification

    # Setup logging
    logger = setup_logging()

    # Load config
    config = load_config()

    # Initialize analyzer
    analyzer = ChickenVisionAnalyzer(config)

    # Get input folder
    input_folder = config['paths']['input_images']
    if not os.path.exists(input_folder):
        print(f"ERROR: Input folder '{input_folder}' not found!")
        exit(1)

    # Process all images
    files = os.listdir(input_folder)
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')

    print(f"\nSentio Vision Analysis - Tier 1")
    print(f"Model: {config['vision']['detection_model']}")
    print(f"Pose Estimation: {'Enabled' if config['vision']['use_pose_estimation'] else 'Disabled'}")
    print(f"Files to analyze: {len([f for f in files if f.lower().endswith(image_extensions)])}")
    print("-" * 50)

    for file_name in files:
        if not file_name.lower().endswith(image_extensions):
            continue

        full_path = os.path.join(input_folder, file_name)
        print(f"\nAnalyzing: {file_name}")

        # Run analysis
        status, details = analyzer.analyze(full_path)

        if status is None:
            print(f"  Result: {details.get('error', 'Unknown error')}")
            continue

        # Display results
        print(f"  Detection Confidence: {details['detection_confidence']:.2f}")
        print(f"  Health Score: {details['health_score']:.2f}")
        print(f"  Aspect Ratio: {details['aspect_ratio']:.2f}")
        print(f"  Pose Detected: {details['pose_detected']}")
        print(f"  -> AI Prediction: {status}")

        # Stage for human validation (non-destructive)
        try:
            stage_classification(
                file_path=full_path,
                modality='vision',
                ai_classification=status,
                confidence=details['detection_confidence'],
                features=details
            )
            print(f"  -> Staged for review")
        except Exception as e:
            print(f"  -> Staging failed: {e}")

    print("\n" + "=" * 50)
    print("Analysis complete! Check Data_Bank/Staging for review.")
