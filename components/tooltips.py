"""
Sentio Training App - Tooltip System

Comprehensive tooltips for every UI element, plus expandable
"How it works" explanations for complex concepts.
"""


# Main tooltip dictionary - organized by category
TOOLTIPS = {
    # === FEEDBACK BUTTONS ===
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

    # === ACTION BUTTONS ===
    'analyze_button': (
        "Run AI analysis using YOLOv10 (for images) or BirdNET (for audio) "
        "to predict whether this chicken is healthy or showing signs of distress."
    ),
    'stage_button': (
        "Save this file and AI prediction to Data_Bank/Staging/ for human verification. "
        "The original file stays untouched."
    ),

    # === METRICS ===
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

    # === MODE SELECTION ===
    'mode_review': (
        "Review mode: Validate AI predictions on staged files. Confirm or correct "
        "each prediction to improve the model's accuracy."
    ),
    'mode_analyze': (
        "Analyze mode: Process new files through the AI. Upload, paste, record, "
        "or select files from the input folder."
    ),

    # === MODALITY ===
    'modality_vision': (
        "Vision analysis uses YOLOv10 for object detection and MediaPipe for "
        "posture analysis. Best for: photos, video frames."
    ),
    'modality_audio': (
        "Audio analysis uses BirdNET embeddings and librosa for acoustic features. "
        "Best for: recordings of chicken vocalizations."
    ),

    # === INPUT METHODS ===
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

    # === THRESHOLD TUNING ===
    'threshold_suggestion': (
        "Based on feedback patterns, this new threshold may improve accuracy. "
        "It considers cases where the AI made errors near the current threshold."
    ),
    'apply_threshold': (
        "Apply this suggested threshold to config.yaml. The change takes effect immediately."
    ),

    # === DATA FLOW STAGES ===
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

    # === FILE LOCATIONS ===
    'file_current': (
        "The file's current location in the data pipeline."
    ),
    'file_destination_correct': (
        "If AI is correct, the file moves here."
    ),
    'file_destination_incorrect': (
        "If AI is wrong, the file moves to the opposite category."
    ),

    # === STATISTICS ===
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

    # === REFERENCE LEARNING ===
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
}


def get_tooltip(key: str) -> str:
    """
    Get a tooltip by key, with fallback for unknown keys.

    Args:
        key: The tooltip key (e.g., 'correct_button', 'health_score')

    Returns:
        The tooltip text, or a default message if key not found
    """
    return TOOLTIPS.get(key, "Hover for more information about this element.")


# === HOW IT WORKS SECTIONS ===
# Longer explanations for expandable sections

HOW_IT_WORKS = {
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
    'file_locations': {
        'title': 'File Location Guide',
        'icon': '',
        'content': """
**Input Folders**
- `Data_Bank/Input_Images/` - Drop images here for batch processing
- `Data_Bank/Input_Sounds/` - Drop audio files here

**Staging**
- `Data_Bank/Staging/` - Files awaiting human review
- `staging_log.csv` - Tracks all staged files and predictions

**Verified (Training Data)**
- `Data_Bank/Verified_Healthy/` - Confirmed healthy samples
- `Data_Bank/Verified_Sick/` - Confirmed sick/distressed samples

**Temp (Auto-cleaned)**
- Uploaded/pasted/recorded files are temporarily saved here
- Automatically cleaned after 24 hours
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
}


def get_how_it_works(key: str) -> dict:
    """
    Get a 'How it works' section by key.

    Args:
        key: The section key (e.g., 'vision_analysis', 'threshold_tuning')

    Returns:
        dict with 'title', 'icon', and 'content' keys
    """
    return HOW_IT_WORKS.get(key, {
        'title': 'How It Works',
        'icon': '',
        'content': 'Information about this feature.',
    })


def render_tooltip_icon(st, key: str, position: str = 'right'):
    """
    Render an info icon with popover tooltip.

    Args:
        st: Streamlit module
        key: The tooltip key
        position: Position of the icon ('left' or 'right')
    """
    tooltip_text = get_tooltip(key)
    st.markdown(f'<span title="{tooltip_text}"></span>', unsafe_allow_html=True)


def render_how_it_works_expander(st, key: str):
    """
    Render an expandable 'How it works' section.

    Args:
        st: Streamlit module
        key: The section key
    """
    section = get_how_it_works(key)
    with st.expander(f"{section['icon']} {section['title']}"):
        st.markdown(section['content'])
