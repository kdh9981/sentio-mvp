"""
Sentio MVP - Chicken Audio Analysis
Tier 1: BirdNET-Lite + YIN Pitch + MFCC + Call Pattern Detection

Upgrades from baseline:
- BirdNET-Lite: 85-90% accuracy on vocalizations, 6.5 MB model
- YIN pitch detection: Real fundamental frequency (not spectral centroid)
- MFCC features: Voice characteristics for classification
- Onset detection: Call patterns and frequency
- Multi-feature distress scoring
"""

import os
import numpy as np
import yaml
import logging
from pathlib import Path

# Optional imports with fallback
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("Warning: librosa not installed. Run: pip install librosa")

try:
    from birdnetlib import Recording
    from birdnetlib.analyzer import Analyzer
    BIRDNET_AVAILABLE = True
except ImportError:
    BIRDNET_AVAILABLE = False
    print("Warning: birdnetlib not installed. Run: pip install birdnetlib")


# Load configuration
def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    config_file = Path(__file__).parent / config_path
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


class ChickenAudioAnalyzer:
    """Multi-feature chicken audio analysis using BirdNET + librosa"""

    def __init__(self, config=None):
        """Initialize the analyzer with configuration"""
        self.config = config or load_config()
        self.audio_config = self.config['audio']
        self.logger = logging.getLogger('sentio.audio')

        # Initialize BirdNET analyzer
        self.birdnet_analyzer = None
        if BIRDNET_AVAILABLE and self.audio_config['use_birdnet']:
            try:
                self.birdnet_analyzer = Analyzer()
                self.logger.info("Initialized BirdNET analyzer")
            except Exception as e:
                self.logger.warning(f"Failed to initialize BirdNET: {e}")

    def analyze(self, audio_path):
        """
        Analyze a chicken audio file for distress indicators.

        Args:
            audio_path: Path to the audio file

        Returns:
            tuple: (status, details) where status is 'DISTRESS', 'NORMAL', or None
        """
        if not LIBROSA_AVAILABLE:
            return None, {"error": "librosa not available"}

        # Load audio
        try:
            y, sr = librosa.load(
                str(audio_path),
                sr=self.audio_config['sample_rate'],
                duration=self.audio_config['duration_seconds']
            )
        except Exception as e:
            return None, {"error": f"Cannot load audio: {e}"}

        if len(y) == 0:
            return None, {"error": "Audio file is empty"}

        # Extract features
        features = self._extract_audio_features(y, sr)

        # BirdNET analysis
        birdnet_result = None
        if self.birdnet_analyzer:
            birdnet_result = self._analyze_with_birdnet(str(audio_path))
            features['birdnet'] = birdnet_result

        # Calculate distress score
        distress_score = self._calculate_distress_score(features, birdnet_result)
        features['distress_score'] = distress_score

        # Determine status
        threshold = self.audio_config['thresholds']['distress_score_threshold']
        status = "DISTRESS" if distress_score > threshold else "NORMAL"

        self.logger.info(f"Analysis complete: {status} (score: {distress_score:.2f})")
        return status, features

    def _extract_audio_features(self, y, sr):
        """
        Extract comprehensive audio features using librosa.

        Features extracted:
        - YIN pitch: Real fundamental frequency (Hz)
        - Volume: RMS energy (mean and variance)
        - MFCC: Voice characteristics (13 coefficients)
        - Onset detection: Call count and rate
        - Zero-crossing rate: Sound regularity
        - Spectral rolloff: Frequency distribution
        """
        features = {}
        duration = len(y) / sr

        # 1. YIN pitch detection (REAL pitch, not spectral centroid!)
        # YIN is more accurate for monophonic sources like bird calls
        try:
            f0 = librosa.yin(y, fmin=100, fmax=3000, sr=sr)
            valid_f0 = f0[f0 > 0]  # Filter out unvoiced segments

            if len(valid_f0) > 0:
                features['pitch_mean'] = float(np.median(valid_f0))
                features['pitch_std'] = float(np.std(valid_f0))
                features['pitch_min'] = float(np.min(valid_f0))
                features['pitch_max'] = float(np.max(valid_f0))
            else:
                features['pitch_mean'] = 0
                features['pitch_std'] = 0
                features['pitch_min'] = 0
                features['pitch_max'] = 0
        except Exception as e:
            self.logger.warning(f"YIN pitch detection failed: {e}")
            features['pitch_mean'] = 0
            features['pitch_std'] = 0

        # 2. Volume (RMS energy)
        rms = librosa.feature.rms(y=y)[0]
        features['volume_mean'] = float(np.mean(rms))
        features['volume_std'] = float(np.std(rms))
        features['volume_max'] = float(np.max(rms))

        # 3. MFCC (voice characteristics) - 13 coefficients
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features['mfcc_mean'] = np.mean(mfcc, axis=1).tolist()
        features['mfcc_std'] = np.std(mfcc, axis=1).tolist()

        # 4. Onset detection (call patterns)
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='frames')
        features['call_count'] = len(onsets)
        features['call_rate'] = len(onsets) / duration if duration > 0 else 0

        # 5. Zero-crossing rate (sound regularity)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        features['zcr_mean'] = float(np.mean(zcr))
        features['zcr_std'] = float(np.std(zcr))

        # 6. Spectral rolloff (frequency distribution)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        features['rolloff_mean'] = float(np.mean(rolloff))

        # 7. Spectral centroid (for comparison with baseline)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        features['spectral_centroid'] = float(np.mean(centroid))

        features['duration'] = duration
        features['sample_rate'] = sr

        return features

    def _analyze_with_birdnet(self, audio_path):
        """
        Use BirdNET for species/call classification.

        Looks for distress-related keywords in detected species.
        """
        try:
            recording = Recording(
                self.birdnet_analyzer,
                audio_path,
                min_conf=0.3
            )
            recording.analyze()

            # Keywords that might indicate distress calls
            distress_keywords = ['alarm', 'distress', 'call', 'scream', 'squawk']

            result = {
                'detected': len(recording.detections) > 0,
                'detections': [],
                'is_distress': False,
                'top_confidence': 0.0
            }

            for detection in recording.detections:
                species = detection.get('common_name', '').lower()
                confidence = detection.get('confidence', 0)

                result['detections'].append({
                    'species': detection.get('common_name', 'Unknown'),
                    'scientific_name': detection.get('scientific_name', ''),
                    'confidence': confidence
                })

                if confidence > result['top_confidence']:
                    result['top_confidence'] = confidence

                # Check if it's a distress-related call
                if any(kw in species for kw in distress_keywords):
                    result['is_distress'] = True

            return result

        except Exception as e:
            self.logger.warning(f"BirdNET analysis failed: {e}")
            return {'error': str(e), 'detected': False, 'is_distress': False}

    def _calculate_distress_score(self, features, birdnet_result):
        """
        Combine features into a distress score (0-1).

        Higher score = more likely distress.

        Chicken vocalizations:
        - Normal: 300-800 Hz
        - Distress/alarm: 1000-2000 Hz
        """
        thresholds = self.audio_config['thresholds']
        score = 0.0

        # 1. Pitch analysis (most important indicator)
        # High pitch strongly indicates distress
        pitch = features.get('pitch_mean', 0)
        if pitch > thresholds['pitch_distress_high']:
            score += 0.25  # Clear distress
        elif pitch > thresholds['pitch_distress_medium']:
            score += 0.15  # Possible distress

        # Pitch variance also indicates irregular calling
        if features.get('pitch_std', 0) > 200:
            score += 0.05

        # 2. Volume analysis
        volume = features.get('volume_mean', 0)
        if volume > thresholds['volume_high']:
            score += 0.20  # Very loud = likely distress
        elif volume > thresholds['volume_medium']:
            score += 0.10  # Elevated volume

        # Volume variance indicates irregular calling patterns
        if features.get('volume_std', 0) > thresholds['volume_variance_high']:
            score += 0.15

        # 3. Call rate (rapid calling = distress)
        call_rate = features.get('call_rate', 0)
        if call_rate > thresholds['call_rate_high']:
            score += 0.20  # Very rapid
        elif call_rate > thresholds['call_rate_medium']:
            score += 0.10  # Elevated

        # 4. Zero-crossing rate (harsh/irregular sounds)
        if features.get('zcr_mean', 0) > thresholds['zcr_high']:
            score += 0.10

        # 5. BirdNET distress detection (bonus)
        if birdnet_result and birdnet_result.get('is_distress'):
            score += 0.30

        return min(score, 1.0)


