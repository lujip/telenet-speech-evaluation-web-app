import React, { useState, useEffect } from 'react';
import { useSession } from '../../contexts/SessionContext.jsx';
import axios from 'axios';
import './GenericWrittenTest.css';

const API_URL = import.meta.env.VITE_API_URL;

const GenericWrittenTest = ({
  // Test configuration
  testType = 'generic',
  title = 'Test',
  icon = '📝',
  instructions = [],
  timerMinutes = 10,
  
  // API endpoints
  fetchQuestionsUrl,
  submitAnswersUrl,
  
  // Display options
  maxQuestions = null, // null means show all questions
  showQuestionNavigation = true,
  showTimer = true,
  
  // Callbacks
  onComplete,
  onNext,
  
  // Custom styling
  containerClass = '',
  primaryColor = '#2F6798'
}) => {
  console.log(`${testType} test component mounted`);
  const { applicantInfo, sessionId } = useSession();
  
  // Test states
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(timerMinutes * 60);
  const [isTestStarted, setIsTestStarted] = useState(false);
  const [isTestComplete, setIsTestComplete] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submissionComplete, setSubmissionComplete] = useState(false);
  
  // Test statistics
  const [startTime, setStartTime] = useState(null);
  const [completionTime, setCompletionTime] = useState(0);

  // Initialize test when component mounts
  useEffect(() => {
    if (applicantInfo && sessionId) {
      fetchQuestions();
    }
  }, [applicantInfo, sessionId]);

  // Timer countdown
  useEffect(() => {
    let timer;
    if (isTestStarted && timeLeft > 0 && !isTestComplete && showTimer) {
      timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleTimeUp();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isTestStarted, timeLeft, isTestComplete, showTimer]);

  // Fetch questions from backend
  const fetchQuestions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(fetchQuestionsUrl);
      
      if (response.data.success) {
        let loadedQuestions = response.data.questions;
        
        // Limit questions if maxQuestions is specified
        if (maxQuestions && loadedQuestions.length > maxQuestions) {
          loadedQuestions = loadedQuestions.slice(0, maxQuestions);
        }
        
        setQuestions(loadedQuestions);
        console.log(`${testType} test questions loaded:`, loadedQuestions.length);
      } else {
        setError(response.data.message || 'Failed to load questions');
      }
    } catch (err) {
      console.error(`Error fetching ${testType} test questions:`, err);
      setError(`Failed to load ${testType} test questions. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  // Start the test
  const startTest = () => {
    setIsTestStarted(true);
    setStartTime(Date.now());
    console.log(`${testType} test started`);
  };

  // Handle answer selection for multiple choice
  const handleAnswerSelect = (questionId, selectedIndex) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: selectedIndex
    }));
  };

  // Handle input answer for input questions  
  const handleInputAnswer = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  // Navigate to specific question
  const goToQuestion = (index) => {
    setCurrentQuestionIndex(index);
  };

  // Navigate to previous question
  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  // Navigate to next question
  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  // Handle time up
  const handleTimeUp = () => {
    console.log(`Time is up! Auto-submitting ${testType} test...`);
    submitTest();
  };

  // Submit the test
  const submitTest = async () => {
    try {
      setLoading(true);
      const endTime = Date.now();
      const timeTaken = startTime ? Math.floor((endTime - startTime) / 1000) : 0;
      setCompletionTime(timeTaken);

      const response = await axios.post(submitAnswersUrl, {
        session_id: sessionId,
        answers: answers,
        completion_time: timeTaken
      });

      if (response.data.success) {
        console.log(`${testType} test submitted successfully:`, response.data);
        setIsTestComplete(true);
        setSubmissionComplete(true);
        
        // Call onComplete callback
        if (onComplete) {
          onComplete({
            testType: testType,
            completed: true,
            totalQuestions: questions.length,
            answeredQuestions: Object.keys(answers).length,
            completionTime: timeTaken,
            results: response.data.results
          });
        }
      } else {
        setError(response.data.message || 'Failed to submit test');
      }
    } catch (err) {
      console.error(`Error submitting ${testType} test:`, err);
      setError(`Failed to submit ${testType} test. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  // Check if all questions are answered
  const areAllQuestionsAnswered = () => {
    return questions.every(q => Object.prototype.hasOwnProperty.call(answers, q.id));
  };



  // Format time display
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Get timer color based on time left
  const getTimerColor = () => {
    const quarterTime = timerMinutes * 15; // 25% of total time
    const halfTime = timerMinutes * 30; // 50% of total time
    
    if (timeLeft > halfTime) return '#10b981'; // Green
    if (timeLeft > quarterTime) return '#f59e0b'; // Orange
    return '#ef4444'; // Red
  };

  if (loading && !questions.length) {
    return (
      <div className={`generic-test-container ${containerClass}`}>
        <div className="loading-spinner"></div>
        <p>Loading {title.toLowerCase()}...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`generic-test-container ${containerClass}`}>
        <div className="error-message">
          <h2>❌ Error</h2>
          <p>{error}</p>
          <button onClick={fetchQuestions} className="retry-button">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  if (!isTestStarted) {
    return (
      <div className={`generic-test-container ${containerClass}`}>
        <div className="test-instructions">
          <h1 className="test-title" style={{ color: primaryColor }}>
            {icon} {title}
          </h1>
          <div className="instructions-content">
            <h2>Instructions:</h2>
            <ul>
              {instructions.map((instruction, index) => (
                <li key={index}>{instruction}</li>
              ))}
              <li>This test contains {questions.length} questions</li>
              {showTimer && <li>You have {timerMinutes} minutes to complete the test</li>}
              <li>You can navigate between questions and change your answers before submitting</li>
            </ul>
            <div className="start-button-container">
              <button 
                onClick={startTest} 
                className="start-test-button"
                style={{ background: primaryColor }}
              >
                🚀 Start {title}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (submissionComplete) {
    return (
      <div className={`generic-test-container ${containerClass}`}>
        <div className="completion-message">
          <h2 className="completion-title" style={{ color: primaryColor }}>
            ✅ {title} Complete!
          </h2>
          <p>Thank you for completing the {title.toLowerCase()}.</p>
          <p>Your answers have been recorded and will be reviewed as part of your evaluation.</p>
          
          <div className="completion-stats">
            <div className="stat-item">
              <span className="stat-value">{Object.keys(answers).length}</span>
              <span className="stat-label">Questions Answered</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{questions.length}</span>
              <span className="stat-label">Total Questions</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{formatTime(completionTime)}</span>
              <span className="stat-label">Time Taken</span>
            </div>
          </div>

          <button 
            onClick={onNext} 
            className="next-test-button"
            style={{ background: primaryColor }}
          >
            ➡️ Continue to Next Test
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className={`generic-test-container ${containerClass}`}>
      <div className="test-header">
        <div className="header-left">
          <h1 className="test-title" style={{ color: primaryColor }}>
            {icon} {title}
          </h1>
        </div>
        <div className="header-right">
          {showTimer && (
            <div className="timer-container">
              <span 
                className={`time-remaining ${timeLeft <= 120 ? 'warning' : ''}`}
                style={{ 
                  color: getTimerColor(),
                  border: `2px solid ${getTimerColor()}`,
                  padding: '8px 16px',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.9)',
                  fontWeight: 'bold'
                }}
              >
                ⏰ Time Left: {formatTime(timeLeft)}
              </span>
            </div>
          )}
        </div>
      </div>

      {showQuestionNavigation && (
        <div className="question-navigation">
          <h4 style={{ color: primaryColor }}>Quick Navigation:</h4>
          <div className="question-numbers">
            {questions.map((_, index) => (
              <button
                key={index}
                onClick={() => goToQuestion(index)}
                className={`question-number ${index === currentQuestionIndex ? 'current' : ''} ${answers[questions[index]?.id] !== undefined ? 'answered' : ''}`}
                style={{
                  borderColor: index === currentQuestionIndex ? primaryColor : '#e5e7eb',
                  backgroundColor: index === currentQuestionIndex ? primaryColor : 
                                 answers[questions[index]?.id] !== undefined ? '#10b981' : 'white'
                }}
              >
                {index + 1}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="question-section">
        <div className="question-header">
          <h2 className="question-text" style={{ color: primaryColor }}>
            {currentQuestion?.question}
          </h2>
        </div>

        <div className="answer-section">
          {currentQuestion?.type === 'input' ? (
            <div className="input-answer">
              <input
                type={currentQuestion.input_type || 'text'}
                placeholder={currentQuestion.placeholder || 'Enter your answer'}
                value={answers[currentQuestion.id] || ''}
                onChange={(e) => handleInputAnswer(currentQuestion.id, e.target.value)}
                className="answer-input"
              />
            </div>
          ) : (
            <div className="options-container">
              {currentQuestion?.options?.map((option, index) => (
                <div 
                  key={index}
                  className={`option-item ${answers[currentQuestion.id] === index ? 'selected' : ''}`}
                  onClick={() => handleAnswerSelect(currentQuestion.id, index)}
                >
                  <div className="option-radio">
                    <input 
                      type="radio"
                      name={`question_${currentQuestion.id}`}
                      checked={answers[currentQuestion.id] === index}
                      onChange={() => handleAnswerSelect(currentQuestion.id, index)}
                    />
                  </div>
                  <div className="option-text">{option}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="navigation-section">
        <div className="nav-buttons">
          <button 
            onClick={previousQuestion}
            disabled={currentQuestionIndex === 0}
            className="nav-button previous"
          >
            ⬅️ Previous
          </button>
          
          {currentQuestionIndex < questions.length - 1 ? (
            <button 
              onClick={nextQuestion}
              className="nav-button next"
            >
              Next ➡️
            </button>
          ) : (
            <button 
              onClick={submitTest}
              disabled={!areAllQuestionsAnswered() || loading}
              className="submit-button"
              style={{ background: areAllQuestionsAnswered() ? primaryColor : '#ccc' }}
            >
              {loading ? '⏳ Submitting...' : `🏁 Submit ${title}`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default GenericWrittenTest; 