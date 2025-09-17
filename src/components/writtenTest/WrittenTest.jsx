import React, { useState, useEffect } from 'react';
import { useSession } from '../../contexts/SessionContext.jsx';
import axios from 'axios';
import './WrittenTest.css';

const API_URL = import.meta.env.VITE_API_URL;

const WrittenTest = ({ onComplete, onNext }) => {
  console.log("WrittenTest component mounted");
  const { applicantInfo, sessionId } = useSession();
  
  // Test states
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes
  const [isTestStarted, setIsTestStarted] = useState(false);
  const [isTestComplete, setIsTestComplete] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submissionComplete, setSubmissionComplete] = useState(false);
  
  // Test statistics
  const [startTime, setStartTime] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [completionTime, setCompletionTime] = useState(0);

  // Initialize written test when component mounts
  useEffect(() => {
    if (applicantInfo && sessionId) {
      fetchQuestions();
    }
  }, [applicantInfo, sessionId]);

  // Timer countdown
  useEffect(() => {
    let timer;
    if (isTestStarted && timeLeft > 0 && !isTestComplete) {
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
  }, [isTestStarted, timeLeft, isTestComplete]);

  // Fetch questions from backend
  const fetchQuestions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/written/questions`);
      
      if (response.data.success) {
        setQuestions(response.data.questions);
        console.log('Written test questions loaded:', response.data.questions);
      } else {
        setError(response.data.message || 'Failed to load questions');
      }
    } catch (err) {
      console.error('Error fetching written test questions:', err);
      setError('Failed to load written test questions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Start the test
  const startTest = () => {
    setIsTestStarted(true);
    setStartTime(Date.now());
    console.log('Written test started');
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
    console.log('Time is up! Auto-submitting test...');
    submitTest();
  };

  // Submit the test
  const submitTest = async () => {
    if (isTestComplete) return;

    try {
      setLoading(true);
      setIsTestComplete(true);
      
      const endTime = Date.now();
      const timeTaken = startTime ? Math.floor((endTime - startTime) / 1000) : 0;
      setCompletionTime(timeTaken);

      const response = await axios.post(`${API_URL}/written/submit`, {
        session_id: sessionId,
        answers: answers,
        completion_time: timeTaken
      });

      if (response.data.success) {
        setSubmissionComplete(true);
        console.log('Written test submitted successfully');
        
        // Automatically proceed to next test after a short delay
        setTimeout(() => {
          handleTestComplete();
        }, 2000);
      } else {
        setError(response.data.message || 'Failed to submit test');
      }
    } catch (err) {
      console.error('Error submitting written test:', err);
      setError('Failed to submit written test. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Check if all questions are answered
  const allQuestionsAnswered = () => {
    return questions.length > 0 && questions.every(q => {
      const answer = answers[q.id];
      if (q.type === 'input') {
        // For input questions, check if answer exists and is not empty
        return answer !== undefined && answer !== null && String(answer).trim() !== '';
      } else {
        // For multiple choice, check if answer is a valid index
        return answer !== undefined && answer !== null && typeof answer === 'number';
      }
    });
  };

  // Handle test completion
  const handleTestComplete = () => {
    if (onComplete) {
      onComplete({
        testType: 'written',
        score: 0, // Score will be calculated by admin
        completed: true
      });
    }
    if (onNext) {
      onNext();
    }
  };

  // Format time display
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Get question status for navigation
  const getQuestionStatus = (index) => {
    const question = questions[index];
    if (!question) return 'unanswered';
    if (index === currentQuestionIndex) return 'current';
    
    const answer = answers[question.id];
    if (question.type === 'input') {
      // For input questions, check if answer exists and is not empty
      return answer !== undefined && answer !== null && String(answer).trim() !== '' ? 'answered' : 'unanswered';
    } else {
      // For multiple choice, check if answer is a valid index
      return answer !== undefined && answer !== null && typeof answer === 'number' ? 'answered' : 'unanswered';
    }
  };

  if (loading) {
    return (
      <div className="written-test-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="written-test-container">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={fetchQuestions} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (submissionComplete) {
    return (
      <div className="written-test-container">
        <div className="submission-complete">
          <h2>✅ Written Test Submitted Successfully!</h2>
          <div className="submission-notice">
            <p>Your answers have been recorded and submitted for evaluation.</p>
            <p>The results will be available to the evaluation team.</p>
            <p>Moving to the next test...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!isTestStarted) {
    return (
      <div className="written-test-container">
        <div className="test-instructions">
          <h2>Written Test Instructions</h2>
          <div className="instructions-content">
            <p>Welcome to the written test! This test evaluates your knowledge of customer service principles and BPO practices.</p>
            
            <div className="test-details">
              <h3>Test Details:</h3>
              <ul>
                <li>Total Questions: {questions.length}</li>
                <li>Time Limit: 10 minutes</li>
                <li>Question Types: Multiple choice</li>
                <li>You can navigate between questions</li>
                <li>Make sure to answer all questions before submitting</li>
              </ul>
            </div>
            
            <div className="test-tips">
              <h3>Tips:</h3>
              <ul>
                <li>Read each question carefully</li>
                <li>Choose the best answer from the options provided</li>
                <li>You can change your answers before submitting</li>
                <li>The test will auto-submit when time runs out</li>
              </ul>
            </div>
          </div>
          
          <button onClick={startTest} className="start-test-button">
            Start Written Test
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="written-test-container">
      <div className="test-header">
        <div className="test-info">
          <h2>Written Test</h2>
          <p>Question {currentQuestionIndex + 1} of {questions.length}</p>
        </div>
        <div className="timer">
          <span className={`time-remaining ${timeLeft <= 60 ? 'warning' : ''}`}>
            Time: {formatTime(timeLeft)}
          </span>
        </div>
      </div>

      <div className="test-content">
        <div className="question-navigation">
          {questions.map((_, index) => (
            <button
              key={index}
              className={`question-nav-btn ${getQuestionStatus(index)}`}
              onClick={() => goToQuestion(index)}
            >
              {index + 1}
            </button>
          ))}
        </div>

        <div className="question-container">
          <div className="question-header">
            <h3>Question {currentQuestionIndex + 1}</h3>
            <span className="question-category">{currentQuestion.category}</span>
          </div>
          
          <div className="question-text">
            {currentQuestion.question}
          </div>
          
          {currentQuestion.type === 'input' ? (
            // Input question
            <div className="input-container">
              <input
                type={currentQuestion.input_type === 'number' ? 'number' : 'text'}
                placeholder={currentQuestion.placeholder || 'Enter your answer'}
                value={answers[currentQuestion.id] || ''}
                onChange={(e) => handleInputAnswer(currentQuestion.id, e.target.value)}
                className="answer-input"
              />
            </div>
          ) : (
            // Multiple choice question
            <div className="options-container">
              {currentQuestion.options.map((option, index) => (
                <div
                  key={index}
                  className={`option ${answers[currentQuestion.id] === index ? 'selected' : ''}`}
                  onClick={() => handleAnswerSelect(currentQuestion.id, index)}
                >
                  <div className="option-radio">
                    <input
                      type="radio"
                      name={`question-${currentQuestion.id}`}
                      checked={answers[currentQuestion.id] === index}
                      onChange={() => handleAnswerSelect(currentQuestion.id, index)}
                    />
                  </div>
                  <div className="option-text">
                    <span className="option-letter">{String.fromCharCode(65 + index)}.</span>
                    <div className="option-text-content">{option}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="test-controls">
          <div className="navigation-buttons">
            <button
              onClick={previousQuestion}
              disabled={currentQuestionIndex === 0}
              className="nav-button prev"
            >
              Previous
            </button>
            <button
              onClick={nextQuestion}
              disabled={currentQuestionIndex === questions.length - 1}
              className="nav-button next"
            >
              Next
            </button>
          </div>
          
          <div className="submit-section">
            <div className="progress-info">
              <p>Answered: {Object.keys(answers).length} / {questions.length}</p>
            </div>
            <button
              onClick={submitTest}
              className={`submit-button ${allQuestionsAnswered() ? 'ready' : 'not-ready'}`}
              disabled={!allQuestionsAnswered() || isTestComplete}
            >
              {allQuestionsAnswered() ? 'Submit Test' : `Answer All Questions (${questions.length - Object.keys(answers).length} remaining)`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WrittenTest;