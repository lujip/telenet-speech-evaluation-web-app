import React from 'react'
import './LandingPage.css'
import Header from '../header/Header.jsx';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../../contexts/SessionContext.jsx';

const LandingPage = () => { 
  console.log("LandingPage component mounted");
  const navigate = useNavigate();
  const { applicantInfo, sessionId, clearSession } = useSession();
  
  const handleStart = () => {
      navigate('/applicantform');
  };

  const handleContinue = () => {
      navigate('/app');
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
          <h1>Welcome to the Voice Evaluation Test</h1>
          <p>
          This short speaking assessment helps us evaluate your communication skills for a potential role in our call center team. 
          You'll be asked a few job-related questions and will respond using your microphone.
          </p>
        </section>

        {/* What to Expect */}
        <section className="expect-section">
          <h2>What to Expect</h2>
          <ul>
            <li>🎤 5–6 short interview questions</li>
            <li>⏱ Each response should be spoken within 30–60 seconds</li>
            <li>📄 Instant feedback and score based on your speech</li>
            <li>✅ No need to repeat questions - just answer naturally</li>
          </ul>
        </section>

        {/* Mic Setup & Instructions */}
        <section className="mic-setup-section">
          <h2>Mic Setup & Instructions</h2>
          <ol>
            <li>Use a quiet environment with minimal background noise  </li>
            <li>Ensure your microphone is working </li>
            <li>Speak clearly and naturally - just like in a real interview</li>
            <li>Grant browser permission to access your microphone when prompted</li>
          </ol>
        </section>

        {/* Start Button (CTA) */}
        <div className="cta-section">
          {applicantInfo && sessionId ? (
            <div style={{ textAlign: 'center' }}>
              <p style={{ marginBottom: '1rem', color: '#4a5568' }}>
                Welcome back, <strong>{applicantInfo.fullName}</strong>! 
                You have an evaluation in progress.
              </p>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
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