# Typing Test System

This document describes the typing test functionality that has been added to your speech evaluation system.

## Overview

The typing test system allows applicants to take a 60-second typing test that measures their words per minute (WPM) and accuracy. The results are stored alongside other evaluation data and can be used for comprehensive applicant assessment.

## Features

- **60-second timer** with countdown display
- **Predefined test content** stored in JSON format
- **Real-time accuracy calculation** based on word matching
- **WPM calculation** (words per minute)
- **Responsive design** for mobile and desktop
- **Session-based storage** using temporary evaluation files
- **Integration** with existing applicant evaluation system

## File Structure

```
backend/
├── data/
│   └── typing_tests.json          # Predefined typing test content
├── routes/
│   └── typing.py                  # Typing test API endpoints
└── config.py                      # Updated with typing test file path

src/components/typingtest/
├── TypingTest.jsx                 # Main typing test component
├── TypingTest.css                 # Styling for the component
└── TypingTestDemo.jsx             # Demo page for testing
```

## API Endpoints

### GET `/typing/test`
Retrieves a random typing test for the applicant.

**Response:**
```json
{
  "success": true,
  "test": {
    "id": 1,
    "title": "Basic Customer Service",
    "text": "Welcome to our customer service team...",
    "word_count": 45,
    "difficulty": "easy",
    "category": "customer_service"
  }
}
```

### POST `/typing/submit`
Submits typing test results and calculates WPM.

**Request Body:**
```json
{
  "session_id": "session-123",
  "test_id": 1,
  "typed_text": "Welcome to our customer...",
  "time_taken": 58,
  "accuracy": 95
}
```

**Response:**
```json
{
  "success": true,
  "message": "Typing test results saved successfully",
  "result": {
    "wpm": 46.55,
    "accuracy": 95,
    "words_typed": 45,
    "time_taken": 58
  }
}
```

## Data Storage

Typing test results are stored in the temporary evaluation file for each session:

```json
{
  "evaluations": [
    {
      "type": "typing",
      "test_id": 1,
      "timestamp": "2024-01-15T10:30:00",
      "typed_text": "Welcome to our customer...",
      "typed_words": 45,
      "time_taken_seconds": 58,
      "words_per_minute": 46.55,
      "accuracy_percentage": 95
    }
  ]
}
```

When the applicant completes all tests, this data is combined with other evaluation results and stored in the main applicants.json file.

## Usage

### Basic Integration

```jsx
import TypingTest from './components/typingtest/TypingTest'

function App() {
  const handleTypingComplete = (results) => {
    console.log('WPM:', results.wpm)
    console.log('Accuracy:', results.accuracy)
    // Handle completion
  }

  return (
    <TypingTest 
      sessionId="unique-session-id"
      onComplete={handleTypingComplete}
    />
  )
}
```

### Props

- **`sessionId`** (required): Unique identifier for the applicant's session
- **`onComplete`** (optional): Callback function called when test is completed

### Test Content

The system includes 5 predefined typing tests with different difficulty levels:

1. **Basic Customer Service** (Easy, 45 words)
2. **Technical Support** (Medium, 67 words)
3. **Sales and Marketing** (Medium, 89 words)
4. **Problem Resolution** (Hard, 112 words)
5. **General Communication** (Easy, 38 words)

## Customization

### Adding New Tests

To add new typing tests, edit `backend/data/typing_tests.json`:

```json
{
  "id": 6,
  "title": "New Test Title",
  "difficulty": "medium",
  "word_count": 75,
  "text": "Your new test content here...",
  "category": "custom"
}
```

### Modifying Test Parameters

- **Timer duration**: Change the `timeLeft` state in `TypingTest.jsx`
- **Scoring algorithm**: Modify the WPM calculation in the backend route
- **Styling**: Update `TypingTest.css` for visual customization

## Testing

1. **Start the backend server** (ensure typing blueprint is registered)
2. **Use the demo component** (`TypingTestDemo.jsx`) to test functionality
3. **Check the console** for test completion logs
4. **Verify data storage** in temporary evaluation files

## Error Handling

The system includes comprehensive error handling for:
- Network failures
- Invalid session IDs
- Missing test data
- File system errors

## Performance Considerations

- **Real-time accuracy calculation** updates on every keystroke
- **Efficient word counting** using JavaScript string methods
- **Minimal API calls** (one for test retrieval, one for submission)
- **Responsive UI** with smooth animations and transitions

## Future Enhancements

Potential improvements could include:
- **Difficulty-based test selection**
- **Custom test creation** by administrators
- **Advanced accuracy metrics** (character-level precision)
- **Performance analytics** and benchmarking
- **Multi-language support**
- **Accessibility features** (screen reader support, keyboard navigation)

## Troubleshooting

### Common Issues

1. **Test not loading**: Check if `typing_tests.json` exists and is valid JSON
2. **Results not saving**: Verify session ID is being passed correctly
3. **Timer issues**: Check for JavaScript errors in browser console
4. **Styling problems**: Ensure CSS file is properly imported

### Debug Mode

Enable debug logging by checking the browser console and backend server logs for detailed error information. 