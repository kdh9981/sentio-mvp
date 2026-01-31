"""
Sentio Training App - Data Flow Visualization

Visual components showing the data pipeline stages:
- Animated header with flowing particles
- File location indicators
- Real-time activity log
"""

from datetime import datetime
from pathlib import Path


# Stage guidance messages
STAGE_GUIDANCE = {
    'input': '▼ Drop a file or click Browse to begin',
    'ai': '⏳ AI is analyzing your file...',
    'staging': '📋 Review the prediction below',
    'review': '❓ Is the AI prediction correct?',
    'verified': '✓ Success! Ready for next file →',
}


def render_data_flow_header(st, current_stage: str = 'input', is_loading: bool = False):
    """
    Render the animated data flow pipeline header.

    Args:
        st: Streamlit module
        current_stage: Which stage to highlight as active
                      ('input', 'ai', 'staging', 'review', 'verified')
        is_loading: Whether AI analysis is in progress (shows spinner)
    """
    stages = [
        {'id': 'input', 'icon': '📁', 'name': 'INPUT', 'desc': 'Upload, paste, or record'},
        {'id': 'ai', 'icon': '🤖', 'name': 'AI ANALYSIS', 'desc': 'YOLOv10 + BirdNET'},
        {'id': 'staging', 'icon': '📋', 'name': 'STAGING', 'desc': 'Saved for review'},
        {'id': 'review', 'icon': '👁️', 'name': 'REVIEW', 'desc': 'Human validation'},
        {'id': 'verified', 'icon': '✅', 'name': 'VERIFIED', 'desc': 'Training data'},
    ]

    # Build the HTML
    stage_html_parts = []
    for i, stage in enumerate(stages):
        # Determine state class
        stage_order = ['input', 'ai', 'staging', 'review', 'verified']
        current_idx = stage_order.index(current_stage) if current_stage in stage_order else 0
        stage_idx = stage_order.index(stage['id'])

        state_classes = []
        if stage['id'] == current_stage:
            state_classes.append('active')
            # Special class for verified stage (gold glow)
            if stage['id'] == 'verified':
                state_classes.append('verified-stage')
            # Loading spinner for AI stage
            if stage['id'] == 'ai' and is_loading:
                state_classes.append('loading')
        elif stage_idx < current_idx:
            state_classes.append('completed')

        state_class = ' '.join(state_classes)

        # Add guidance panel for active stage
        guidance_html = ''
        if stage['id'] == current_stage:
            guidance_text = STAGE_GUIDANCE.get(stage['id'], '')
            guidance_html = f'''
            <div class="stage-guidance">
                <span class="guidance-arrow">▼</span>
                {guidance_text}
            </div>
            '''

        stage_html = f"""
        <div class="pipeline-stage">
            <div class="stage-icon {state_class}">{stage['icon']}</div>
            <div class="stage-name">{stage['name']}</div>
            <div class="stage-desc">{stage['desc']}</div>
            {guidance_html}
        </div>
        """
        stage_html_parts.append(stage_html)

        # Add connector between stages (except after last)
        if i < len(stages) - 1:
            stage_html_parts.append('<div class="pipeline-connector"></div>')

    stages_html = ''.join(stage_html_parts)

    # Enhanced feedback loop with animated particle when at VERIFIED stage
    is_verified = current_stage == 'verified'
    particle_html = ''
    if is_verified:
        particle_html = '''
            <circle class="feedback-particle" r="3">
                <animateMotion dur="2.5s" repeatCount="indefinite">
                    <mpath href="#feedbackPath"/>
                </animateMotion>
            </circle>
        '''

    # Complete pipeline HTML with visual feedback loop
    pipeline_html = f"""
    <div class="pipeline-container">
        <div class="pipeline-title">YOUR DATA'S JOURNEY</div>
        <div class="pipeline-stages">
            {stages_html}
        </div>
        <!-- Visual feedback loop: curved arrow from VERIFIED back to INPUT -->
        <div class="feedback-loop-container">
            <svg class="feedback-loop-svg" viewBox="0 0 100 30" preserveAspectRatio="xMidYMid meet">
                <!-- Curved path from right (VERIFIED) to left (INPUT) -->
                <path id="feedbackPath" class="feedback-loop-path"
                      d="M 92 5 Q 50 28, 8 5"
                      marker-end="url(#arrowhead)"/>
                {particle_html}
                <!-- Arrowhead definition -->
                <defs>
                    <marker id="arrowhead" markerWidth="8" markerHeight="8"
                            refX="4" refY="4" orient="auto">
                        <polygon class="feedback-loop-arrow" points="0,0 8,4 0,8"/>
                    </marker>
                </defs>
            </svg>
            <div class="feedback-badge">
                <span class="feedback-badge-icon">↻</span>
                Verified data improves AI accuracy
            </div>
        </div>
    </div>
    """

    # Use st.html for better raw HTML rendering in newer Streamlit versions
    if hasattr(st, 'html'):
        st.html(pipeline_html)
    else:
        st.markdown(pipeline_html, unsafe_allow_html=True)


