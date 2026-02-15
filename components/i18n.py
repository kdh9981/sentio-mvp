"""
Sentio Training App - Internationalization (i18n) System

Bilingual support for English and Korean with:
- Organized translations by category
- Shorthand t() function for easy access
- Language toggle rendering
- Session state management
"""

import streamlit as st

# Supported languages
LANGUAGES = {
    'en': 'EN',
    'ko': '한국어',
}

# Main translations dictionary organized by category
TRANSLATIONS = {
    'en': {
        # === HEADER ===
        'header': {
            'title': 'Sentio',
            'subtitle': 'Chicken Health Observatory · Human-in-the-Loop Training',
            'page_title': 'Sentio Training Observatory',
        },

        # === CONTROL PANEL ===
        'control_panel': {
            'title': 'Control Panel',
            'mode': 'Mode',
            'mode_analyze': 'Analyze New',
            'mode_review': 'Review Staged',
            'modality': 'Modality',
            'modality_vision': 'Vision',
            'modality_audio': 'Audio',
            'pipeline_stats': 'Pipeline Stats',
            'this_session': 'This Session',
            'reference_learning': 'Reference Learning',
        },

        # === REFERENCE STATUS ===
        'reference': {
            'disabled': 'Reference comparison disabled',
            'active': 'Active: Using {count} verified samples',
            'need_healthy': '{count} more healthy',
            'need_sick': '{count} more sick',
            'need_both': '{healthy} more healthy and {sick} more sick',
            'to_activate': 'Need {detail} samples to activate',
        },

        # === STATS ===
        'stats': {
            'staged': 'Staged',
            'pending': 'Pending',
            'validated': 'Validated',
            'accuracy': 'Accuracy',
            'session_score': 'Session Score',
            'healthy': 'Healthy',
            'sick': 'Sick',
            'active': 'Active',
        },

        # === BUTTONS ===
        'buttons': {
            'analyze': '🔍 Analyze',
            'stage': '📥 Stage for Review',
            'skip': 'Skip',
            'skip_icon': '⏭️ Skip',
            'correct': '✓ Correct',
            'incorrect': '✗ Wrong',
            'apply_threshold': 'Apply {threshold} Threshold',
        },

        # === PREDICTIONS ===
        'predictions': {
            'healthy': 'HEALTHY',
            'sick': 'SICK',
            'normal': 'NORMAL',
            'distress': 'DISTRESS',
        },

        # === ANALYSIS ===
        'analysis': {
            'ai_prediction': 'AI Prediction',
            'confidence': 'Confidence',
            'key_features': 'Key Features',
            'health_score': 'Health Score',
            'distress_score': 'Distress Score',
            'your_verdict': 'Your Verdict',
            'results': 'Analysis Results',
            'base_score': 'Base: {base} {adj} (reference)',
            'similar_images': 'Similar verified images',
        },

        # === INPUT TABS ===
        'input': {
            'upload_image': '📤 Upload Image',
            'upload_audio': '📤 Upload Audio',
            'paste_clipboard': '📋 Paste Clipboard',
            'record_mic': '🎤 Record Microphone',
            'browse_folder': '📁 Browse Folder',
            'drop_image': 'Drop image file here',
            'drop_audio': 'Drop audio file here',
            'select_file': 'Select a file to analyze',
            'paste_info': 'Click below, then paste an image (Cmd+V / Ctrl+V)',
            'paste_button': '📋 Paste Image',
            'record_info': 'Click to start recording, click again to stop.',
            'record_label': 'Record chicken sounds',
        },

        # === MESSAGES ===
        'messages': {
            'loaded': 'Loaded: {filename}',
            'uploaded': 'Uploaded {filename}',
            'image_pasted': 'Image pasted!',
            'pasted_clipboard': 'Pasted image from clipboard',
            'recording_saved': 'Recording saved!',
            'recorded_audio': 'Recorded audio',
            'no_files_folder': "No files in '{folder}'. Use upload or {method} instead.",
            'file_not_found': 'File not found: {path}',
            'file_missing': 'Previously selected file no longer exists. Please select a new file.',
            'no_pending': '📂 No {modality} items pending review. Switch to \'Analyze New\' mode to process files.',
            'analyzing': 'AI analyzing...',
            'analysis_failed': 'Analysis failed: {error}',
            'staged_success': "Staged! Switch to 'Review Staged' mode to validate.",
            'threshold_applied': 'Threshold applied!',
            'threshold_updated': 'Threshold updated to {threshold}',
            'paste_requires': 'Clipboard paste requires: `pip install streamlit-paste-button`',
            'reviewing': 'Reviewing {current} of {total}',
        },

        # === ACTIVITY LOG ===
        'activity': {
            'title': 'SESSION ACTIVITY',
            'no_activity': 'No activity yet. Start analyzing or reviewing files!',
            'skipped': 'Skipped {filename}',
            'analyzed': 'Analyzed {filename}',
            'result': 'Result: {status}',
            'staged': 'Staged {filename}',
            'staged_dest': '→ Data_Bank/Staging/',
            'confirmed': 'Confirmed {prediction} ({filename}...)',
            'corrected': 'Corrected {prediction} ({filename}...)',
            'detection': '{modality} detection',
        },

        # === FILE LOCATION ===
        'file_location': {
            'title': 'FILE LOCATION',
            'no_file': 'No file selected',
            'current': 'Current: {path}',
            'if_correct': 'If Correct → {dest}',
            'if_wrong': 'If Wrong → {dest}',
        },

        # === PIPELINE ===
        'pipeline': {
            'title': "YOUR DATA'S JOURNEY",
            'input': 'INPUT',
            'input_desc': 'Upload, paste, or record',
            'ai': 'AI ANALYSIS',
            'ai_desc': 'YOLOv10 + BirdNET',
            'staging': 'STAGING',
            'staging_desc': 'Saved for review',
            'review': 'REVIEW',
            'review_desc': 'Human validation',
            'verified': 'VERIFIED',
            'verified_desc': 'Training data',
            'feedback_badge': 'Verified data improves AI accuracy',
        },

        # === STAGE GUIDANCE ===
        'guidance': {
            'input': '▼ Drop a file or click Browse to begin',
            'ai': '⏳ AI is analyzing your file...',
            'staging': '📋 Review the prediction below',
            'review': '❓ Is the AI prediction correct?',
            'verified': '✓ Success! Ready for next file →',
        },

        # === LEARNING STATUS ===
        'learning': {
            'title': 'AI Learning Progress',
            'samples': 'Samples',
            'accuracy': 'Accuracy',
            'hint_start': 'Start reviewing to help calibrate AI thresholds',
            'hint_progress': 'Keep going! {remaining} more reviews for initial calibration',
            'hint_samples': '{remaining} more samples until threshold suggestion',
            'hint_ready': 'Threshold adjustment ready based on your feedback!',
            'hint_calibrated': 'AI thresholds are well-calibrated from your feedback',
        },

        # === FEEDBACK PANEL ===
        'feedback_panel': {
            'title': 'FEEDBACK LOOP STATUS',
            'your_feedback': 'Your Feedback',
            'samples': '{count} samples',
            'ai_accuracy': 'AI Accuracy',
            'threshold_adjustment': 'THRESHOLD ADJUSTMENT',
            'current': 'Current:',
            'suggested': 'Suggested:',
            'based_on': 'Based on {count} boundary errors',
            'samples_needed': '{count} more samples needed for threshold suggestions',
        },

        # === EXPANDERS ===
        'expanders': {
            'review_mode': 'Review Mode',
            'vision_analysis': '👁️ Vision Analysis',
            'audio_analysis': '🔊 Audio Analysis',
            'reference_learning': '🧠 Reference Learning',
            'threshold_tuning': '⚙️ Threshold Tuning',
        },

        # === AUDIO FEATURES ===
        'audio': {
            'pitch': '🎵 Pitch: {value} Hz',
            'volume': '📢 Volume: {value}',
            'call_rate': '📊 Call Rate: {value}/sec',
        },

        # === COMPLETION REPORT ===
        'report': {
            'confirmed': '✅ Confirmed {status} — {file} saved!',
            'corrected': '🔄 Corrected {status} → opposite — {file} saved!',
            'destination': 'Saved to {dest}',
        },

        # === INPUT METHODS ===
        'input_methods': {
            'upload': 'Upload',
            'upload_desc_image': 'Drop image file',
            'upload_desc_audio': 'Drop audio file',
            'paste': 'Paste',
            'paste_desc': 'From clipboard',
            'record': 'Record',
            'record_desc': 'Use microphone',
            'folder': 'Folder',
            'folder_desc': 'Browse files',
        },
    },

    'ko': {
        # === HEADER ===
        'header': {
            'title': 'Sentio',
            'subtitle': '닭 건강 관측소 · 인간 참여 학습',
            'page_title': 'Sentio 학습 관측소',
        },

        # === CONTROL PANEL ===
        'control_panel': {
            'title': '제어판',
            'mode': '모드',
            'mode_analyze': '새 항목 분석',
            'mode_review': '대기 항목 검토',
            'modality': '분석 유형',
            'modality_vision': '이미지',
            'modality_audio': '오디오',
            'pipeline_stats': '파이프라인 통계',
            'this_session': '현재 세션',
            'reference_learning': '참조 학습',
        },

        # === REFERENCE STATUS ===
        'reference': {
            'disabled': '참조 비교 비활성화됨',
            'active': '활성화: 검증된 샘플 {count}개 사용 중',
            'need_healthy': '건강 샘플 {count}개 더 필요',
            'need_sick': '아픈 샘플 {count}개 더 필요',
            'need_both': '건강 샘플 {healthy}개, 아픈 샘플 {sick}개 더 필요',
            'to_activate': '활성화하려면 {detail}',
        },

        # === STATS ===
        'stats': {
            'staged': '대기 중',
            'pending': '검토 필요',
            'validated': '검증 완료',
            'accuracy': '정확도',
            'session_score': '세션 점수',
            'healthy': '건강',
            'sick': '아픔',
            'active': '활성화',
        },

        # === BUTTONS ===
        'buttons': {
            'analyze': '🔍 분석',
            'stage': '📥 검토 대기',
            'skip': '건너뛰기',
            'skip_icon': '⏭️ 건너뛰기',
            'correct': '✓ 정확함',
            'incorrect': '✗ 오류',
            'apply_threshold': '{threshold} 임계값 적용',
        },

        # === PREDICTIONS ===
        'predictions': {
            'healthy': '건강',
            'sick': '아픔',
            'normal': '정상',
            'distress': '이상',
        },

        # === ANALYSIS ===
        'analysis': {
            'ai_prediction': 'AI 예측',
            'confidence': '신뢰도',
            'key_features': '주요 특징',
            'health_score': '건강 점수',
            'distress_score': '이상 점수',
            'your_verdict': '당신의 판단',
            'results': '분석 결과',
            'base_score': '기본: {base} {adj} (참조)',
            'similar_images': '유사한 검증 이미지',
        },

        # === INPUT TABS ===
        'input': {
            'upload_image': '📤 이미지 업로드',
            'upload_audio': '📤 오디오 업로드',
            'paste_clipboard': '📋 클립보드 붙여넣기',
            'record_mic': '🎤 마이크 녹음',
            'browse_folder': '📁 폴더 찾아보기',
            'drop_image': '여기에 이미지 파일을 놓으세요',
            'drop_audio': '여기에 오디오 파일을 놓으세요',
            'select_file': '분석할 파일을 선택하세요',
            'paste_info': '아래를 클릭한 후 이미지 붙여넣기 (Cmd+V / Ctrl+V)',
            'paste_button': '📋 이미지 붙여넣기',
            'record_info': '녹음을 시작하려면 클릭, 멈추려면 다시 클릭하세요.',
            'record_label': '닭 소리 녹음',
        },

        # === MESSAGES ===
        'messages': {
            'loaded': '로드됨: {filename}',
            'uploaded': '{filename} 업로드됨',
            'image_pasted': '이미지 붙여넣기 완료!',
            'pasted_clipboard': '클립보드에서 이미지 붙여넣기',
            'recording_saved': '녹음 저장 완료!',
            'recorded_audio': '오디오 녹음됨',
            'no_files_folder': "'{folder}'에 파일이 없습니다. 업로드 또는 {method}을(를) 사용하세요.",
            'file_not_found': '파일을 찾을 수 없음: {path}',
            'file_missing': '이전에 선택한 파일이 더 이상 존재하지 않습니다. 새 파일을 선택하세요.',
            'no_pending': '📂 검토 대기 중인 {modality} 항목이 없습니다. \'새 항목 분석\' 모드로 전환하여 파일을 처리하세요.',
            'analyzing': 'AI 분석 중...',
            'analysis_failed': '분석 실패: {error}',
            'staged_success': "대기 완료! '대기 항목 검토' 모드로 전환하여 검증하세요.",
            'threshold_applied': '임계값 적용됨!',
            'threshold_updated': '임계값이 {threshold}(으)로 업데이트됨',
            'paste_requires': '클립보드 붙여넣기에 필요: `pip install streamlit-paste-button`',
            'reviewing': '{total}개 중 {current}개 검토 중',
        },

        # === ACTIVITY LOG ===
        'activity': {
            'title': '세션 활동',
            'no_activity': '아직 활동이 없습니다. 파일 분석 또는 검토를 시작하세요!',
            'skipped': '{filename} 건너뜀',
            'analyzed': '{filename} 분석됨',
            'result': '결과: {status}',
            'staged': '{filename} 대기 중',
            'staged_dest': '→ Data_Bank/Staging/',
            'confirmed': '{prediction} 확인됨 ({filename}...)',
            'corrected': '{prediction} 수정됨 ({filename}...)',
            'detection': '{modality} 감지',
        },

        # === FILE LOCATION ===
        'file_location': {
            'title': '파일 위치',
            'no_file': '선택된 파일 없음',
            'current': '현재: {path}',
            'if_correct': '정확하면 → {dest}',
            'if_wrong': '오류면 → {dest}',
        },

        # === PIPELINE ===
        'pipeline': {
            'title': '데이터의 여정',
            'input': '입력',
            'input_desc': '업로드, 붙여넣기, 또는 녹음',
            'ai': 'AI 분석',
            'ai_desc': 'YOLOv10 + BirdNET',
            'staging': '대기',
            'staging_desc': '검토를 위해 저장됨',
            'review': '검토',
            'review_desc': '인간 검증',
            'verified': '검증됨',
            'verified_desc': '학습 데이터',
            'feedback_badge': '검증된 데이터가 AI 정확도를 향상시킵니다',
        },

        # === STAGE GUIDANCE ===
        'guidance': {
            'input': '▼ 파일을 놓거나 찾아보기를 클릭하여 시작',
            'ai': '⏳ AI가 파일을 분석 중...',
            'staging': '📋 아래 예측을 검토하세요',
            'review': '❓ AI 예측이 정확한가요?',
            'verified': '✓ 성공! 다음 파일 준비 →',
        },

        # === LEARNING STATUS ===
        'learning': {
            'title': 'AI 학습 진행',
            'samples': '샘플',
            'accuracy': '정확도',
            'hint_start': 'AI 임계값 조정을 위해 검토를 시작하세요',
            'hint_progress': '계속하세요! 초기 조정까지 {remaining}개 더 필요',
            'hint_samples': '임계값 제안까지 {remaining}개 샘플 더 필요',
            'hint_ready': '피드백을 기반으로 임계값 조정 준비됨!',
            'hint_calibrated': '피드백을 통해 AI 임계값이 잘 조정됨',
        },

        # === FEEDBACK PANEL ===
        'feedback_panel': {
            'title': '피드백 루프 상태',
            'your_feedback': '귀하의 피드백',
            'samples': '{count}개 샘플',
            'ai_accuracy': 'AI 정확도',
            'threshold_adjustment': '임계값 조정',
            'current': '현재:',
            'suggested': '제안:',
            'based_on': '{count}개 경계 오류 기반',
            'samples_needed': '임계값 제안까지 {count}개 샘플 더 필요',
        },

        # === EXPANDERS ===
        'expanders': {
            'review_mode': '검토 모드',
            'vision_analysis': '👁️ 이미지 분석',
            'audio_analysis': '🔊 오디오 분석',
            'reference_learning': '🧠 참조 학습',
            'threshold_tuning': '⚙️ 임계값 조정',
        },

        # === AUDIO FEATURES ===
        'audio': {
            'pitch': '🎵 음높이: {value} Hz',
            'volume': '📢 음량: {value}',
            'call_rate': '📊 울음 빈도: {value}/초',
        },

        # === COMPLETION REPORT ===
        'report': {
            'confirmed': '✅ {status} 확인 완료 — {file} 저장됨!',
            'corrected': '🔄 {status} 수정 완료 — {file} 저장됨!',
            'destination': '{dest}에 저장됨',
        },

        # === INPUT METHODS ===
        'input_methods': {
            'upload': '업로드',
            'upload_desc_image': '이미지 파일 놓기',
            'upload_desc_audio': '오디오 파일 놓기',
            'paste': '붙여넣기',
            'paste_desc': '클립보드에서',
            'record': '녹음',
            'record_desc': '마이크 사용',
            'folder': '폴더',
            'folder_desc': '파일 찾아보기',
        },
    },
}


