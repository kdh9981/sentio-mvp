"""
Sentio MVP - Audio Visualization

Creates waveform and spectrogram visualizations for audio files.
Used by the Streamlit training app to display audio analysis results.

Features:
- Waveform plot with amplitude over time
- Pitch contour overlay (from YIN detection)
- Distress region highlighting based on thresholds
- Interactive matplotlib figures for Streamlit
"""

import numpy as np
from pathlib import Path

# Optional imports with fallback
try:
    import librosa
    import librosa.display
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def create_waveform_figure(audio_path, sample_rate=22050, duration=5.0,
                           pitch_data=None, distress_regions=None,
                           figsize=(12, 4)):
    """
    Create a waveform visualization with optional overlays.

    Args:
        audio_path: Path to the audio file
        sample_rate: Sample rate for loading audio
        duration: Duration to load (seconds)
        pitch_data: Optional dict with pitch information
        distress_regions: Optional list of (start, end) tuples for highlighting
        figsize: Figure size as (width, height)

    Returns:
        matplotlib.figure.Figure: The waveform figure
    """
    if not LIBROSA_AVAILABLE or not MATPLOTLIB_AVAILABLE:
        return None

    # Load audio
    try:
        y, sr = librosa.load(str(audio_path), sr=sample_rate, duration=duration)
    except Exception as e:
        print(f"Error loading audio: {e}")
        return None

    # Create time axis
    time = np.linspace(0, len(y) / sr, len(y))

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot waveform
    ax.plot(time, y, color='#2E86AB', linewidth=0.5, alpha=0.8)
    ax.fill_between(time, y, alpha=0.3, color='#2E86AB')

    # Add distress region highlighting
    if distress_regions:
        for start, end in distress_regions:
            ax.axvspan(start, end, alpha=0.2, color='#E94F37',
                       label='Potential Distress')

    # Style the plot
    ax.set_xlabel('Time (seconds)', fontsize=10)
    ax.set_ylabel('Amplitude', fontsize=10)
    ax.set_title('Audio Waveform', fontsize=12, fontweight='bold')
    ax.set_xlim(0, len(y) / sr)
    ax.grid(True, alpha=0.3)

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    return fig


def create_pitch_figure(audio_path, sample_rate=22050, duration=5.0,
                        distress_threshold=1000, figsize=(12, 3)):
    """
    Create a pitch contour visualization.

    Shows fundamental frequency over time with distress threshold line.

    Args:
        audio_path: Path to the audio file
        sample_rate: Sample rate for loading audio
        duration: Duration to load (seconds)
        distress_threshold: Hz value above which indicates distress
        figsize: Figure size as (width, height)

    Returns:
        matplotlib.figure.Figure: The pitch contour figure
    """
    if not LIBROSA_AVAILABLE or not MATPLOTLIB_AVAILABLE:
        return None

    # Load audio
    try:
        y, sr = librosa.load(str(audio_path), sr=sample_rate, duration=duration)
    except Exception as e:
        print(f"Error loading audio: {e}")
        return None

    # Extract pitch using YIN
    try:
        f0 = librosa.yin(y, fmin=100, fmax=3000, sr=sr)
        times = librosa.times_like(f0, sr=sr)
    except Exception as e:
        print(f"Error extracting pitch: {e}")
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot pitch contour (filter out zeros for clarity)
    valid_mask = f0 > 0
    ax.scatter(times[valid_mask], f0[valid_mask],
               c=f0[valid_mask], cmap='RdYlGn_r',
               vmin=200, vmax=1500, s=10, alpha=0.7)

    # Add distress threshold line
    ax.axhline(y=distress_threshold, color='#E94F37',
               linestyle='--', linewidth=2, label=f'Distress Threshold ({distress_threshold} Hz)')

    # Add normal range shading
    ax.axhspan(300, 800, alpha=0.1, color='#28A745', label='Normal Range (300-800 Hz)')

    # Style the plot
    ax.set_xlabel('Time (seconds)', fontsize=10)
    ax.set_ylabel('Frequency (Hz)', fontsize=10)
    ax.set_title('Pitch Contour (YIN)', fontsize=12, fontweight='bold')
    ax.set_xlim(0, len(y) / sr)
    ax.set_ylim(0, 2000)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    return fig


