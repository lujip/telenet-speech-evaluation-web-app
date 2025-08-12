# Segmented Evaluation Structure

This document describes the new segmented structure for applicant evaluation data in the `temp_evaluation` JSON files.

## Overview

The evaluation system now organizes applicant assessment data into four distinct sections, making it easier to categorize and analyze different types of evaluations:

- **`speech_eval`**: Speech evaluation results from audio recordings
- **`listening_test`**: Listening comprehension test results
- **`written_test`**: Written response test results
- **`typing_test`**: Typing speed and accuracy test results

## Structure

```json
{
  "speech_eval": [
    {
      "question": "Question text",
      "transcript": "Speech-to-text transcript",
      "audio_metrics": {
        "duration": 12.5,
        "avg_pitch_hz": 180.25,
        "estimated_wpm": 120.0
      },
      "evaluation": {
        "score": 85,
        "category_scores": {
          "relevance": 90,
          "grammar_lexis": 85,
          "communication_skills": 88,
          "fluency_pronunciation": 82,
          "customer_service_fit": 87
        },
        "comment": "Evaluation feedback"
      },
      "timestamp": "2025-01-15T10:00:00",
      "audio_path": "path/to/audio/file.wav"
    }
  ],
  "listening_test": [
    {
      "type": "listening",
      "test_id": "LT001",
      "score": 92,
      "questions_correct": 9,
      "total_questions": 10,
      "time_taken": 180,
      "timestamp": "2025-01-15T11:00:00"
    }
  ],
  "written_test": [
    {
      "type": "written",
      "test_id": "WT001",
      "score": 87,
      "time_taken": 300,
      "timestamp": "2025-01-15T11:30:00",
      "response": "Written response text",
      "evaluation": {
        "grammar": 85,
        "clarity": 90,
        "professionalism": 88,
        "problem_solving": 86
      }
    }
  ],
  "typing_test": [
    {
      "type": "typing",
      "test_id": 1,
      "timestamp": "2025-01-15T12:00:00",
      "typed_text": "Typed text content",
      "typed_words": 45,
      "time_taken_seconds": 58,
      "words_per_minute": 46.55,
      "accuracy_percentage": 95
    }
  ]
}
```

## Benefits

1. **Better Organization**: Clear separation of different evaluation types
2. **Easier Analysis**: Administrators can quickly assess specific skill areas
3. **Scalability**: Easy to add new evaluation types in the future
4. **Data Integrity**: Structured format prevents data mixing
5. **Backward Compatibility**: Existing data is automatically migrated

## Implementation Details

### File Operations

The `save_temp_evaluation()` function now:
- Creates the segmented structure for new evaluations
- Merges new data with existing sections
- Preserves data across multiple evaluation sessions
- Automatically migrates old format data

### Data Migration

Existing `temp_evaluation` files are automatically migrated:
- Old `evaluations` array → `speech_eval` section
- New sections are initialized as empty arrays
- No data loss during migration

### API Integration

All existing API endpoints continue to work:
- Speech evaluation → `speech_eval` section
- Typing test → `typing_test` section
- Future listening/written tests → respective sections

## Usage Examples

### Adding Speech Evaluation

```python
from utils.file_ops import save_temp_evaluation

speech_data = {
    "speech_eval": [{
        "question": "How would you handle a difficult customer?",
        "transcript": "I would listen carefully...",
        "evaluation": {"score": 85}
    }]
}

save_temp_evaluation(speech_data, session_id)
```

### Adding Typing Test Results

```python
typing_data = {
    "typing_test": [{
        "type": "typing",
        "wpm": 45,
        "accuracy": 95
    }]
}

save_temp_evaluation(typing_data, session_id)
```

### Loading All Evaluations

```python
from utils.file_ops import load_temp_evaluation

eval_data = load_temp_evaluation(session_id)

# Access specific sections
speech_results = eval_data.get("speech_eval", [])
typing_results = eval_data.get("typing_test", [])
listening_results = eval_data.get("listening_test", [])
written_results = eval_data.get("written_test", [])

# Get total count
total_evaluations = len(speech_results) + len(typing_results) + len(listening_results) + len(written_results)
```

## Migration

To migrate existing evaluation files:

```bash
cd backend
python migrate_eval_structure.py
```

This will automatically convert all existing `temp_evaluation_*.json` files to the new segmented structure.

## Testing

Run the test script to verify the new structure:

```bash
cd backend
python test_segmented_eval.py
```

## Future Enhancements

The segmented structure makes it easy to add new evaluation types:

1. **Video Tests**: Add `video_test` section
2. **Technical Assessments**: Add `technical_test` section
3. **Personality Tests**: Add `personality_test` section
4. **Custom Evaluations**: Add application-specific sections

## File Locations

- **Backend**: `backend/utils/file_ops.py` - Core functions
- **Routes**: Updated to use segmented structure
- **Migration**: `backend/migrate_eval_structure.py`
- **Test**: `backend/test_segmented_eval.py`
- **Example**: `backend/example_segmented_evaluation.json`

## Notes

- All sections are arrays, allowing multiple evaluations per type
- Empty sections are initialized as empty arrays `[]`
- Timestamps are stored in ISO format for consistency
- The structure is backward compatible with existing code
- Data is automatically merged when saving multiple times 