"""
Sentio MVP - Interactive Training Loop v2

A visually distinctive, production-grade training interface with:
- Agricultural Data Observatory aesthetic
- Animated data flow pipeline visualization
- Comprehensive tooltip system
- Real-time activity logging
- Three-panel layout for maximum clarity

Design: "Farm Tech Mission Control" - NASA meets organic farming
Typography: Playfair Display + DM Sans + JetBrains Mono
Color: Bold greens/reds with warm amber on deep dark background

Usage:
    streamlit run training_app_v2.py
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
    cleanup_temp_files
)
from reference_database import get_reference_database

# Component imports
from components.theme import apply_theme
from components.tooltips import get_tooltip, get_how_it_works
from components.data_flow import (
    render_data_flow_header,
    render_file_location,
    render_feedback_panel,
    render_learning_status,
    render_activity_log,
    add_activity
)

# Optional: clipboard paste support
try:
    from streamlit_paste_button import paste_image_button
    PASTE_AVAILABLE = True
except ImportError:
    PASTE_AVAILABLE = False
    paste_image_button = None


def render_html(html_content):
    """Render HTML using the best available method for current Streamlit version."""
    if hasattr(st, 'html'):
        st.html(html_content)
    else:
        st.markdown(html_content, unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="Sentio Training Observatory",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Theme is applied in main() after session state is initialized


def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'current_index': 0,
        'feedback_history': [],
        'mode': 'analyze',  # 'review' or 'analyze'
        'selected_modality': 'vision',
        'analyzers': {},
        'tuner': ThresholdTuner(),
        'pending_items': [],
        'current_input_file': None,
        'current_input_source': None,
        'last_analysis': None,
        'activity_log': [],
        'current_stage': 'input',  # For pipeline visualization
        'is_analyzing': False,  # For AI loading spinner
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


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


def render_header():
    """Render the main observatory header"""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <h1 class="observatory-header">
            Sentio
        </h1>
        <p class="observatory-subtitle">
            Chicken Health Observatory · Human-in-the-Loop Training
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_left_panel():
    """Render the left navigation panel with mode selection and stats"""
    st.markdown("""
    <div style="font-family: var(--font-display); font-size: 1rem; font-weight: 600;
                color: var(--text-primary); margin-bottom: 1rem;">
        Control Panel
    </div>
    """, unsafe_allow_html=True)

    # Mode selection
    st.markdown("##### Mode")
    mode = st.radio(
        "Operation Mode",
        options=['Analyze New', 'Review Staged'],
        index=0 if st.session_state.mode == 'analyze' else 1,
        help=get_tooltip('mode_review') if st.session_state.mode == 'review' else get_tooltip('mode_analyze'),
        label_visibility="collapsed"
    )
    # Detect mode change to reset stage appropriately
    old_mode = st.session_state.mode
    new_mode = 'analyze' if mode == 'Analyze New' else 'review'

    if old_mode != new_mode:
        # Mode changed - reset stage to appropriate starting point
        st.session_state.mode = new_mode
        if new_mode == 'review':
            st.session_state.current_stage = 'review'
        else:
            st.session_state.current_stage = 'input'
    else:
        st.session_state.mode = new_mode
        # Don't override current_stage - let workflow logic control it

    st.markdown("---")

    # Modality selection
    st.markdown("##### Modality")
    modality = st.radio(
        "Input Type",
        options=['Vision', 'Audio'],
        index=0 if st.session_state.selected_modality == 'vision' else 1,
        help=get_tooltip('modality_vision') if st.session_state.selected_modality == 'vision' else get_tooltip('modality_audio'),
        label_visibility="collapsed"
    )
    st.session_state.selected_modality = modality.lower()

    st.markdown("---")

    # Statistics
    st.markdown("##### Pipeline Stats")
    stats = get_statistics()

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Staged",
            stats['total_staged'],
            help=get_tooltip('stat_total_staged')
        )
    with col2:
        st.metric(
            "Pending",
            stats['pending_review'],
            help=get_tooltip('stat_pending')
        )

    col3, col4 = st.columns(2)
    with col3:
        st.metric(
            "Validated",
            stats['validated'],
            help=get_tooltip('stat_validated')
        )
    with col4:
        accuracy_display = f"{stats['accuracy']:.0%}"
        st.metric(
            "Accuracy",
            accuracy_display,
            help=get_tooltip('accuracy')
        )

    # Session accuracy
    if st.session_state.feedback_history:
        st.markdown("---")
        st.markdown("##### This Session")
        session_correct = sum(1 for f in st.session_state.feedback_history if f['agrees'])
        session_total = len(st.session_state.feedback_history)
        st.metric(
            "Session Score",
            f"{session_correct}/{session_total}",
            help=get_tooltip('stat_session_accuracy')
        )

    # Reference database status
    st.markdown("---")
    st.markdown("##### Reference Learning")
    ref_db = get_reference_database()
    ref_stats = ref_db.get_statistics()

    col_h, col_s = st.columns(2)
    with col_h:
        st.metric(
            "Healthy",
            ref_stats['healthy_samples'],
            help="Verified healthy samples in reference database"
        )
    with col_s:
        st.metric(
            "Sick",
            ref_stats['sick_samples'],
            help="Verified sick samples in reference database"
        )

    # Status indicator
    if ref_stats['is_active']:
        st.success(f"Active", icon="✓")
    else:
        st.info(ref_stats['status_message'], icon="ℹ️")


def render_right_panel():
    """Render the right context panel with file location and activity log"""
    # File location indicator
    modality = st.session_state.selected_modality
    if st.session_state.mode == 'review':
        pending = st.session_state.pending_items
        idx = st.session_state.current_index
        if pending and idx < len(pending):
            item = pending[idx]
            config = get_config()
            staging_folder = config['paths']['staging_folder']
            file_path = f"{staging_folder}/{item['staged_file']}"
            prediction = item['ai_classification']
            item_modality = item.get('modality', modality)
            render_file_location(st, file_path, prediction, item_modality)
        else:
            render_file_location(st, None, None)
    elif st.session_state.current_input_file:
        prediction = None
        if st.session_state.last_analysis:
            prediction = st.session_state.last_analysis.get('status')
        render_file_location(st, str(st.session_state.current_input_file), prediction, modality)
    else:
        render_file_location(st, None, None)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Feedback loop status
    tuner = st.session_state.tuner
    modality = st.session_state.selected_modality
    current, suggested, samples = tuner.get_suggested_threshold(modality)

    tuner_data = {
        'current': current or 0.5,
        'suggested': suggested,
        'samples': samples,
    }

    stats = get_statistics()

    # Learning status indicator (compact view of how feedback improves AI)
    render_learning_status(st, tuner_data, stats)

    # Detailed feedback panel with threshold suggestions
    render_feedback_panel(st, tuner_data, stats)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Activity log
    render_activity_log(st, st.session_state.activity_log)

    # Threshold application button
    if suggested and samples >= 10 and abs(suggested - current) > 0.01:
        if st.button(
            f"Apply {suggested:.2f} Threshold",
            type="primary",
            help=get_tooltip('apply_threshold'),
            use_container_width=True
        ):
            if tuner.apply_threshold_update(modality):
                add_activity(
                    st.session_state,
                    '',
                    f"Threshold updated to {suggested:.2f}",
                    f"{modality.title()} detection"
                )
                st.success("Threshold applied!")
                st.rerun()


def render_review_mode():
    """Render the review mode UI for staged items"""
    # Get pending reviews
    pending = get_pending_reviews()
    modality = st.session_state.selected_modality

    # Filter by modality
    pending = [p for p in pending if p['modality'] == modality]
    st.session_state.pending_items = pending

    if not pending:
        st.info(
            f"📂 No {modality} items pending review. "
            f"Switch to 'Analyze New' mode to process files."
        )

        # Show how it works
        with st.expander("ℹ️ Review Mode"):
            section = get_how_it_works('data_flow')
            st.markdown(section['content'])
        return

    # Current item
    idx = st.session_state.current_index
    if idx >= len(pending):
        st.session_state.current_index = 0
        idx = 0

    item = pending[idx]
    # Only set review stage if not already at verified (preserves verified highlight briefly)
    if st.session_state.current_stage not in ('verified',):
        st.session_state.current_stage = 'review'

    # Progress bar
    progress = (idx + 1) / len(pending)
    st.progress(progress, text=f"Reviewing {idx + 1} of {len(pending)}")

    # Two-column layout for content
    col_content, col_prediction = st.columns([2, 1])

    with col_content:
        # Display the file
        config = get_config()
        project_root = Path(__file__).parent
        staging_folder = project_root / config['paths']['staging_folder']
        file_path = staging_folder / item['staged_file']

        if modality == 'vision':
            if file_path.exists():
                st.image(
                    str(file_path),
                    caption=item['original_file'],
                    use_container_width=True
                )
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

    with col_prediction:
        # AI Prediction card
        prediction = item['ai_classification']
        confidence = float(item['confidence'])

        # Prediction display
        st.markdown("##### AI Prediction")

        if prediction in ('HEALTHY', 'NORMAL'):
            st.markdown(
                f'<div class="prediction-healthy">{prediction}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="prediction-sick">{prediction}</div>',
                unsafe_allow_html=True
            )

        st.metric("Confidence", f"{confidence:.1%}", help=get_tooltip('confidence'))

        # Key features
        st.markdown("##### Key Features")
        features = item.get('features', {})
        if isinstance(features, dict):
            if modality == 'vision':
                health_score = features.get('health_score', 'N/A')
                if isinstance(health_score, (int, float)):
                    st.metric("Health Score", f"{health_score:.2f}", help=get_tooltip('health_score'))
                else:
                    st.write(f"Health Score: {health_score}")

                # Show reference adjustment if used
                ref_details = features.get('reference_details', {})
                if ref_details.get('reference_used'):
                    ref_adj = features.get('reference_adjustment', 0)
                    base_score = features.get('base_health_score', health_score)
                    adj_sign = "+" if ref_adj >= 0 else ""
                    st.caption(
                        f"Base: {base_score:.2f} {adj_sign}{ref_adj:.2f} (ref)"
                    )
            else:
                distress_score = features.get('distress_score', 'N/A')
                if isinstance(distress_score, (int, float)):
                    st.metric("Distress Score", f"{distress_score:.2f}", help=get_tooltip('distress_score'))
                else:
                    st.write(f"Distress Score: {distress_score}")

                pitch = features.get('pitch_mean', 0)
                volume = features.get('volume_mean', 0)
                call_rate = features.get('call_rate', 0)
                st.write(f"🎵 Pitch: {pitch:.0f} Hz")
                st.write(f"📢 Volume: {volume:.4f}")
                st.write(f"📊 Call Rate: {call_rate:.1f}/sec")

        st.markdown("---")

        # Feedback buttons
        st.markdown("##### Your Verdict")

        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button(
                "✓ Correct",
                type="primary",
                key="btn_correct",
                help=get_tooltip('correct_button'),
                use_container_width=True
            ):
                handle_feedback(item, agrees=True)

        with col_no:
            if st.button(
                "✗ Wrong",
                type="secondary",
                key="btn_incorrect",
                help=get_tooltip('incorrect_button'),
                use_container_width=True
            ):
                handle_feedback(item, agrees=False)

        # Skip button
        if st.button(
            "Skip",
            key="btn_skip",
            help=get_tooltip('skip_button'),
            use_container_width=True
        ):
            st.session_state.current_index = (idx + 1) % len(pending)
            add_activity(st.session_state, '', f"Skipped {item['original_file']}")
            st.rerun()


def render_analyze_mode():
    """Render the analyze mode UI for new files with multiple input methods"""
    modality = st.session_state.selected_modality
    # Only reset to input if we don't have a file or analysis in progress
    if not st.session_state.current_input_file and not st.session_state.last_analysis:
        st.session_state.current_stage = 'input'

    # Clean up old temp files periodically
    cleanup_temp_files(max_age_hours=24)

    # Input method tabs
    if modality == 'vision':
        tab_upload, tab_paste, tab_folder = st.tabs([
            "📤 Upload Image",
            "📋 Paste Clipboard",
            "📁 Browse Folder"
        ])
    else:
        tab_upload, tab_record, tab_folder = st.tabs([
            "📤 Upload Audio",
            "🎤 Record Microphone",
            "📁 Browse Folder"
        ])

    selected_file = None
    input_source = None

    # Tab 1: File Upload
    with tab_upload:
        extensions = get_supported_extensions(modality)
        upload_types = [ext.lstrip('.') for ext in extensions]

        uploaded_file = st.file_uploader(
            f"Drop {'image' if modality == 'vision' else 'audio'} file here",
            type=upload_types,
            key=f"upload_{modality}",
            help=get_tooltip('input_upload')
        )

        if uploaded_file is not None:
            file_path, detected_modality = save_uploaded_file(uploaded_file)
            if file_path and detected_modality == modality:
                selected_file = file_path
                input_source = 'upload'
                st.success(f"Loaded: {uploaded_file.name}")
                add_activity(st.session_state, '', f"Uploaded {uploaded_file.name}")

    # Tab 2: Modality-specific input
    if modality == 'vision':
        with tab_paste:
            if PASTE_AVAILABLE:
                st.info("Click below, then paste an image (Cmd+V / Ctrl+V)")
                paste_result = paste_image_button(
                    label="📋 Paste Image",
                    key="paste_image"
                )
                if paste_result.image_data is not None:
                    # Only save if we don't already have a file from paste
                    # This prevents re-saving on rerun which would create a new file path
                    # and break the confirm button comparison (last_analysis['file'] != current_input_file)
                    if st.session_state.get('current_input_source') != 'paste' or st.session_state.get('current_input_file') is None:
                        file_path, _ = save_pasted_image(paste_result.image_data)
                        if file_path:
                            selected_file = file_path
                            input_source = 'paste'
                            st.success("Image pasted!")
                            add_activity(st.session_state, '', "Pasted image from clipboard")
            else:
                st.warning(
                    "Clipboard paste requires: `pip install streamlit-paste-button`"
                )
    else:
        with tab_record:
            st.info("Click to start recording, click again to stop.")
            audio_bytes = st.audio_input(
                "Record chicken sounds",
                key="mic_recording",
                help=get_tooltip('input_record')
            )
            if audio_bytes is not None:
                file_path, _ = save_recorded_audio(audio_bytes)
                if file_path:
                    selected_file = file_path
                    input_source = 'recording'
                    st.success("Recording saved!")
                    add_activity(st.session_state, '', "Recorded audio")

    # Tab 3: Browse folder
    with tab_folder:
        files = get_input_files(modality)
        if files:
            folder_file = st.selectbox(
                "Select a file to analyze",
                options=files,
                format_func=lambda x: x.name,
                key=f"folder_{modality}",
                help=get_tooltip('input_folder')
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
        st.session_state.current_stage = 'ai'

    # Display and Analyze Section
    if st.session_state.current_input_file is not None:
        selected_file = st.session_state.current_input_file

        # Check if file still exists (temp files may be deleted between sessions)
        if not Path(selected_file).exists():
            st.warning("Previously selected file no longer exists. Please select a new file.")
            st.session_state.current_input_file = None
            st.session_state.current_input_source = None
            st.session_state.last_analysis = None
        else:
            st.markdown("---")

            col_preview, col_actions = st.columns([2, 1])

            with col_preview:
                if modality == 'vision':
                    st.image(str(selected_file), caption=Path(selected_file).name, use_container_width=True)
                else:
                    st.audio(str(selected_file))

            with col_actions:
                if st.button(
                    "🔍 Analyze",
                    type="primary",
                    key="btn_analyze",
                    help=get_tooltip('analyze_button'),
                    use_container_width=True
                ):
                    # Set loading state for pipeline visualization
                    st.session_state.current_stage = 'ai'
                    st.session_state.is_analyzing = True

                    with st.spinner("AI analyzing..."):
                        analyzer = get_analyzer(modality)
                        status, details = analyzer.analyze(selected_file)

                        # Clear loading state
                        st.session_state.is_analyzing = False

                        if status:
                            st.session_state.last_analysis = {
                                'file': selected_file,
                                'status': status,
                                'details': details,
                                'modality': modality
                            }
                            st.session_state.current_stage = 'staging'
                            add_activity(
                                st.session_state,
                                '',
                                f"Analyzed {Path(selected_file).name}",
                                f"Result: {status}"
                            )
                            st.rerun()
                        else:
                            st.session_state.current_stage = 'input'
                            st.error(f"Analysis failed: {details.get('error', 'Unknown error')}")
                            add_activity(st.session_state, '', f"Analysis failed", str(details.get('error', '')))

            # Display analysis results
            if st.session_state.last_analysis:
                analysis = st.session_state.last_analysis

                if str(analysis['file']) == str(st.session_state.current_input_file):
                    st.markdown("---")
                    st.markdown("### Analysis Results")

                    status = analysis['status']
                    details = analysis['details']

                    # Two columns for results
                    res_col1, res_col2 = st.columns([1, 1])

                    with res_col1:
                        # Prediction with styled display
                        if status in ('HEALTHY', 'NORMAL'):
                            st.markdown(
                                f'<div class="prediction-healthy" style="font-size: 1.5rem;">{status}</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f'<div class="prediction-sick" style="font-size: 1.5rem;">{status}</div>',
                                unsafe_allow_html=True
                            )

                    with res_col2:
                        # Score metric
                        if modality == 'vision':
                            score = details.get('health_score', 0)
                            st.metric("Health Score", f"{score:.2f}", help=get_tooltip('health_score'))

                            # Show reference comparison details
                            ref_details = details.get('reference_details', {})
                            if ref_details.get('reference_used'):
                                ref_adj = details.get('reference_adjustment', 0)
                                base_score = details.get('base_health_score', score)
                                adj_sign = "+" if ref_adj >= 0 else ""
                                st.caption(
                                    f"Base: {base_score:.2f} {adj_sign}{ref_adj:.2f} (reference)"
                                )
                                # Show nearest neighbors in expander
                                neighbors = ref_details.get('k_neighbors', [])
                                if neighbors:
                                    with st.expander("Similar verified images"):
                                        for n in neighbors[:3]:
                                            icon = "✓" if n['class'] == 'HEALTHY' else "✗"
                                            st.caption(
                                                f"{icon} {n['file'][:25]}... "
                                                f"({n['similarity']:.0%} similar, {n['class']})"
                                            )
                            else:
                                # Show why reference wasn't used
                                reason = ref_details.get('reason', '')
                                if reason:
                                    st.caption(f"ℹ️ {reason}")
                        else:
                            score = details.get('distress_score', 0)
                            st.metric("Distress Score", f"{score:.2f}", help=get_tooltip('distress_score'))

                    # Audio visualization
                    if modality == 'audio' and MATPLOTLIB_AVAILABLE:
                        fig = create_combined_figure(selected_file, features=details)
                        if fig:
                            st.pyplot(fig)

                    # Action buttons
                    st.markdown("---")
                    col_stage, col_skip = st.columns(2)

                    with col_stage:
                        if st.button(
                            "📥 Stage for Review",
                            type="primary",
                            key="btn_stage",
                            help=get_tooltip('stage_button'),
                            use_container_width=True
                        ):
                            stage_classification(
                                file_path=selected_file,
                                modality=modality,
                                ai_classification=status,
                                confidence=score,
                                features=details
                            )
                            st.session_state.current_stage = 'staging'
                            add_activity(
                                st.session_state,
                                '',
                                f"Staged {Path(selected_file).name}",
                                f"→ Data_Bank/Staging/"
                            )
                            st.success("Staged! Switch to 'Review Staged' mode to validate.")

                            # Clear current input after staging
                            st.session_state.current_input_file = None
                            st.session_state.current_input_source = None
                            st.session_state.last_analysis = None

                    with col_skip:
                        if st.button(
                            "⏭️ Skip",
                            key="btn_skip_analyze",
                            use_container_width=True
                        ):
                            add_activity(st.session_state, '', f"Skipped {Path(selected_file).name}")
                            st.session_state.last_analysis = None
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

    # Determine destination based on modality and classification
    prediction = item['ai_classification']
    modality = item.get('modality', 'vision')
    suffix = "Images/" if modality == 'vision' else "Audio/"

    if agrees:
        if prediction in ('HEALTHY', 'NORMAL'):
            destination = f"Verified_Healthy_{suffix}"
        else:
            destination = f"Verified_Sick_{suffix}"
        icon = ''
    else:
        if prediction in ('HEALTHY', 'NORMAL'):
            destination = f"Verified_Sick_{suffix}"
        else:
            destination = f"Verified_Healthy_{suffix}"
        icon = ''

    # Log activity
    action = "Confirmed" if agrees else "Corrected"
    add_activity(
        st.session_state,
        icon,
        f"{action} {prediction} ({item['original_file'][:20]}...)",
        f"→ {destination}"
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

    # Update stage
    st.session_state.current_stage = 'verified'

    # Move to next item
    pending = st.session_state.pending_items
    if pending:
        st.session_state.current_index = st.session_state.current_index % max(len(pending) - 1, 1)

    st.rerun()


def main():
    """Main application entry point"""
    init_session_state()

    # Apply dark theme
    apply_theme(st)

    # Header
    render_header()

    # NOTE: We no longer override current_stage here.
    # The stage is controlled by workflow logic in render_analyze_mode(),
    # render_review_mode(), and handle_feedback(). Mode changes are handled
    # in render_left_panel() which only resets stage when mode actually changes.

    # Animated data flow pipeline
    render_data_flow_header(
        st,
        st.session_state.current_stage,
        is_loading=st.session_state.get('is_analyzing', False)
    )

    # Three-panel layout
    col_left, col_center, col_right = st.columns([1, 2.5, 1.2])

    with col_left:
        render_left_panel()

    with col_center:
        # Main content area
        st.markdown("""
        <div style="background: var(--bg-surface); border-radius: 16px;
                    padding: 1.5rem; border: 1px solid var(--border-default);
                    min-height: 400px;">
        """, unsafe_allow_html=True)

        if st.session_state.mode == 'review':
            render_review_mode()
        else:
            render_analyze_mode()

        st.markdown("</div>", unsafe_allow_html=True)

        # How it works expanders (titles shortened to prevent icon overlap)
        with st.expander("👁️ Vision Analysis"):
            section = get_how_it_works('vision_analysis')
            st.markdown(section['content'])

        with st.expander("🔊 Audio Analysis"):
            section = get_how_it_works('audio_analysis')
            st.markdown(section['content'])

        with st.expander("🧠 Reference Learning"):
            section = get_how_it_works('reference_learning')
            st.markdown(section['content'])

        with st.expander("⚙️ Threshold Tuning"):
            section = get_how_it_works('threshold_tuning')
            st.markdown(section['content'])

    with col_right:
        render_right_panel()


if __name__ == "__main__":
    main()