def init_language():
    """Initialize language in session state if not already set."""
    if 'language' not in st.session_state:
        st.session_state.language = 'ko'


def get_current_language() -> str:
    """Get the current language code from session state."""
    init_language()
    return st.session_state.language


def set_language(lang: str):
    """Set the current language."""
    if lang in LANGUAGES:
        st.session_state.language = lang


def t(key_path: str, **kwargs) -> str:
    """
    Get translated text for the given key path.

    Args:
        key_path: Dot-separated path to translation (e.g., 'buttons.analyze')
        **kwargs: Format arguments for string interpolation

    Returns:
        Translated string, or key_path if not found

    Examples:
        t('buttons.analyze')  # Returns '🔍 Analyze' or '🔍 분석'
        t('messages.loaded', filename='test.jpg')  # With interpolation
    """
    init_language()
    lang = st.session_state.language

    # Navigate the nested dictionary
    keys = key_path.split('.')
    value = TRANSLATIONS.get(lang, TRANSLATIONS['en'])

    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            value = None
            break

    # Fallback to English if not found in current language
    if value is None:
        value = TRANSLATIONS['en']
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break

    # Return key_path if still not found
    if value is None:
        return key_path

    # Apply format arguments if provided
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value

    return value


def render_language_toggle(streamlit_module):
    """
    Render a language toggle (EN | 한국어) at the top of the sidebar.

    Args:
        streamlit_module: The Streamlit module (st)
    """
    init_language()
    current_lang = st.session_state.language

    # Create a horizontal radio button for language selection
    selected = streamlit_module.radio(
        "🌐 Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        index=0 if current_lang == 'en' else 1,
        horizontal=True,
        key="language_toggle",
        label_visibility="collapsed"
    )

    if selected != current_lang:
        set_language(selected)
        streamlit_module.rerun()


