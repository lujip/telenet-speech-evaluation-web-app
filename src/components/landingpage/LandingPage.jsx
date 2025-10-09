import React from 'react'
import './LandingPage.css'
import Header from '../header/Header.jsx';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../../contexts/SessionContext.jsx';

const LandingPage = () => { 
  // console.log("LandingPage component mounted");
  const navigate = useNavigate();
  const { applicantInfo, sessionId, clearSession } = useSession();
  
  const handleStart = () => {
      navigate('/applicantform');
  };

  const handleContinue = () => {
      navigate('/testing');
  };

  const handleStartNew = () => {
      clearSession();
      navigate('/applicantform');
  };

  return (
    <>
      <Header />
      <div className="box-container">
        {/* Hero Section */}
        <section className="hero-section">
          <h1>Welcome to the Tele-net Comprehensive Evaluation</h1>
          <p>
          This comprehensive assessment evaluates your skills across multiple areas for a potential role in our call center team. 
          You'll complete five different types of tests: listening comprehension, written communication, speech evaluation, personality assessment, and typing skills.
          </p>
        </section>

        {/* Test Overview */}
        <section className="test-overview-section">
          <h2>Evaluation Components</h2>
          <div className="test-grid">
            <div className="landing-page-test-item">
              <div className="landing-page-test-icon">🎧</div>
              <h3>Listening Test</h3>
              <p>Answer multiple-choice questions based on audio scenarios</p>
            </div>
            <div className="landing-page-test-item">
              <div className="landing-page-test-icon">📝</div>
              <h3>Written Test</h3>
              <p>Respond to written questions demonstrating your communication skills</p>
            </div>
            <div className="landing-page-test-item">
              <div className="landing-page-test-icon">🗣️</div>
              <h3>Speech Evaluation</h3>
              <p>Record verbal responses to interview questions (60 seconds each)</p>
            </div>
            <div className="landing-page-test-item">
              <div className="landing-page-test-icon">🧠</div>
              <h3>Personality Assessment</h3>
              <p>Multiple-choice questions to evaluate personality traits and work preferences</p>
            </div>
            <div className="landing-page-test-item">
              <div className="landing-page-test-icon">⌨️</div>
              <h3>Typing Test</h3>
              <p>Complete a 60-second typing test to measure speed and accuracy</p>
            </div>
          </div>
        </section>

        {/* What to Expect */}
        <section className="expect-section">
          <h2>What to Expect</h2>
          <ul>
            <li><strong>Listening Test:</strong> Multiple-choice questions based on customer service scenarios</li>
            <li><strong>Written Test:</strong> Professional written responses to job-related questions</li>
            <li><strong>Speech Evaluation:</strong> 5 interview questions with 60 second responses</li>
            <li><strong>Personality Assessment:</strong> Psychological evaluation to assess work style and traits</li>
            <li><strong>Typing Test:</strong> 60-second speed and accuracy assessment</li>
            
            
            
          </ul>
        </section>

        {/* Technical Requirements & Instructions 
        <section className="mic-setup-section">
          <h2>Technical Requirements & Instructions</h2>
          <ol>
            <li><strong>Environment:</strong> Use a quiet space with minimal background noise</li>
            <li><strong>Microphone:</strong> Ensure your microphone is working and grant browser permissions when prompted</li>
            <li><strong>Audio Playback:</strong> Make sure your speakers/headphones work for the listening test</li>
            <li><strong>Internet Connection:</strong> Stable connection required for all test components</li>
            <li><strong>Browser Compatibility:</strong> Use a modern browser (Chrome, Firefox, Safari, or Edge)</li>
            <li><strong>Device Requirements:</strong> Computer or tablet recommended for optimal experience</li>
            <li><strong>Test Your Setup:</strong> Use the microphone test feature before starting the evaluation</li>
          </ol>
        </section>
        */}

        {/* Start Button (CTA) */}
        <div className="cta-section">
          {applicantInfo && sessionId ? (
            <div style={{ textAlign: 'center' }}>
              <p style={{ marginBottom: '0', color: '#4a5568' }}>
                Welcome back, <strong>{applicantInfo.firstName} {applicantInfo.lastName}</strong>! 
                You have an evaluation in progress.
              </p>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', marginTop: '0' }}>
                <button className="start-btn" onClick={handleContinue}>
                  Continue Evaluation
                </button>
                <button 
                  className="start-btn new-application" 
                  onClick={handleStartNew}
                >
                  Start New Application
                </button>
              </div>
            </div>
          ) : (
            <button className="start-btn" onClick={handleStart}>
              Start Evaluation
            </button>
          )}
        </div>
      </div>
    </>
  )
}

export default LandingPage  