# Audio Recording Organization System

This document describes the implementation of the audio recording organization system for the speech evaluation application.

## Overview

The system now organizes and saves audio recordings per applicant and question, allowing administrators to replay recorded answers in the admin panel.

## File Structure

```
backend/
├── recordings/
│   ├── {applicantId}/
│   │   ├── q0.wav
│   │   ├── q1.wav
│   │   ├── q2.wav
│   │   └── ...
│   └── ...
├── data/
│   └── applicants.json
└── app.py
```

## Implementation Details

### 1. Backend Changes

#### New Functions Added:
- `ensure_recordings_directory(applicant_id)`: Creates the recordings directory for a specific applicant
- `serve_audio(filename)`: Serves audio files from the recordings directory

#### Modified Routes:
- `/evaluate`: Now saves audio files with organized paths and includes `audio_path` in evaluation results
- `/recordings/<path:filename>`: New route to serve audio files

#### Audio File Naming Convention:
- Format: `recordings/{applicantId}/q{questionIndex}.wav`
- Example: `recordings/juan_dela_cruz_1721112233/q1.wav`

### 2. Frontend Changes

#### App.jsx:
- Added `question_index` to the form data sent to the `/evaluate` endpoint
- Uses `currentQuestionIndex` to track which question is being answered

#### Admin.jsx:
- Added audio player display for each evaluation
- Shows audio file path for debugging
- Includes error handling for missing audio files

### 3. Data Structure

Each evaluation now includes an `audio_path` field:

```json
{
  "question": "How would you handle a customer who is angry?",
  "transcript": "...",
  "audio_metrics": {...},
  "evaluation": {...},
  "comment": "...",
  "timestamp": "2024-01-15T10:30:00",
  "audio_path": "recordings/juan_dela_cruz_1721112233/q1.wav"
}
```

## Usage

### For Applicants:
1. Start recording an answer
2. The system automatically saves the audio file to `recordings/{sessionId}/q{questionIndex}.wav`
3. The audio path is stored with the evaluation data

### For Administrators:
1. Access the admin panel
2. View any applicant's detailed evaluation
3. Each question will show an audio player if a recording exists
4. Click play to hear the original recorded answer

## Testing

Run the test script to verify audio file serving:

```bash
cd backend
python test_audio_serving.py
```

## Error Handling

- If an audio file is missing, the admin panel shows "Audio file not available"
- Console warnings are logged for debugging
- The system gracefully handles missing files without breaking the UI

## Security Considerations

- Audio files are served from a dedicated `/recordings/` route
- File paths are validated to prevent directory traversal attacks
- Only WAV files are served from the recordings directory

## Future Enhancements

- Add audio file compression to save storage space
- Implement audio file cleanup for old recordings
- Add audio waveform visualization
- Support for different audio formats (MP3, OGG)
- Audio file download functionality for administrators 