# === TOOLTIPS TRANSLATIONS ===
# These are kept separate for the tooltips module to use

TOOLTIPS_TRANSLATIONS = {
    'en': {
        'correct_button': (
            "The AI got it right! This file will move to the Verified folder "
            "and this feedback helps improve future accuracy."
        ),
        'incorrect_button': (
            "The AI was wrong. This corrects the record and helps adjust "
            "the detection threshold to prevent similar errors."
        ),
        'skip_button': (
            "Skip this file for now. It will remain in Staging for later review."
        ),
        'analyze_button': (
            "Run AI analysis using YOLOv10 (for images) or BirdNET (for audio) "
            "to predict whether this chicken is healthy or showing signs of distress."
        ),
        'stage_button': (
            "Save this file and AI prediction to Data_Bank/Staging/ for human verification. "
            "The original file stays untouched."
        ),
        'health_score': (
            "Composite health score (0-1) based on posture analysis, color vibrancy, "
            "and body alignment. Higher = healthier. Threshold determines healthy vs sick."
        ),
        'distress_score': (
            "Composite distress score (0-1) based on pitch, volume, call rate, "
            "and frequency patterns. Higher = more distressed."
        ),
        'confidence': (
            "How certain the AI is about its prediction. Higher confidence means "
            "the features strongly indicate the predicted state."
        ),
        'threshold': (
            "The cutoff point for healthy vs sick classification. Scores above this "
            "are HEALTHY/NORMAL, below are SICK/DISTRESS. Your feedback adjusts this over time."
        ),
        'accuracy': (
            "How often the AI's predictions match human judgment. Calculated from "
            "all validated samples in this session."
        ),
        'mode_review': (
            "Review mode: Validate AI predictions on staged files. Confirm or correct "
            "each prediction to improve the model's accuracy."
        ),
        'mode_analyze': (
            "Analyze mode: Process new files through the AI. Upload, paste, record, "
            "or select files from the input folder."
        ),
        'modality_vision': (
            "Vision analysis uses YOLOv10 for object detection and MediaPipe for "
            "posture analysis. Best for: photos, video frames."
        ),
        'modality_audio': (
            "Audio analysis uses BirdNET embeddings and librosa for acoustic features. "
            "Best for: recordings of chicken vocalizations."
        ),
        'input_upload': (
            "Drag and drop or click to upload a file from your computer."
        ),
        'input_paste': (
            "Paste an image directly from your clipboard (Cmd+V or Ctrl+V)."
        ),
        'input_record': (
            "Record audio directly from your microphone. Click to start, click again to stop."
        ),
        'input_folder': (
            "Browse files in the configured input folder (Data_Bank/Input_Images or Input_Sounds)."
        ),
        'threshold_suggestion': (
            "Based on feedback patterns, this new threshold may improve accuracy. "
            "It considers cases where the AI made errors near the current threshold."
        ),
        'apply_threshold': (
            "Apply this suggested threshold to config.yaml. The change takes effect immediately."
        ),
        'stage_input': (
            "Your starting point: upload, paste, record, or select files from folders."
        ),
        'stage_ai': (
            "The AI analyzes the file using computer vision (YOLO) or audio analysis (BirdNET)."
        ),
        'stage_staging': (
            "Files are saved to Data_Bank/Staging/ with their AI predictions, awaiting human review."
        ),
        'stage_review': (
            "You verify whether the AI's prediction is correct. Your feedback is crucial."
        ),
        'stage_verified': (
            "Confirmed files move to Verified_Healthy/ or Verified_Sick/ folders for training data."
        ),
        'stage_feedback': (
            "Your corrections feed back into the system, adjusting thresholds for better accuracy."
        ),
        'file_current': (
            "The file's current location in the data pipeline."
        ),
        'file_destination_correct': (
            "If AI is correct, the file moves here."
        ),
        'file_destination_incorrect': (
            "If AI is wrong, the file moves to the opposite category."
        ),
        'stat_total_staged': (
            "Total number of files that have been staged for review since the pipeline started."
        ),
        'stat_pending': (
            "Files currently waiting for human validation in the Staging folder."
        ),
        'stat_validated': (
            "Files that have been reviewed and confirmed/corrected by a human."
        ),
        'stat_session_accuracy': (
            "Accuracy for just this session. Shows how many of your validations agreed with the AI."
        ),
        'reference_healthy': (
            "Number of verified healthy samples in the reference database. "
            "Used to compare new images against known healthy chickens."
        ),
        'reference_sick': (
            "Number of verified sick samples in the reference database. "
            "Used to compare new images against known sick chickens."
        ),
        'reference_status': (
            "When active, new predictions are compared to verified samples for improved accuracy. "
            "Requires at least 3 samples in each category."
        ),
    },
    'ko': {
        'correct_button': (
            "AI가 맞았습니다! 이 파일은 검증 폴더로 이동하며 "
            "이 피드백은 향후 정확도 향상에 도움이 됩니다."
        ),
        'incorrect_button': (
            "AI가 틀렸습니다. 이 기록을 수정하고 감지 임계값을 조정하여 "
            "유사한 오류를 방지하는 데 도움이 됩니다."
        ),
        'skip_button': (
            "이 파일을 일단 건너뜁니다. 나중에 검토하기 위해 대기에 남습니다."
        ),
        'analyze_button': (
            "YOLOv10(이미지용) 또는 BirdNET(오디오용)을 사용하여 AI 분석을 실행하고 "
            "이 닭이 건강한지 또는 이상 징후를 보이는지 예측합니다."
        ),
        'stage_button': (
            "이 파일과 AI 예측을 Data_Bank/Staging/에 저장하여 인간 검증을 대기합니다. "
            "원본 파일은 그대로 유지됩니다."
        ),
        'health_score': (
            "자세 분석, 색상 선명도, 신체 정렬을 기반으로 한 복합 건강 점수(0-1). "
            "높을수록 건강합니다. 임계값이 건강/아픔을 결정합니다."
        ),
        'distress_score': (
            "음높이, 음량, 울음 빈도, 주파수 패턴을 기반으로 한 복합 이상 점수(0-1). "
            "높을수록 더 이상한 상태입니다."
        ),
        'confidence': (
            "AI가 예측에 얼마나 확신하는지 나타냅니다. 신뢰도가 높을수록 "
            "특징이 예측 상태를 강하게 나타냅니다."
        ),
        'threshold': (
            "건강/아픔 분류의 기준점. 이 점수 이상은 건강/정상, "
            "이하는 아픔/이상입니다. 피드백이 시간이 지남에 따라 조정합니다."
        ),
        'accuracy': (
            "AI 예측이 인간 판단과 얼마나 자주 일치하는지 나타냅니다. "
            "이 세션의 모든 검증 샘플에서 계산됩니다."
        ),
        'mode_review': (
            "검토 모드: 대기 중인 파일에 대한 AI 예측을 검증합니다. "
            "각 예측을 확인하거나 수정하여 모델 정확도를 향상시킵니다."
        ),
        'mode_analyze': (
            "분석 모드: AI를 통해 새 파일을 처리합니다. 입력 폴더에서 파일을 "
            "업로드, 붙여넣기, 녹음 또는 선택합니다."
        ),
        'modality_vision': (
            "이미지 분석은 객체 감지에 YOLOv10을, 자세 분석에 MediaPipe를 사용합니다. "
            "최적: 사진, 비디오 프레임."
        ),
        'modality_audio': (
            "오디오 분석은 음향 특징에 BirdNET 임베딩과 librosa를 사용합니다. "
            "최적: 닭 울음소리 녹음."
        ),
        'input_upload': (
            "컴퓨터에서 파일을 드래그 앤 드롭하거나 클릭하여 업로드합니다."
        ),
        'input_paste': (
            "클립보드에서 직접 이미지를 붙여넣습니다 (Cmd+V 또는 Ctrl+V)."
        ),
        'input_record': (
            "마이크에서 직접 오디오를 녹음합니다. 클릭하여 시작, 다시 클릭하여 중지."
        ),
        'input_folder': (
            "구성된 입력 폴더의 파일을 찾아봅니다 (Data_Bank/Input_Images 또는 Input_Sounds)."
        ),
        'threshold_suggestion': (
            "피드백 패턴을 기반으로 이 새 임계값이 정확도를 향상시킬 수 있습니다. "
            "현재 임계값 근처에서 AI가 오류를 범한 경우를 고려합니다."
        ),
        'apply_threshold': (
            "이 제안된 임계값을 config.yaml에 적용합니다. 변경 사항이 즉시 적용됩니다."
        ),
        'stage_input': (
            "시작점: 폴더에서 파일을 업로드, 붙여넣기, 녹음 또는 선택합니다."
        ),
        'stage_ai': (
            "AI가 컴퓨터 비전(YOLO) 또는 오디오 분석(BirdNET)을 사용하여 파일을 분석합니다."
        ),
        'stage_staging': (
            "파일은 AI 예측과 함께 Data_Bank/Staging/에 저장되어 인간 검토를 기다립니다."
        ),
        'stage_review': (
            "AI 예측이 올바른지 확인합니다. 귀하의 피드백이 중요합니다."
        ),
        'stage_verified': (
            "확인된 파일은 학습 데이터를 위해 Verified_Healthy/ 또는 Verified_Sick/ 폴더로 이동합니다."
        ),
        'stage_feedback': (
            "귀하의 수정 사항이 시스템에 피드백되어 더 나은 정확도를 위해 임계값을 조정합니다."
        ),
        'file_current': (
            "데이터 파이프라인에서 파일의 현재 위치."
        ),
        'file_destination_correct': (
            "AI가 정확하면 파일이 여기로 이동합니다."
        ),
        'file_destination_incorrect': (
            "AI가 틀리면 파일이 반대 카테고리로 이동합니다."
        ),
        'stat_total_staged': (
            "파이프라인이 시작된 이후 검토를 위해 대기된 총 파일 수."
        ),
        'stat_pending': (
            "현재 대기 폴더에서 인간 검증을 기다리는 파일."
        ),
        'stat_validated': (
            "인간이 검토하고 확인/수정한 파일."
        ),
        'stat_session_accuracy': (
            "이 세션만의 정확도. 검증 중 AI와 얼마나 동의했는지 보여줍니다."
        ),
        'reference_healthy': (
            "참조 데이터베이스의 검증된 건강 샘플 수. "
            "새 이미지를 알려진 건강한 닭과 비교하는 데 사용됩니다."
        ),
        'reference_sick': (
            "참조 데이터베이스의 검증된 아픈 샘플 수. "
            "새 이미지를 알려진 아픈 닭과 비교하는 데 사용됩니다."
        ),
        'reference_status': (
            "활성화되면 향상된 정확도를 위해 새 예측이 검증된 샘플과 비교됩니다. "
            "각 카테고리에 최소 3개의 샘플이 필요합니다."
        ),
    },
}


