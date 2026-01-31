# Human Feedback System Documentation

## Overview

Sentio uses a **human-in-the-loop** approach where your feedback directly improves AI accuracy through threshold calibration. Instead of retraining the underlying models (YOLOv10, BirdNET), the system learns the optimal decision boundaries from your corrections.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEEDBACK DATA FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User uploads image/audio                                       │
│           │                                                     │
│           ▼                                                     │
│  AI analyzes (YOLOv10 or BirdNET)                              │
│           │                                                     │
│           ▼                                                     │
│  File copied to Staging/ + logged in staging_log.csv           │
│           │                                                     │
│           ▼                                                     │
│  Human reviews in "Review Staged" mode                         │
│           │                                                     │
│           ▼                                                     │
│  User clicks "Correct" or "Wrong"                              │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ON FEEDBACK:                                            │   │
│  │                                                          │   │
│  │  1. staging_log.csv updated:                             │   │
│  │     • human_validated = True                             │   │
│  │     • human_agrees = True/False                          │   │
│  │     • final_classification = corrected label             │   │
│  │                                                          │   │
│  │  2. File moved:                                          │   │
│  │     Staging/ → Verified_Healthy/ or Verified_Sick/       │   │
│  │                                                          │   │
│  │  3. threshold_history.json updated:                      │   │
│  │     • Records score, prediction, human_agrees            │   │
│  │     • Recalculates suggested threshold                   │   │
│  │                                                          │   │
│  │  4. Statistics recalculated:                             │   │
│  │     • accuracy = ai_correct / validated                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  After 10+ boundary errors → threshold suggestion appears       │
│           │                                                     │
│           ▼                                                     │
│  User clicks "Apply 0.52 Threshold" → config.yaml updated      │
│           │                                                     │
│           ▼                                                     │
│  Future predictions use new threshold                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `threshold_tuner.py` | Core threshold calculation logic |
| `data_pipeline.py` | File movement, CSV logging, statistics |
| `training_app_v2.py:727-791` | `handle_feedback()` function |
| `config.yaml:57-63` | Threshold tuning settings |

## Data Storage

### 1. Staging Log (`Data_Bank/Staging/staging_log.csv`)

Records every AI prediction and human validation:

| Column | Description |
|--------|-------------|
| `timestamp` | When the file was analyzed |
| `original_file` | Original filename |
| `staged_file` | Timestamped filename in staging |
| `modality` | `vision` or `audio` |
| `ai_classification` | AI's prediction (HEALTHY/SICK/NORMAL/DISTRESS) |
| `confidence` | Score from 0-1 |
| `features` | JSON blob of extracted features |
| `human_validated` | True/False |
| `human_agrees` | True/False/None |
| `final_classification` | Corrected label after human review |
| `validated_at` | Timestamp of validation |

### 2. Threshold History (`Data_Bank/threshold_history.json`)

Tracks feedback for threshold optimization:

```json
{
  "vision": {
    "feedback": [
      {
        "timestamp": "2026-01-31T13:44:22",
        "score": 0.48,
        "ai_prediction": "HEALTHY",
        "human_agrees": false,
        "current_threshold": 0.5
      }
    ],
    "current_threshold": 0.5,
    "suggested_threshold": 0.52,
    "last_updated": "2026-01-31T14:00:00"
  },
  "audio": { ... }
}
```

### 3. Verified Folders

```
Data_Bank/
├── Staging/              # Files awaiting human review
├── Verified_Healthy/     # Confirmed healthy/normal samples
├── Verified_Sick/        # Confirmed sick/distress samples
└── threshold_history.json
```

## Threshold Tuning Algorithm

### The Learning Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│  THRESHOLD TUNING CYCLE                                          │
│                                                                  │
│  1. AI predicts: HEALTHY (score: 0.48, threshold: 0.50)         │
│                                                                  │
│  2. Human reviews: "That's WRONG - it's actually SICK"          │
│                                                                  │
│  3. ThresholdTuner records:                                      │
│     • Score was 0.48 (near threshold = boundary error)          │
│     • AI said HEALTHY but was wrong                             │
│     • Conclusion: threshold too LOW (letting sick chickens pass)│
│                                                                  │
│  4. After 10+ similar errors:                                    │
│     • System suggests: "Raise threshold to 0.52"                │
│     • User clicks "Apply" button                                │
│                                                                  │
│  5. Future predictions:                                          │
│     • Same 0.48 score now classified as SICK (below 0.52)       │
│     • AI accuracy improves WITHOUT retraining the model         │
└─────────────────────────────────────────────────────────────────┘
```

### Boundary Region Logic

The tuner focuses on **boundary errors** - mistakes near the decision threshold:

- **Boundary region**: Within ±0.15 of the current threshold
- **Why boundary matters**: Errors far from the threshold indicate model problems, not threshold problems
- **Adjustment direction**:
  - AI said HEALTHY but was wrong → threshold too LOW → raise it
  - AI said SICK but was wrong → threshold too HIGH → lower it

### Configuration (`config.yaml`)

```yaml
threshold_tuning:
  enabled: true
  min_samples_before_update: 10    # Reviews needed before suggestion
  learning_rate: 0.1                # How aggressively to adjust (0.05-0.2)
  history_file: Data_Bank/threshold_history.json
```

## UI Components

### Right Panel - AI Learning Progress

Shows:
- **Sample count**: Total feedback instances
- **Progress bar**: Fills toward 10 samples (minimum for suggestions)
- **Accuracy percentage**: AI correct / total validated

### Right Panel - Feedback Loop Status

Shows:
- **Current threshold**: Active decision boundary
- **Suggested threshold**: Calculated from boundary errors (after 10+ samples)
- **"Apply" button**: Updates `config.yaml` when clicked

## Verification Commands

Check current data state:

```bash
# View staging log
cat Data_Bank/Staging/staging_log.csv

# View threshold history
cat Data_Bank/threshold_history.json

# Check verified folders
ls -la Data_Bank/Verified_Healthy/
ls -la Data_Bank/Verified_Sick/

# Get pipeline statistics (CLI)
python data_pipeline.py stats

# List pending reviews
python data_pipeline.py list
```

## Why Threshold Tuning (Not Model Retraining)

| Aspect | Threshold Tuning | Model Retraining |
|--------|------------------|------------------|
| **Hardware** | No GPU needed | Requires GPU |
| **Speed** | Instant effect | Hours/days |
| **Reversibility** | Easy to adjust back | Complex rollback |
| **Data needs** | 10+ samples | 100s-1000s samples |
| **Risk** | Low - just moves boundary | High - can degrade model |

## Testing the System

Run the test script to verify everything works:

```bash
python test_feedback_loop.py
```

This tests:
1. CSV logging functionality
2. Threshold history updates
3. File movement to verified folders
4. Threshold calculation logic
5. End-to-end feedback flow

## Troubleshooting

### No threshold suggestion appears

- Need 10+ samples with boundary errors
- Errors must be within ±0.15 of threshold
- Check `threshold_history.json` for feedback count

### Files not moving to verified folders

- Check staging log for `human_validated` status
- Verify folder permissions
- Check `data_pipeline.py` logs

### Threshold not updating after clicking Apply

- Check if `config.yaml` is writable
- Verify suggested differs from current by >0.01
- Check console for error messages
