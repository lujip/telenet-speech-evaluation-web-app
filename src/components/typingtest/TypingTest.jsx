import React, { useState, useEffect, useRef } from 'react'
import './TypingTest.css'

const TypingTest = ({ onComplete, onNext, sessionId }) => {
  const [testData, setTestData] = useState(null)
  const [typedText, setTypedText] = useState('')
  const [timeLeft, setTimeLeft] = useState(60)
  const [isActive, setIsActive] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [wpm, setWpm] = useState(0)
  const [accuracy, setAccuracy] = useState(0)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  
  const inputRef = useRef(null)
  const timerRef = useRef(null)
  const completionTriggeredRef = useRef(false)

  const API_URL = import.meta.env.VITE_API_URL;

  // Fetch typing test on component mount
  useEffect(() => {
    fetchTypingTest()
  }, [])

  // Timer countdown
  useEffect(() => {
    if (isActive && timeLeft > 0) {
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            // Don't call handleTestComplete here, just return 0
            // The useEffect will handle the completion when timeLeft becomes 0
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [isActive, timeLeft])

  // Handle completion when timer reaches 0
  useEffect(() => {
    if (isActive && timeLeft === 0 && !isComplete && !completionTriggeredRef.current) {
      completionTriggeredRef.current = true
      // Use setTimeout to defer the completion call to avoid state update during render
      const completionTimeout = setTimeout(() => {
        if (isActive && timeLeft === 0 && !isComplete) {
          handleTestComplete()
        }
      }, 100)
      
      return () => clearTimeout(completionTimeout)
    }
  }, [timeLeft, isActive, isComplete])

  const fetchTypingTest = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`${API_URL}/typing/test`)
      const data = await response.json()
      
      if (data.success) {
        setTestData(data.test)
        setError('')
      } else {
        setError(data.message || 'Failed to load typing test')
      }
    } catch {
      setError('Network error: Could not load typing test')
    } finally {
      setIsLoading(false)
    }
  }

  const startTest = () => {
    setIsActive(true)
    setTimeLeft(60)
    setTypedText('')
    setWpm(0)
    setAccuracy(0)
    setIsComplete(false)
    completionTriggeredRef.current = false
    inputRef.current?.focus()
  }

  const handleInputChange = (e) => {
    if (!isActive || isComplete) return
    
    const value = e.target.value
    setTypedText(value)
    
    // Calculate accuracy
    if (testData) {
      const expectedWords = testData.text.split(' ')
      const typedWords = value.split(' ').filter(word => word.trim() !== '')
      
      let correctWords = 0
      typedWords.forEach((word, index) => {
        if (expectedWords[index] && word === expectedWords[index]) {
          correctWords++
        }
      })
      
      const accuracyPercent = typedWords.length > 0 ? (correctWords / typedWords.length) * 100 : 0
      setAccuracy(Math.round(accuracyPercent))
    }
  }

  // Handle test completion
  const handleTestComplete = () => {
    // Prevent multiple completion calls
    if (isComplete) return;
    
    // Set completion state first
    setIsComplete(true);
    setIsActive(false);
    
    // Clear the timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    
    // Calculate final WPM
    const typedWords = typedText.split(' ').filter(word => word.trim() !== '').length
    const timeMinutes = (60 - timeLeft) / 60
    const finalWpm = timeMinutes > 0 ? Math.round((typedWords / timeMinutes) * 100) / 100 : 0
    
    // Update local state
    setWpm(finalWpm);
    
    // Use setTimeout to defer the callback calls to avoid state update during render
    setTimeout(async () => {
      try {
        // Save typing test results to backend first
        const typingResult = {
          session_id: sessionId || "test_session",
          test_id: testData?.id || 1,
          typed_text: typedText,
          time_taken: 60 - timeLeft,
          accuracy: accuracy
        };
        
        const response = await fetch(`${API_URL}/typing/submit`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(typingResult)
        });
        
        if (response.ok) {
          const result = await response.json();
          console.log('✅ Typing test results saved successfully:', result);
        } else {
          console.error('❌ Failed to save typing test results:', response.status);
          const errorText = await response.text();
          console.error('Error response:', errorText);
        }
      } catch (error) {
        console.error('Error saving typing test results:', error);
      }
      
      // Call onComplete callback with results
      if (onComplete) {
        onComplete({
          testType: 'typing',
          score: finalWpm,
          wpm: finalWpm,
          accuracy: accuracy,
          results: {
            wpm: finalWpm,
            accuracy: accuracy,
            wordsTyped: typedWords,
            timeTaken: 60 - timeLeft
          }
        });
      }
      
      // Move to next test
      if (onNext) {
        onNext();
      }
    }, 100);
  };



  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (isLoading) {
    return (
      <div className="typing-test-container">
        <div className="loading">Loading typing test...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="typing-test-container">
        <div className="error">{error}</div>
        <button onClick={fetchTypingTest} className="retry-btn">Retry</button>
      </div>
    )
  }

  if (!testData) {
    return (
      <div className="typing-test-container">
        <div className="error">No typing test available</div>
      </div>
    )
  }

  return (
    <div className="typing-test-container">
      <div className="test-header">
        <h2>Typing Test</h2>
        <div className="test-info">
          <span>Duration: 60 seconds</span>
          <span>Type the text as accurately as possible</span>
        </div>
      </div>

      {!isActive && !isComplete && (
        <div className="test-instructions">
          <p>You will have 60 seconds to type the text below as accurately as possible.</p>
          <p>Your typing speed (WPM) and accuracy will be recorded.</p>
          <button onClick={startTest} className="start-btn">Start Test</button>
        </div>
      )}

      {isActive && (
        <div className="test-active">
          <div className="timer">Time Remaining: {formatTime(timeLeft)}</div>
          <div className="text-display">
            <p>{testData.text}</p>
          </div>
          <div className="input-section">
            <textarea
              ref={inputRef}
              value={typedText}
              onChange={handleInputChange}
              onPaste={(e) => {
                e.preventDefault();
                return false;
              }}
              placeholder="Start typing here..."
              disabled={!isActive || isComplete}
              className="typing-input"
            />
          </div>
          <div className="stats">
            <span>Accuracy: {accuracy}%</span>
            <span>Words Typed: {typedText.split(' ').filter(word => word.trim() !== '').length}</span>
          </div>
          <div className="test-controls">
            <button 
              onClick={handleTestComplete} 
              className="complete-btn"
              disabled={isComplete}
            >
              Complete Test Early
            </button>
          </div>
        </div>
      )}

      {isComplete && (
        <div className="test-results">
          <h3>Test Complete!</h3>
          <div className="results-grid">
            <div className="result-item">
              <label>Words Per Minute:</label>
              <span className="wpm-display">{wpm}</span>
            </div>
            <div className="result-item">
              <label>Accuracy:</label>
              <span>{accuracy}%</span>
            </div>
            <div className="result-item">
              <label>Words Typed:</label>
              <span>{typedText.split(' ').filter(word => word.trim() !== '').length}</span>
            </div>
            <div className="result-item">
              <label>Time Taken:</label>
              <span>{formatTime(60 - timeLeft)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TypingTest