def create_spectrogram_figure(audio_path, sample_rate=22050, duration=5.0,
                              figsize=(12, 4)):
    """
    Create a mel spectrogram visualization.

    Args:
        audio_path: Path to the audio file
        sample_rate: Sample rate for loading audio
        duration: Duration to load (seconds)
        figsize: Figure size as (width, height)

    Returns:
        matplotlib.figure.Figure: The spectrogram figure
    """
    if not LIBROSA_AVAILABLE or not MATPLOTLIB_AVAILABLE:
        return None

    # Load audio
    try:
        y, sr = librosa.load(str(audio_path), sr=sample_rate, duration=duration)
    except Exception as e:
        print(f"Error loading audio: {e}")
        return None

    # Compute mel spectrogram
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_dB = librosa.power_to_db(S, ref=np.max)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot spectrogram
    img = librosa.display.specshow(S_dB, x_axis='time', y_axis='mel',
                                   sr=sr, fmax=8000, ax=ax, cmap='magma')

    # Add colorbar
    fig.colorbar(img, ax=ax, format='%+2.0f dB', label='Intensity')

    # Style the plot
    ax.set_title('Mel Spectrogram', fontsize=12, fontweight='bold')

    plt.tight_layout()
    return fig


def create_combined_figure(audio_path, sample_rate=22050, duration=5.0,
                           distress_threshold=1000, features=None,
                           figsize=(12, 8)):
    """
    Create a combined visualization with waveform, pitch, and spectrogram.

    Args:
        audio_path: Path to the audio file
        sample_rate: Sample rate for loading audio
        duration: Duration to load (seconds)
        distress_threshold: Hz value above which indicates distress
        features: Optional dict of extracted audio features
        figsize: Figure size as (width, height)

    Returns:
        matplotlib.figure.Figure: The combined figure
    """
    if not LIBROSA_AVAILABLE or not MATPLOTLIB_AVAILABLE:
        return None

    # Load audio once
    try:
        y, sr = librosa.load(str(audio_path), sr=sample_rate, duration=duration)
    except Exception as e:
        print(f"Error loading audio: {e}")
        return None

    # Create figure with 3 subplots
    fig, axes = plt.subplots(3, 1, figsize=figsize, height_ratios=[1, 1, 1.2])

    # --- Waveform ---
    time = np.linspace(0, len(y) / sr, len(y))
    axes[0].plot(time, y, color='#2E86AB', linewidth=0.5, alpha=0.8)
    axes[0].fill_between(time, y, alpha=0.3, color='#2E86AB')
    axes[0].set_ylabel('Amplitude', fontsize=9)
    axes[0].set_title('Waveform', fontsize=10, fontweight='bold')
    axes[0].set_xlim(0, len(y) / sr)
    axes[0].grid(True, alpha=0.3)
    axes[0].spines['top'].set_visible(False)
    axes[0].spines['right'].set_visible(False)

    # --- Pitch Contour ---
    try:
        f0 = librosa.yin(y, fmin=100, fmax=3000, sr=sr)
        times = librosa.times_like(f0, sr=sr)
        valid_mask = f0 > 0
        axes[1].scatter(times[valid_mask], f0[valid_mask],
                        c=f0[valid_mask], cmap='RdYlGn_r',
                        vmin=200, vmax=1500, s=8, alpha=0.7)
        axes[1].axhline(y=distress_threshold, color='#E94F37',
                        linestyle='--', linewidth=1.5)
        axes[1].axhspan(300, 800, alpha=0.1, color='#28A745')
    except Exception:
        axes[1].text(0.5, 0.5, 'Pitch extraction failed',
                     ha='center', va='center', transform=axes[1].transAxes)

    axes[1].set_ylabel('Frequency (Hz)', fontsize=9)
    axes[1].set_title('Pitch Contour', fontsize=10, fontweight='bold')
    axes[1].set_xlim(0, len(y) / sr)
    axes[1].set_ylim(0, 2000)
    axes[1].grid(True, alpha=0.3)
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['right'].set_visible(False)

    # --- Spectrogram ---
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=64, fmax=4000)
    S_dB = librosa.power_to_db(S, ref=np.max)
    librosa.display.specshow(S_dB, x_axis='time', y_axis='mel',
                             sr=sr, fmax=4000, ax=axes[2], cmap='magma')
    axes[2].set_ylabel('Frequency (Hz)', fontsize=9)
    axes[2].set_title('Mel Spectrogram', fontsize=10, fontweight='bold')

    # Add features annotation if provided
    if features:
        info_text = (
            f"Pitch: {features.get('pitch_mean', 0):.0f} Hz | "
            f"Volume: {features.get('volume_mean', 0):.4f} | "
            f"Calls: {features.get('call_count', 0)}"
        )
        fig.text(0.5, 0.02, info_text, ha='center', fontsize=9,
                 style='italic', color='#666666')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08)
    return fig


def get_audio_duration(audio_path, sample_rate=22050):
    """
    Get the duration of an audio file in seconds.

    Args:
        audio_path: Path to the audio file
        sample_rate: Sample rate for loading

    Returns:
        float: Duration in seconds, or 0 if loading fails
    """
    if not LIBROSA_AVAILABLE:
        return 0

    try:
        y, sr = librosa.load(str(audio_path), sr=sample_rate)
        return len(y) / sr
    except Exception:
        return 0
