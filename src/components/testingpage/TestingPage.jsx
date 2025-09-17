import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../../contexts/SessionContext.jsx';
import ListenTest from '../listenTest/ListenTest.jsx';
import EvaluationPage from '../evaluationpage/EvaluationPage.jsx';
import TypingTest from '../typingtest/TypingTest.jsx';
import WrittenTest from '../writtenTest/WrittenTest.jsx';
import './TestingPage.css';
import Header from '../header/Header.jsx';
const API_URL = import.meta.env.VITE_API_URL;
const TestingPage = () => {
  console.log("TestingPage component mounted");
  const navigate = useNavigate();
  const { applicantInfo, sessionId } = useSession();
  
  // Test pipeline states
  const [currentTest, setCurrentTest] = useState('listening'); // 'listening', 'written', 'speech', 'typing'
  const [testProgress, setTestProgress] = useState({
    listening: { completed: false, score: 0 },
    written: { completed: false, score: 0 },
    speech: { completed: false, score: 0 },
    typing: { completed: false, score: 0 }
  });
  
  // Initialize testing pipeline when component mounts
  useEffect(() => {
    if (applicantInfo && sessionId) {
      console.log("TestingPage: Applicant info and session found");
      // Check test completion status and resume from appropriate test
      checkTestCompletionStatus();
    } else {
      console.log("TestingPage: No applicant info or session, redirecting to home");
      navigate('/');
    }
  }, [applicantInfo, sessionId, navigate]);

  // Check test completion status and resume from appropriate test
  const checkTestCompletionStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/get_test_completion_status?session_id=${sessionId}`);
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          const completionStatus = result.completion_status;
          console.log('Test completion status:', completionStatus);
          
          // Update local test progress state
          setTestProgress({
            listening: { completed: completionStatus.listening, score: 0 },
            written: { completed: completionStatus.written, score: 0 },
            speech: { completed: completionStatus.speech, score: 0 },
            typing: { completed: completionStatus.typing, score: 0 }
          });
          
          // Determine which test to resume from
          let nextTest = 'listening';
          if (completionStatus.listening && !completionStatus.written) {
            nextTest = 'written';
          } else if (completionStatus.listening && completionStatus.written && !completionStatus.speech) {
            nextTest = 'speech';
          } else if (completionStatus.listening && completionStatus.written && completionStatus.speech && !completionStatus.typing) {
            nextTest = 'typing';
          } else if (completionStatus.listening && completionStatus.written && completionStatus.speech && completionStatus.typing) {
            // All tests completed, navigate to completion page
            navigate('/completion');
            return;
          }
          
          setCurrentTest(nextTest);
          console.log(`Resuming from ${nextTest} test`);
        } else {
          console.error('Failed to get test completion status:', result.message);
          // Fallback to starting with listening test
          setCurrentTest('listening');
        }
      } else {
        console.error('Error getting test completion status:', response.status);
        // Fallback to starting with listening test
        setCurrentTest('listening');
      }
    } catch (error) {
      console.error('Error checking test completion status:', error);
      // Fallback to starting with listening test
      setCurrentTest('listening');
    }
  };

  // Handle test completion
  const handleTestComplete = async (testType, results) => {
    console.log(`${testType} test completed:`, results);
    
    // Update test progress
    setTestProgress(prev => ({
      ...prev,
      [testType]: {
        completed: true,
        score: results.score || 0
      }
    }));
    
    // Mark test as completed in backend session
    try {
      const response = await fetch(`${API_URL}/mark_test_completed`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          test_type: testType
        })
      });
      
      if (response.ok) {
        console.log(`✅ ${testType} test marked as completed in session`);
      } else {
        console.error(`❌ Failed to mark ${testType} test as completed:`, response.status);
      }
    } catch (error) {
      console.error(`❌ Error marking ${testType} test as completed:`, error);
    }
    
    // Move to next test
    moveToNextTest(testType);
  };

  // Move to next test in pipeline
  const moveToNextTest = (completedTest) => {
    const testOrder = ['listening', 'written', 'speech', 'typing'];
    const currentIndex = testOrder.indexOf(completedTest);
    const nextTest = testOrder[currentIndex + 1];
    
    if (nextTest) {
      setCurrentTest(nextTest);
    } else {
      // All tests completed
      handleAllTestsComplete();
    }
  };

  // Handle completion of all tests
  const handleAllTestsComplete = async () => {
    console.log('All tests completed!');
    console.log('Session ID for completion:', sessionId);
    
    try {
      // Call backend to combine all evaluation files and mark applicant as complete
      const response = await fetch(`${API_URL}/finish_evaluation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Evaluation completion result:', result);
        
        if (result.success) {
          console.log('✅ All evaluation files combined successfully!');
          console.log('✅ Applicant marked as complete!');
        } else {
          console.error('❌ Failed to complete evaluation:', result.message);
        }
      } else {
        console.error('❌ Error calling finish_evaluation endpoint:', response.status);
        const errorText = await response.text();
        console.error('Error response body:', errorText);
      }
    } catch (error) {
      console.error('❌ Error completing evaluation:', error);
    }
    
    // Navigate to completion page
    navigate('/completion');
  };

  // Render current test component
  const renderCurrentTest = () => {
    switch (currentTest) {
      case 'listening':
        return (
          <ListenTest 
            onComplete={(results) => handleTestComplete('listening', results)}
            onNext={() => moveToNextTest('listening')}
          />
        );
      case 'written':
        return (
          <WrittenTest 
            onComplete={(results) => handleTestComplete('written', results)}
            onNext={() => moveToNextTest('written')}
          />
        );
      case 'speech':
        return (
          <EvaluationPage 
            onComplete={(results) => handleTestComplete('speech', results)}
            onNext={() => moveToNextTest('speech')}
          />
        );
      case 'typing':
        return (
          <TypingTest 
            onComplete={(results) => handleTestComplete('typing', results)}
            onNext={() => moveToNextTest('typing')}
            sessionId={sessionId}
          />
        );
      default:
        return <div>Loading...</div>;
    }
  };

  // Get test status for progress bar
  const getTestStatus = (testType) => {
    if (testType === currentTest) return 'active';
    if (testProgress[testType] && testProgress[testType].completed) return 'completed';
    return 'pending';
  };

  // Get test icon
  const getTestIcon = (testType) => {
    switch (testType) {
      case 'listening': return '🎧';
      case 'written': return '📝';
      case 'speech': return '🗣️';
      case 'typing': return '⌨️';
      default: return '❓';
    }
  };

  // Get test title
  const getTestTitle = (testType) => {
    switch (testType) {
      case 'listening': return 'Listening Test';
      case 'written': return 'Written Test';
      case 'speech': return 'Speech Evaluation';
      case 'typing': return 'Typing Test';
      default: return 'Unknown Test';
    }
  };

  return (
    <div>
      <Header />
    <div className="testing-page-container">
      {/* Progress Header */}
      <div className="testing-header">
        <p>Complete all four tests to finish your evaluation</p>
        
        {/* Progress Bar */}
        <div className="progress-bar">
          {['listening', 'written', 'speech', 'typing'].map((testType, index) => (
            <div key={testType} className={`progress-step ${getTestStatus(testType)}`}>
              <div className="step-icon">
                {getTestStatus(testType) === 'completed' ? '✅' : getTestIcon(testType)}
              </div>
              <div className="step-info">
                <span className="step-title">{getTestTitle(testType)}</span>
                <span className="step-status">
                  {getTestStatus(testType) === 'completed' ? 'Completed' : 
                   getTestStatus(testType) === 'active' ? 'In Progress' : 'Pending'}
                </span>
              </div>
              {index < 3 && (
                <div className={`step-connector ${getTestStatus(testType) === 'completed' ? 'completed' : ''}`} />
              )}  
            </div>
          ))}
        </div>
      </div>

      {/* Current Test Display */}
      <div className="test-content">
        {renderCurrentTest()}
      </div>


    </div>
    </div>
  );
};

export default TestingPage; 