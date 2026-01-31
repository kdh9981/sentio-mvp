"""
Sentio MVP - Interactive Training Loop

A Streamlit web app for human-in-the-loop training:
1. Display images/audio for review
2. Show AI predictions with confidence scores
3. Collect human feedback (correct/incorrect)
4. Auto-tune thresholds based on feedback patterns
5. Track progress and accuracy statistics

Usage:
    streamlit run training_app.py
"""

import os
import streamlit as st
from pathlib import Path
from datetime import datetime

# Local imports
from chicken_vision import ChickenVisionAnalyzer
from chicken_audio import ChickenAudioAnalyzer
from data_pipeline import (
    stage_classification,
    finalize_classification,
    get_pending_reviews,
    get_statistics,
    get_config
)
from threshold_tuner import ThresholdTuner
from audio_viz import create_combined_figure, MATPLOTLIB_AVAILABLE
from input_helpers import (
    save_uploaded_file,
    save_pasted_image,
    save_recorded_audio,
    get_supported_extensions,
    detect_input_type,
    cleanup_temp_files
)

# Optional: clipboard paste support
try:
    from streamlit_paste_button import paste_image_button
    PASTE_AVAILABLE = True
except ImportError:
    PASTE_AVAILABLE = False
    paste_image_button = None

# Page configuration
st.set_page_config(
    page_title="Sentio Training Loop",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .prediction-healthy {
        color: #28a745;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .prediction-sick {
        color: #dc3545;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'feedback_history' not in st.session_state:
        st.session_state.feedback_history = []
    if 'mode' not in st.session_state:
        st.session_state.mode = 'review'  # 'review' or 'analyze'
    if 'selected_modality' not in st.session_state:
        st.session_state.selected_modality = 'vision'
    if 'analyzers' not in st.session_state:
        st.session_state.analyzers = {}
    if 'tuner' not in st.session_state:
        st.session_state.tuner = ThresholdTuner()
    if 'pending_items' not in st.session_state:
        st.session_state.pending_items = []


def get_analyzer(modality):
    """Get or create analyzer for a modality"""
    if modality not in st.session_state.analyzers:
        if modality == 'vision':
            st.session_state.analyzers['vision'] = ChickenVisionAnalyzer()
        else:
            st.session_state.analyzers['audio'] = ChickenAudioAnalyzer()
    return st.session_state.analyzers[modality]


def get_input_files(modality):
    """Get list of files to analyze from input folders"""
    config = get_config()
    project_root = Path(__file__).parent

    if modality == 'vision':
        folder = project_root / config['paths']['input_images']
        extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    else:
        folder = project_root / config['paths']['input_sounds']
        extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')

    if not folder.exists():
        return []

    files = [
        folder / f for f in os.listdir(folder)
        if f.lower().endswith(extensions)
    ]
    return sorted(files)


def display_sidebar():
    """Display sidebar with mode selection and stats"""
    st.sidebar.markdown("## Sentio Training")

    # Mode selection
    mode = st.sidebar.radio(
        "Mode",
        options=['Review Staged', 'Analyze New'],
        index=0 if st.session_state.mode == 'review' else 1,
        help="Review: Process staged items. Analyze: Process new files from input folders."
    )
    st.session_state.mode = 'review' if mode == 'Review Staged' else 'analyze'

    # Modality selection
    st.sidebar.markdown("---")
    modality = st.sidebar.radio(
        "Modality",
        options=['Vision', 'Audio'],
        index=0 if st.session_state.selected_modality == 'vision' else 1
    )
    st.session_state.selected_modality = modality.lower()

    # Statistics
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Statistics")

    stats = get_statistics()
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Total Staged", stats['total_staged'])
    col2.metric("Pending", stats['pending_review'])

    col3, col4 = st.sidebar.columns(2)
    col3.metric("Validated", stats['validated'])
    col4.metric("Accuracy", f"{stats['accuracy']:.1%}")

    # Session stats
    if st.session_state.feedback_history:
        session_correct = sum(1 for f in st.session_state.feedback_history if f['agrees'])
        session_total = len(st.session_state.feedback_history)
        st.sidebar.markdown("### Session")
        st.sidebar.metric("Session Accuracy", f"{session_correct}/{session_total}")

    # Threshold tuning info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Threshold Tuning")

    tuner = st.session_state.tuner
    for mod in ['vision', 'audio']:
        current, suggested, samples = tuner.get_suggested_threshold(mod)
        if suggested and abs(suggested - current) > 0.01:
            st.sidebar.warning(
                f"**{mod.title()}**: {current:.2f} → {suggested:.2f} "
                f"(based on {samples} samples)"
            )
            if st.sidebar.button(f"Apply {mod.title()} Threshold", key=f"apply_{mod}"):
                if tuner.apply_threshold_update(mod):
                    st.sidebar.success("Threshold updated!")
                    st.rerun()


def display_review_mode():
    """Display the review mode UI for staged items"""
    st.markdown('<p class="main-header">Review Staged Items</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Validate AI predictions and improve accuracy</p>',
                unsafe_allow_html=True)

    # Get pending reviews
    pending = get_pending_reviews()
    modality = st.session_state.selected_modality

    # Filter by modality
    pending = [p for p in pending if p['modality'] == modality]
    st.session_state.pending_items = pending

    if not pending:
        st.info(f"No {modality} items pending review. Try 'Analyze New' mode to process input files.")
        return

    # Current item
    idx = st.session_state.current_index
    if idx >= len(pending):
        st.session_state.current_index = 0
        idx = 0

    item = pending[idx]

    # Progress bar
    progress = (idx + 1) / len(pending)
    st.progress(progress)
    st.markdown(f"**Item {idx + 1} of {len(pending)}**")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Display the file
        config = get_config()
        project_root = Path(__file__).parent
        staging_folder = project_root / config['paths']['staging_folder']
        file_path = staging_folder / item['staged_file']

        if modality == 'vision':
            if file_path.exists():
                st.image(str(file_path), caption=item['original_file'], use_container_width=True)
            else:
                st.error(f"File not found: {file_path}")
        else:
            # Audio display
            if file_path.exists():
                st.audio(str(file_path))

                # Show visualization
                if MATPLOTLIB_AVAILABLE:
                    features = item.get('features', {})
                    fig = create_combined_figure(
                        file_path,
                        features=features if isinstance(features, dict) else {}
                    )
                    if fig:
                        st.pyplot(fig)
            else:
                st.error(f"File not found: {file_path}")

    with col2:
        # AI Prediction
        st.markdown("### AI Prediction")

        prediction = item['ai_classification']
        confidence = float(item['confidence'])

        # Color-coded prediction
        if prediction in ('HEALTHY', 'NORMAL'):
            st.markdown(f'<p class="prediction-healthy">{prediction}</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="prediction-sick">{prediction}</p>',
                        unsafe_allow_html=True)

        # Confidence meter
        st.metric("Confidence", f"{confidence:.1%}")

        # Key features
        st.markdown("### Key Features")
        features = item.get('features', {})
        if isinstance(features, dict):
            if modality == 'vision':
                st.write(f"- Health Score: {features.get('health_score', 'N/A')}")
                st.write(f"- Aspect Ratio: {features.get('aspect_ratio', 'N/A')}")
                st.write(f"- Pose Detected: {features.get('pose_detected', 'N/A')}")
            else:
                st.write(f"- Distress Score: {features.get('distress_score', 'N/A')}")
                st.write(f"- Pitch: {features.get('pitch_mean', 0):.0f} Hz")
                st.write(f"- Volume: {features.get('volume_mean', 0):.4f}")
                st.write(f"- Call Rate: {features.get('call_rate', 0):.1f}/sec")

        # Feedback buttons
        st.markdown("---")
        st.markdown("### Your Feedback")

        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("✓ Correct", type="primary", key="btn_correct"):
                handle_feedback(item, agrees=True)

        with col_no:
            if st.button("✗ Incorrect", type="secondary", key="btn_incorrect"):
                handle_feedback(item, agrees=False)

        # Skip button
        if st.button("Skip →", key="btn_skip"):
            st.session_state.current_index = (idx + 1) % len(pending)
            st.rerun()


def display_analyze_mode():
    """Display the analyze mode UI for new files with multiple input methods"""
    st.markdown('<p class="main-header">Analyze New Files</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Upload, paste, record, or select from folder</p>',
                unsafe_allow_html=True)

    modality = st.session_state.selected_modality

    # Clean up old temp files periodically
    cleanup_temp_files(max_age_hours=24)

    # Initialize input tracking in session state
    if 'current_input_file' not in st.session_state:
        st.session_state.current_input_file = None
    if 'current_input_source' not in st.session_state:
        st.session_state.current_input_source = None

    # --- Input Methods Section ---
    st.markdown("### Choose Input Method")

    # Create tabs for different input methods based on modality
    if modality == 'vision':
        tab_upload, tab_paste, tab_folder = st.tabs([
            "Upload Image",
            "Paste from Clipboard",
            "Browse Folder"
        ])
    else:
        tab_upload, tab_record, tab_folder = st.tabs([
            "Upload Audio",
            "Record Microphone",
            "Browse Folder"
        ])

    selected_file = None
    input_source = None

    # --- Tab 1: File Upload (both modalities) ---
    with tab_upload:
        extensions = get_supported_extensions(modality)
        # Convert extensions for file_uploader (remove dots)
        upload_types = [ext.lstrip('.') for ext in extensions]

        uploaded_file = st.file_uploader(
            f"Drop {'image' if modality == 'vision' else 'audio'} file here",
            type=upload_types,
            key=f"upload_{modality}"
        )

        if uploaded_file is not None:
            file_path, detected_modality = save_uploaded_file(uploaded_file)
            if file_path and detected_modality == modality:
                selected_file = file_path
                input_source = 'upload'
                st.success(f"File loaded: {uploaded_file.name}")

    # --- Tab 2: Modality-specific input ---
    if modality == 'vision':
        # Clipboard paste for images
        with tab_paste:
            if PASTE_AVAILABLE:
                st.info("Click the button below, then paste an image (Cmd+V / Ctrl+V)")
                paste_result = paste_image_button(
                    label="Paste Image from Clipboard",
                    key="paste_image"
                )
                if paste_result.image_data is not None:
                    file_path, _ = save_pasted_image(paste_result.image_data)
                    if file_path:
                        selected_file = file_path
                        input_source = 'paste'
                        st.success("Image pasted successfully!")
            else:
                st.warning(
                    "Clipboard paste not available. "
                    "Install with: `pip install streamlit-paste-button`"
                )
    else:
        # Microphone recording for audio
        with tab_record:
            st.info("Click to start recording. Click again to stop.")
            audio_bytes = st.audio_input(
                "Record chicken sounds",
                key="mic_recording"
            )
            if audio_bytes is not None:
                file_path, _ = save_recorded_audio(audio_bytes)
                if file_path:
                    selected_file = file_path
                    input_source = 'recording'
                    st.success("Recording saved!")

    # --- Tab 3: Browse folder (both modalities) ---
    with tab_folder:
        files = get_input_files(modality)
        if files:
            folder_file = st.selectbox(
                "Select a file to analyze",
                options=files,
                format_func=lambda x: x.name,
                key=f"folder_{modality}"
            )
            if folder_file:
                selected_file = folder_file
                input_source = 'folder'
        else:
            config = get_config()
            folder = config['paths']['input_images'] if modality == 'vision' else config['paths']['input_sounds']
            st.info(f"No files in '{folder}'. Use upload or {'paste' if modality == 'vision' else 'record'} instead.")

    # Update session state with current input
    if selected_file is not None:
        st.session_state.current_input_file = selected_file
        st.session_state.current_input_source = input_source

    # --- Display and Analyze Section ---
    if st.session_state.current_input_file is not None:
        selected_file = st.session_state.current_input_file

        st.markdown("---")
        col1, col2 = st.columns([2, 1])

        with col1:
            if modality == 'vision':
                st.image(str(selected_file), caption=Path(selected_file).name, use_container_width=True)
            else:
                st.audio(str(selected_file))

        with col2:
            if st.button("Analyze", type="primary", key="btn_analyze"):
                with st.spinner("Analyzing..."):
                    analyzer = get_analyzer(modality)
                    status, details = analyzer.analyze(selected_file)

                    if status:
                        st.session_state.last_analysis = {
                            'file': selected_file,
                            'status': status,
                            'details': details,
                            'modality': modality
                        }
                    else:
                        st.error(f"Analysis failed: {details.get('error', 'Unknown error')}")

        # Display analysis results
        if 'last_analysis' in st.session_state:
            analysis = st.session_state.last_analysis

            if str(analysis['file']) == str(selected_file):
                st.markdown("---")
                st.markdown("### Analysis Results")

                status = analysis['status']
                details = analysis['details']

                # Prediction with color
                if status in ('HEALTHY', 'NORMAL'):
                    st.success(f"**Prediction: {status}**")
                else:
                    st.error(f"**Prediction: {status}**")

                # Score metric
                if modality == 'vision':
                    score = details.get('health_score', 0)
                    st.metric("Health Score", f"{score:.2f}")
                else:
                    score = details.get('distress_score', 0)
                    st.metric("Distress Score", f"{score:.2f}")

                # Audio visualization
                if modality == 'audio' and MATPLOTLIB_AVAILABLE:
                    fig = create_combined_figure(selected_file, features=details)
                    if fig:
                        st.pyplot(fig)

                # Stage for review buttons
                st.markdown("---")
                col_stage, col_skip = st.columns(2)

                with col_stage:
                    if st.button("Stage for Review", type="primary", key="btn_stage"):
                        stage_classification(
                            file_path=selected_file,
                            modality=modality,
                            ai_classification=status,
                            confidence=score,
                            features=details
                        )
                        st.success("Staged! Switch to 'Review Staged' mode to validate.")
                        # Clear current input after staging
                        st.session_state.current_input_file = None
                        st.session_state.current_input_source = None

                with col_skip:
                    if st.button("Skip (Don't Stage)", key="btn_skip_analyze"):
                        del st.session_state.last_analysis
                        st.session_state.current_input_file = None
                        st.session_state.current_input_source = None
                        st.rerun()


def handle_feedback(item, agrees):
    """Handle user feedback on a prediction"""
    # Finalize the classification
    finalize_classification(
        staged_file=item['staged_file'],
        human_agrees=agrees
    )

    # Record for threshold tuning
    tuner = st.session_state.tuner
    features = item.get('features', {})

    if item['modality'] == 'vision':
        score = features.get('health_score', 0.5) if isinstance(features, dict) else 0.5
    else:
        score = features.get('distress_score', 0.5) if isinstance(features, dict) else 0.5

    tuner.record_feedback(
        modality=item['modality'],
        score=score,
        ai_prediction=item['ai_classification'],
        human_agrees=agrees
    )

    # Track in session
    st.session_state.feedback_history.append({
        'file': item['original_file'],
        'agrees': agrees,
        'prediction': item['ai_classification'],
        'timestamp': datetime.now().isoformat()
    })

    # Move to next item
    pending = st.session_state.pending_items
    if pending:
        st.session_state.current_index = st.session_state.current_index % max(len(pending) - 1, 1)

    st.rerun()


def main():
    """Main application entry point"""
    init_session_state()
    display_sidebar()

    if st.session_state.mode == 'review':
        display_review_mode()
    else:
        display_analyze_mode()


if __name__ == "__main__":
    main()