def analyze_chicken_audio(audio_path, config=None):
    """
    Convenience function for single audio analysis.

    Args:
        audio_path: Path to the audio file
        config: Optional configuration dict

    Returns:
        tuple: (status, details)
    """
    analyzer = ChickenAudioAnalyzer(config)
    return analyzer.analyze(audio_path)


# Main execution for batch processing
if __name__ == "__main__":
    from utils.logging_config import setup_logging
    from data_pipeline import stage_classification

    # Setup logging
    logger = setup_logging()

    # Load config
    config = load_config()

    # Initialize analyzer
    analyzer = ChickenAudioAnalyzer(config)

    # Get input folder
    input_folder = config['paths']['input_sounds']
    if not os.path.exists(input_folder):
        print(f"ERROR: Input folder '{input_folder}' not found!")
        exit(1)

    # Process all audio files
    files = os.listdir(input_folder)
    audio_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')

    print(f"\nSentio Audio Analysis - Tier 1")
    print(f"BirdNET: {'Enabled' if config['audio']['use_birdnet'] else 'Disabled'}")
    print(f"Duration: {config['audio']['duration_seconds']}s per file")
    print(f"Files to analyze: {len([f for f in files if f.lower().endswith(audio_extensions)])}")
    print("-" * 50)

    for file_name in files:
        if not file_name.lower().endswith(audio_extensions):
            continue

        full_path = os.path.join(input_folder, file_name)
        print(f"\nAnalyzing: {file_name}")

        # Run analysis
        status, details = analyzer.analyze(full_path)

        if status is None:
            print(f"  Result: {details.get('error', 'Unknown error')}")
            continue

        # Display results
        print(f"  Distress Score: {details['distress_score']:.2f}")
        print(f"  Pitch (YIN): {details['pitch_mean']:.0f} Hz")
        print(f"  Volume: {details['volume_mean']:.4f}")
        print(f"  Call Rate: {details['call_rate']:.1f} calls/sec")

        if 'birdnet' in details and details['birdnet'].get('detected'):
            print(f"  BirdNET: {len(details['birdnet']['detections'])} detections")
            for det in details['birdnet']['detections'][:3]:  # Top 3
                print(f"    - {det['species']}: {det['confidence']:.2f}")

        print(f"  -> AI Prediction: {status}")

        # Stage for human validation (non-destructive)
        try:
            stage_classification(
                file_path=full_path,
                modality='audio',
                ai_classification=status,
                confidence=details['distress_score'],
                features=details
            )
            print(f"  -> Staged for review")
        except Exception as e:
            print(f"  -> Staging failed: {e}")

    print("\n" + "=" * 50)
    print("Analysis complete! Check Data_Bank/Staging for review.")