def render_file_location(st, current_path: str = None, prediction: str = None, modality: str = None):
    """
    Render the file location indicator showing current location
    and where the file will go based on feedback.

    Args:
        st: Streamlit module
        current_path: Current file path (can be relative)
        prediction: Current AI prediction ('HEALTHY', 'SICK', etc.)
        modality: 'vision' or 'audio' (auto-detected from file extension if not provided)
    """
    if not current_path:
        st.markdown("""
        <div class="file-location">
            <div class="file-location-header">
                FILE LOCATION
            </div>
            <div class="file-path" style="color: var(--text-muted);">
                No file selected
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Parse the path for display
    path = Path(current_path)
    display_path = str(path.parent.name) + '/' + path.name if path.parent.name else path.name

    # Auto-detect modality from file extension if not provided
    if modality is None:
        ext = path.suffix.lower()
        audio_exts = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}
        modality = 'audio' if ext in audio_exts else 'vision'

    # Determine folder suffix based on modality
    suffix = "Images/" if modality == 'vision' else "Audio/"

    # Determine destinations based on prediction and modality
    if prediction in ('HEALTHY', 'NORMAL'):
        correct_dest = f'Verified_Healthy_{suffix}'
        incorrect_dest = f'Verified_Sick_{suffix}'
    elif prediction in ('SICK', 'DISTRESS'):
        correct_dest = f'Verified_Sick_{suffix}'
        incorrect_dest = f'Verified_Healthy_{suffix}'
    else:
        correct_dest = f'Verified_{suffix}'
        incorrect_dest = f'Verified_{suffix}'

    location_html = f"""
    <div class="file-location">
        <div class="file-location-header">
            FILE LOCATION
        </div>
        <div class="file-path">
            Current: {display_path}
        </div>
        <div class="file-destination">
            <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                <span class="destination-healthy">
                    If Correct → {correct_dest}
                </span>
            </div>
            <div style="margin-top: 4px;">
                <span class="destination-sick">
                    If Wrong → {incorrect_dest}
                </span>
            </div>
        </div>
    </div>
    """

    if hasattr(st, 'html'):
        st.html(location_html)
    else:
        st.markdown(location_html, unsafe_allow_html=True)


def _get_learning_hint(samples: int, has_suggestion: bool) -> str:
    """Get contextual hint based on learning progress."""
    if samples == 0:
        return "Start reviewing to help calibrate AI thresholds"
    elif samples < 5:
        return f"Keep going! {5 - samples} more reviews for initial calibration"
    elif samples < 10:
        return f"{10 - samples} more samples until threshold suggestion"
    elif has_suggestion:
        return "Threshold adjustment ready based on your feedback!"
    else:
        return "AI thresholds are well-calibrated from your feedback"


def render_learning_status(st, tuner_data: dict = None, stats: dict = None):
    """
    Render a compact learning status indicator showing how feedback improves AI.

    Args:
        st: Streamlit module
        tuner_data: dict with 'current', 'suggested', 'samples' keys
        stats: dict with accuracy info
    """
    if not tuner_data:
        tuner_data = {'current': 0.5, 'suggested': None, 'samples': 0}
    if not stats:
        stats = {'accuracy': 0.0}

    samples = tuner_data.get('samples', 0)
    accuracy = stats.get('accuracy', 0) * 100
    has_suggestion = tuner_data.get('suggested') is not None and samples >= 10

    # Progress toward threshold suggestion (needs 10 samples)
    progress = min(samples / 10, 1.0) * 100
    progress_color = 'var(--accent-healthy)' if progress >= 100 else 'var(--accent-warn)'

    hint = _get_learning_hint(samples, has_suggestion)

    html = f"""
    <div style="background: var(--bg-elevated); border: 1px solid var(--border-default);
                border-radius: 10px; padding: 14px 18px; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <span style="font-size: 1.25rem;">🧠</span>
            <span style="font-family: var(--font-body); font-weight: 600;
                        color: var(--text-primary); font-size: 0.9rem;">
                AI Learning Progress
            </span>
        </div>
        <div style="display: flex; gap: 24px; margin-bottom: 12px;">
            <div style="text-align: center;">
                <div style="font-family: var(--font-mono); font-size: 1.25rem;
                            color: var(--accent-info); font-weight: 600;">{samples}</div>
                <div style="font-size: 0.7rem; color: var(--text-muted);
                            text-transform: uppercase; letter-spacing: 0.05em;">Samples</div>
            </div>
            <div style="text-align: center;">
                <div style="font-family: var(--font-mono); font-size: 1.25rem;
                            color: {'var(--accent-healthy)' if accuracy >= 70 else 'var(--accent-sick)'};
                            font-weight: 600;">{accuracy:.0f}%</div>
                <div style="font-size: 0.7rem; color: var(--text-muted);
                            text-transform: uppercase; letter-spacing: 0.05em;">Accuracy</div>
            </div>
        </div>
        <div style="background: var(--bg-deep); border-radius: 4px; height: 6px;
                    overflow: hidden; margin-bottom: 8px;">
            <div style="width: {progress}%; height: 100%; background: {progress_color};
                        border-radius: 4px; transition: width 0.3s ease;"></div>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary);">
            {hint}
        </div>
    </div>
    """

    if hasattr(st, 'html'):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def render_feedback_panel(st, tuner_data: dict = None, stats: dict = None):
    """
    Render the feedback loop status panel showing how feedback
    is improving the model.

    Args:
        st: Streamlit module
        tuner_data: dict with 'current', 'suggested', 'samples' keys
        stats: dict with accuracy and session info
    """
    if not tuner_data:
        tuner_data = {'current': 0.5, 'suggested': None, 'samples': 0}

    if not stats:
        stats = {'accuracy': 0.0, 'session_correct': 0, 'session_total': 0}

    # Calculate accuracy change (mock for now)
    accuracy_pct = stats.get('accuracy', 0) * 100

    # Build threshold suggestion section
    if tuner_data.get('suggested') and tuner_data.get('samples', 0) >= 10:
        suggested = tuner_data['suggested']
        current = tuner_data['current']
        if abs(suggested - current) > 0.01:
            threshold_section = f"""
            <div style="background: var(--bg-deep); padding: 12px; border-radius: 8px; margin-top: 12px;">
                <div style="font-size: 0.75rem; color: var(--accent-warn); margin-bottom: 8px;">
                    THRESHOLD ADJUSTMENT
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: var(--text-muted);">Current:</span>
                        <span style="font-family: var(--font-mono); color: var(--text-primary);">{current:.2f}</span>
                    </div>
                    <div style="color: var(--text-muted);">→</div>
                    <div>
                        <span style="color: var(--text-muted);">Suggested:</span>
                        <span style="font-family: var(--font-mono); color: var(--accent-warn);">{suggested:.2f}</span>
                    </div>
                </div>
                <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 8px;">
                    Based on {tuner_data['samples']} boundary errors
                </div>
            </div>
            """
        else:
            threshold_section = ""
    else:
        samples_needed = max(0, 10 - tuner_data.get('samples', 0))
        threshold_section = f"""
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 12px;">
            {samples_needed} more samples needed for threshold suggestions
        </div>
        """

    panel_html = f"""
    <div class="glass-card">
        <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-muted);
                    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">
            FEEDBACK LOOP STATUS
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <div>
                <div class="metric-label">Your Feedback</div>
                <div class="metric-value">{tuner_data.get('samples', 0)} samples</div>
            </div>
            <div>
                <div class="metric-label">AI Accuracy</div>
                <div class="metric-value {'metric-value-healthy' if accuracy_pct >= 70 else 'metric-value-sick'}">{accuracy_pct:.0f}%</div>
            </div>
        </div>
        {threshold_section}
    </div>
    """

    if hasattr(st, 'html'):
        st.html(panel_html)
    else:
        st.markdown(panel_html, unsafe_allow_html=True)


def render_activity_log(st, activities: list = None, max_items: int = 10):
    """
    Render the real-time activity log showing recent actions.

    Args:
        st: Streamlit module
        activities: List of activity dicts with 'time', 'icon', 'text', 'detail' keys
        max_items: Maximum number of items to display
    """
    if not activities:
        activities = []

    # Build activity items HTML
    if activities:
        items_html = ""
        for activity in activities[:max_items]:
            time_str = activity.get('time', datetime.now().strftime('%H:%M'))
            icon = activity.get('icon', '')
            text = activity.get('text', '')
            detail = activity.get('detail', '')

            detail_html = f'<div class="activity-detail">{detail}</div>' if detail else ''

            items_html += f"""
            <div class="activity-item">
                <span class="activity-time">{time_str}</span>
                <span class="activity-icon">{icon}</span>
                <div>
                    <div class="activity-text">{text}</div>
                    {detail_html}
                </div>
            </div>
            """
    else:
        items_html = """
        <div style="color: var(--text-muted); font-size: 0.8125rem; text-align: center; padding: 20px;">
            No activity yet. Start analyzing or reviewing files!
        </div>
        """

    log_html = f"""
    <div class="activity-log">
        <div class="activity-log-header">
            SESSION ACTIVITY
        </div>
        {items_html}
    </div>
    """

    if hasattr(st, 'html'):
        st.html(log_html)
    else:
        st.markdown(log_html, unsafe_allow_html=True)


def add_activity(session_state, icon: str, text: str, detail: str = None):
    """
    Add a new activity to the session's activity log.

    Args:
        session_state: Streamlit session state
        icon: Emoji icon for the activity
        text: Main activity text
        detail: Optional detail text (e.g., file destination)
    """
    if 'activity_log' not in session_state:
        session_state.activity_log = []

    activity = {
        'time': datetime.now().strftime('%H:%M'),
        'icon': icon,
        'text': text,
        'detail': detail,
    }

    # Add to beginning (most recent first)
    session_state.activity_log.insert(0, activity)

    # Keep only last 50 activities
    session_state.activity_log = session_state.activity_log[:50]


def render_input_method_cards(st, modality: str):
    """
    Render the visual input method selector cards.

    Args:
        st: Streamlit module
        modality: 'vision' or 'audio'
    """
    if modality == 'vision':
        methods = [
            {'icon': '📤', 'name': 'Upload', 'desc': 'Drop image file'},
            {'icon': '📋', 'name': 'Paste', 'desc': 'From clipboard'},
            {'icon': '📁', 'name': 'Folder', 'desc': 'Browse files'},
        ]
    else:
        methods = [
            {'icon': '📤', 'name': 'Upload', 'desc': 'Drop audio file'},
            {'icon': '🎤', 'name': 'Record', 'desc': 'Use microphone'},
            {'icon': '📁', 'name': 'Folder', 'desc': 'Browse files'},
        ]

    cards_html = '<div style="display: flex; gap: 12px; margin-bottom: 20px;">'
    for method in methods:
        cards_html += f"""
        <div class="glass-card" style="flex: 1; text-align: center; padding: 16px; cursor: pointer;">
            <div style="font-size: 1.5rem; margin-bottom: 8px;">{method['icon']}</div>
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">
                {method['name']}
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">
                {method['desc']}
            </div>
        </div>
        """
    cards_html += '</div>'

    if hasattr(st, 'html'):
        st.html(cards_html)
    else:
        st.markdown(cards_html, unsafe_allow_html=True)