def get_translated_tooltip(key: str) -> str:
    """
    Get a translated tooltip by key.

    Args:
        key: The tooltip key (e.g., 'correct_button', 'health_score')

    Returns:
        The translated tooltip text, or English fallback
    """
    init_language()
    lang = st.session_state.language

    tooltips = TOOLTIPS_TRANSLATIONS.get(lang, TOOLTIPS_TRANSLATIONS['en'])
    return tooltips.get(key, TOOLTIPS_TRANSLATIONS['en'].get(key, "Hover for more information."))


# === HOW IT WORKS TRANSLATIONS ===

HOW_IT_WORKS_TRANSLATIONS = {
    'en': {
        'vision_analysis': {
            'title': 'How Vision Analysis Works',
            'icon': '',
            'content': """
**Step 1: Object Detection (YOLOv10)**
The image is processed by a YOLO model trained to detect chickens.
This identifies the bird's location and generates a bounding box.

**Step 2: Pose Analysis (MediaPipe)**
If a chicken is detected, MediaPipe analyzes body posture - looking
at leg positions, body tilt, and head orientation.

**Step 3: Color Analysis**
The system examines comb and wattle color vibrancy, looking for
pale or discolored areas that might indicate illness.

**Step 4: Health Score**
All factors combine into a health score (0-1). Values above the
threshold indicate HEALTHY, below indicate SICK.
            """,
        },
        'audio_analysis': {
            'title': 'How Audio Analysis Works',
            'icon': '',
            'content': """
**Step 1: Feature Extraction (librosa)**
The audio is analyzed for: pitch (fundamental frequency), volume,
call rate (vocalizations per second), and frequency spectrum.

**Step 2: Neural Embeddings (BirdNET)**
A pre-trained model generates feature vectors that capture
acoustic patterns associated with different bird states.

**Step 3: Pattern Matching**
The extracted features are compared against known patterns
of normal vs distressed chicken vocalizations.

**Step 4: Distress Score**
All factors combine into a distress score (0-1). Higher scores
indicate more distressed vocalizations.
            """,
        },
        'threshold_tuning': {
            'title': 'How Threshold Tuning Works',
            'icon': '',
            'content': """
**The Problem**
A fixed threshold (e.g., 0.5) may not be optimal. Some environments
produce naturally higher or lower scores.

**The Solution**
When you mark an AI prediction as incorrect, the system records:
- The score that was misclassified
- Whether it was a false positive or false negative

**Boundary Region**
The tuner focuses on scores within 0.15 of the current threshold.
Errors far from the boundary suggest model issues, not threshold issues.

**Adjustment**
After enough samples (10+), the system suggests a new threshold:
- False positives (healthy marked sick) → lower threshold
- False negatives (sick marked healthy) → raise threshold

**Applying Changes**
When you apply a new threshold, it's written to config.yaml
and takes effect immediately.
            """,
        },
        'data_flow': {
            'title': "Your Data's Journey",
            'icon': '',
            'content': """
**1. Input**
Files enter the system via upload, clipboard paste, microphone
recording, or selection from input folders.

**2. AI Analysis**
YOLO/MediaPipe (vision) or BirdNET/librosa (audio) process
the file and generate a prediction with confidence score.

**3. Staging**
The file is copied (never moved!) to Data_Bank/Staging/ with
its AI prediction saved in staging_log.csv.

**4. Human Review**
You validate each prediction. Your expertise is essential for
building accurate training data.

**5. Verified**
Confirmed files move to Verified_Healthy/ or Verified_Sick/.
Corrected files move to the opposite folder.

**6. Feedback Loop**
Your corrections improve threshold calibration, making future
predictions more accurate over time.
            """,
        },
        'reference_learning': {
            'title': 'How Reference Learning Works',
            'icon': '',
            'content': """
**The Concept**
Your verified samples become "reference examples" that help classify
future images. New images are compared against these verified samples.

**Building the Database**
Every time you verify an image (clicking Correct or Wrong), its
features are added to the reference database automatically.

**How Comparison Works**
When analyzing a new image, the system:
1. Extracts features (posture, color, texture, alignment)
2. Finds the 5 most similar verified images
3. Calculates average similarity to healthy vs sick samples
4. Adjusts the health score based on which class is more similar

**Example**
- New image has base health score: 0.55 (borderline)
- Very similar to 3 verified healthy samples (avg similarity: 0.8)
- Less similar to sick samples (avg similarity: 0.4)
- Adjustment: (0.8 - 0.4) × 0.3 = +0.12
- Final score: 0.67 → Confidently HEALTHY

**Requirements**
Need at least 3 verified samples in each category (healthy/sick)
before reference comparison activates.

**Settings (config.yaml)**
- `min_samples_per_class`: Samples needed per category (default: 3)
- `similarity_weight`: How much to trust reference similarity (default: 0.3)
- `k_neighbors`: Number of similar samples to consider (default: 5)
            """,
        },
    },
    'ko': {
        'vision_analysis': {
            'title': '이미지 분석 작동 방식',
            'icon': '',
            'content': """
**1단계: 객체 감지 (YOLOv10)**
이미지는 닭을 감지하도록 훈련된 YOLO 모델로 처리됩니다.
이것은 새의 위치를 식별하고 경계 상자를 생성합니다.

**2단계: 자세 분석 (MediaPipe)**
닭이 감지되면 MediaPipe가 신체 자세를 분석합니다 -
다리 위치, 몸 기울기, 머리 방향을 확인합니다.

**3단계: 색상 분석**
시스템은 볏과 볏의 색상 선명도를 검사하여
질병을 나타낼 수 있는 창백하거나 변색된 부분을 찾습니다.

**4단계: 건강 점수**
모든 요소가 건강 점수(0-1)로 결합됩니다. 임계값 이상의 값은
건강을, 이하는 아픔을 나타냅니다.
            """,
        },
        'audio_analysis': {
            'title': '오디오 분석 작동 방식',
            'icon': '',
            'content': """
**1단계: 특징 추출 (librosa)**
오디오는 음높이(기본 주파수), 음량, 울음 빈도
(초당 발성), 주파수 스펙트럼을 분석합니다.

**2단계: 신경 임베딩 (BirdNET)**
사전 훈련된 모델이 다양한 새 상태와 관련된
음향 패턴을 캡처하는 특징 벡터를 생성합니다.

**3단계: 패턴 매칭**
추출된 특징은 정상 대 이상한 닭 울음소리의
알려진 패턴과 비교됩니다.

**4단계: 이상 점수**
모든 요소가 이상 점수(0-1)로 결합됩니다. 높은 점수는
더 이상한 울음소리를 나타냅니다.
            """,
        },
        'threshold_tuning': {
            'title': '임계값 조정 작동 방식',
            'icon': '',
            'content': """
**문제점**
고정된 임계값(예: 0.5)은 최적이 아닐 수 있습니다. 일부 환경은
자연적으로 더 높거나 낮은 점수를 생성합니다.

**해결책**
AI 예측을 틀렸다고 표시하면 시스템이 기록합니다:
- 잘못 분류된 점수
- 거짓 양성인지 거짓 음성인지

**경계 영역**
튜너는 현재 임계값의 0.15 이내의 점수에 집중합니다.
경계에서 멀리 떨어진 오류는 임계값 문제가 아닌 모델 문제를 시사합니다.

**조정**
충분한 샘플(10+) 후에 시스템이 새 임계값을 제안합니다:
- 거짓 양성(건강을 아픔으로 표시) → 임계값 낮추기
- 거짓 음성(아픔을 건강으로 표시) → 임계값 높이기

**변경 사항 적용**
새 임계값을 적용하면 config.yaml에 기록되고
즉시 적용됩니다.
            """,
        },
        'data_flow': {
            'title': '데이터의 여정',
            'icon': '',
            'content': """
**1. 입력**
파일은 업로드, 클립보드 붙여넣기, 마이크
녹음 또는 입력 폴더에서 선택하여 시스템에 들어옵니다.

**2. AI 분석**
YOLO/MediaPipe(이미지) 또는 BirdNET/librosa(오디오)가
파일을 처리하고 신뢰도 점수와 함께 예측을 생성합니다.

**3. 대기**
파일은 (이동이 아닌!) Data_Bank/Staging/에 복사되고
AI 예측이 staging_log.csv에 저장됩니다.

**4. 인간 검토**
각 예측을 검증합니다. 정확한 학습 데이터를 구축하는 데
귀하의 전문 지식이 필수적입니다.

**5. 검증됨**
확인된 파일은 Verified_Healthy/ 또는 Verified_Sick/로 이동합니다.
수정된 파일은 반대 폴더로 이동합니다.

**6. 피드백 루프**
귀하의 수정 사항이 임계값 조정을 개선하여
시간이 지남에 따라 향후 예측을 더 정확하게 만듭니다.
            """,
        },
        'reference_learning': {
            'title': '참조 학습 작동 방식',
            'icon': '',
            'content': """
**개념**
검증된 샘플이 향후 이미지 분류에 도움이 되는 "참조 예제"가 됩니다.
새 이미지는 이러한 검증된 샘플과 비교됩니다.

**데이터베이스 구축**
이미지를 검증할 때마다(정확함 또는 오류 클릭), 해당
특징이 자동으로 참조 데이터베이스에 추가됩니다.

**비교 작동 방식**
새 이미지를 분석할 때 시스템은:
1. 특징 추출(자세, 색상, 질감, 정렬)
2. 가장 유사한 검증된 이미지 5개 찾기
3. 건강 대 아픈 샘플에 대한 평균 유사성 계산
4. 더 유사한 클래스에 따라 건강 점수 조정

**예시**
- 새 이미지의 기본 건강 점수: 0.55(경계선)
- 검증된 건강 샘플 3개와 매우 유사(평균 유사성: 0.8)
- 아픈 샘플과는 덜 유사(평균 유사성: 0.4)
- 조정: (0.8 - 0.4) × 0.3 = +0.12
- 최종 점수: 0.67 → 확실히 건강

**요구 사항**
참조 비교가 활성화되기 전에 각 카테고리(건강/아픔)에
최소 3개의 검증된 샘플이 필요합니다.

**설정 (config.yaml)**
- `min_samples_per_class`: 카테고리당 필요한 샘플(기본값: 3)
- `similarity_weight`: 참조 유사성 신뢰도(기본값: 0.3)
- `k_neighbors`: 고려할 유사 샘플 수(기본값: 5)
            """,
        },
    },
}


def get_translated_how_it_works(key: str) -> dict:
    """
    Get a translated 'How it works' section by key.

    Args:
        key: The section key (e.g., 'vision_analysis', 'threshold_tuning')

    Returns:
        dict with 'title', 'icon', and 'content' keys
    """
    init_language()
    lang = st.session_state.language

    sections = HOW_IT_WORKS_TRANSLATIONS.get(lang, HOW_IT_WORKS_TRANSLATIONS['en'])
    return sections.get(key, HOW_IT_WORKS_TRANSLATIONS['en'].get(key, {
        'title': 'How It Works',
        'icon': '',
        'content': 'Information about this feature.',
    }))
