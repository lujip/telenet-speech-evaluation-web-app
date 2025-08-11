import React, { useState, useEffect, useRef } from 'react'
import './TypingTest.css'

const TypingTest = ({ sessionId, onComplete }) => {
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
            handleTestComplete()
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

  const fetchTypingTest = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('http://localhost:5000/typing/test')
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

  const handleTestComplete = async () => {
    setIsActive(false)
    setIsComplete(true)
    
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }

    // Calculate final WPM
    const typedWords = typedText.split(' ').filter(word => word.trim() !== '').length
    const timeMinutes = (60 - timeLeft) / 60
    const finalWpm = timeMinutes > 0 ? Math.round((typedWords / timeMinutes) * 100) / 100 : 0
    setWpm(finalWpm)

    // Submit results to backend
    try {
      const response = await fetch('http://localhost:5000/typing/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          test_id: testData?.id,
          typed_text: typedText,
          time_taken: 60 - timeLeft,
          accuracy: accuracy
        })
      })

      const data = await response.json()
      if (!data.success) {
        console.error('Failed to submit typing test:', data.message)
      }
    } catch (err) {
      console.error('Error submitting typing test:', err)
    }

    // Notify parent component
    if (onComplete) {
      onComplete({
        wpm: finalWpm,
        accuracy: accuracy,
        wordsTyped: typedWords,
        timeTaken: 60 - timeLeft
      })
    }
  }

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
        <h2>Typing Test: {testData.title}</h2>
        <div className="test-info">
          <span>Difficulty: {testData.difficulty}</span>
          <span>Words: {testData.word_count}</span>
          <span>Category: {testData.category}</span>
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
              placeholder="Start typing here..."
              disabled={!isActive || isComplete}
              className="typing-input"
            />
          </div>
          <div className="stats">
            <span>Accuracy: {accuracy}%</span>
            <span>Words Typed: {typedText.split(' ').filter(word => word.trim() !== '').length}</span>
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
          <button onClick={startTest} className="retry-btn">Take Test Again</button>
        </div>
      )}
    </div>
  )
}

export default TypingTest