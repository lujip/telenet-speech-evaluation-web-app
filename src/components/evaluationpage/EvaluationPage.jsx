import React, { useEffect, useState, useRef } from 'react';
import './EvaluationPage.css';
import axios from 'axios';
import { useSession } from '../../contexts/SessionContext.jsx';

const EvaluationPage = ({ onComplete, onNext }) => {
  console.log("EvaluationPage component mounted");
  const { applicantInfo, sessionId } = useSession();
  
  // Check if position type is non-voice and skip speech evaluation
  const [shouldSkipSpeech, setShouldSkipSpeech] = useState(false);
  
  const [question, setQuestion] = useState('');
  const [questionKeywords, setQuestionKeywords] = useState([]);
  const [currentAudioId, setCurrentAudioId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [timeLeft, setTimeLeft] = useState(60);
  const [hasAnswered, setHasAnswered] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioElement, setAudioElement] = useState(null);
  // Add overall session timer (15 minutes)
  const [sessionTimeLeft, setSessionTimeLeft] = useState(900); // 15 minutes in seconds
  const [isSessionStarted, setIsSessionStarted] = useState(false);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const sourceRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const [sessionStats, setSessionStats] = useState({
    questionsAnswered: 0,
    totalRecordingTime: 0,
    averageScore: 0
  });
  const [hasSpokenInitialQuestion, setHasSpokenInitialQuestion] = useState(false);
  const API_URL = import.meta.env.VITE_API_URL;

  // Check position type and skip speech evaluation if non-voice
  useEffect(() => {
    if (applicantInfo && applicantInfo.positionType) {
      const positionType = applicantInfo.positionType.toLowerCase();
      if (positionType === 'non-voice' || positionType === 'non voice' || positionType === 'nonvoice') {
        setShouldSkipSpeech(true);
        console.log("Non-voice position detected, speech evaluation will be skipped");
      }
    }
  }, [applicantInfo]);

  // Reset evaluation state when component mounts (new session)
  useEffect(() => {
    if (applicantInfo && sessionId && !hasSpokenInitialQuestion && !shouldSkipSpeech) {
      // Check current session state from backend with resume support
      checkSessionStateAndResume();
      setHasSpokenInitialQuestion(true);
      // Start session timer
      setIsSessionStarted(true);
    }
  }, [applicantInfo, sessionId, shouldSkipSpeech]);

  // Session timer countdown effect
  useEffect(() => {
    let sessionTimer;
    if (isSessionStarted && sessionTimeLeft > 0) {
      sessionTimer = setInterval(() => {
        setSessionTimeLeft(prev => {
          if (prev <= 1) {
            handleSessionTimeUp();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(sessionTimer);
  }, [isSessionStarted, sessionTimeLeft]);

  // Check current session state from backend and resume from last checkpoint
  const checkSessionStateAndResume = async () => {
    try {
      // Get session progress first to see if we need to resume
      const progressRes = await axios.get(`${API_URL}/session_progress?session_id=${sessionId}`);
      
      if (progressRes.data.success) {
        const progress = progressRes.data;
        console.log('Session progress loaded:', progress);
        
        // If there are answered questions, resume from last checkpoint
        if (progress.speech_evaluation.answered_count > 0 && 
            !progress.speech_evaluation.is_complete) {
          console.log('Resuming speech evaluation from checkpoint...');
          
          // Resume session from last unanswered question
          const resumeRes = await axios.post(`${API_URL}/resume_session`, {
            session_id: sessionId,
            test_type: 'speech'
          });
          
          if (resumeRes.data.success) {
            if (resumeRes.data.all_complete) {
              // All questions answered, test now marked complete, move to next test
              console.log('All speech questions answered, moving to next test');
              
              // Call onComplete to update progress bar
              if (onComplete) {
                onComplete({
                  testType: 'speech',
                  score: 0, // Score will be calculated by admin
                  totalQuestions: progress.speech_evaluation.total_questions,
                  questionsAnswered: progress.speech_evaluation.answered_count,
                  completed: true
                });
              }
              
              // Then move to next test
              if (onNext) {
                onNext();
              }
              return;
            } else if (resumeRes.data.resumed) {
              // Set up resumed question
              setQuestion(resumeRes.data.question.text);
              setQuestionKeywords(resumeRes.data.question.keywords || []);
              setCurrentAudioId(resumeRes.data.question.audio_id || '');
              setCurrentQuestionIndex(resumeRes.data.current_index);
              setTotalQuestions(progress.speech_evaluation.total_questions);
              console.log(`Resumed at question ${resumeRes.data.current_index + 1}/${progress.speech_evaluation.total_questions}`);
              return;
            }
          }
        }
      }
      
      // If no resume needed, get current question normally
      const [questionRes, countRes] = await Promise.all([
        axios.get(`${API_URL}/question?session_id=${sessionId}`),
        axios.get(`${API_URL}/question_count?session_id=${sessionId}`)
      ]);
      
      setQuestion(questionRes.data.text);
      setQuestionKeywords(questionRes.data.keywords || []);
      setCurrentAudioId(questionRes.data.audio_id || '');
      setTotalQuestions(countRes.data.total);
      setCurrentQuestionIndex(countRes.data.current);
      
      // Check if current question has been answered
      const statusRes = await axios.get(`${API_URL}/question_status?session_id=${sessionId}`);
      setHasAnswered(statusRes.data.has_answered);
    } catch (err) {
      console.error("Error checking session state:", err);
      // Fallback to reset if session state check fails
      resetAndFetchQuestions();
    }
  };

  // Reset the speech flag when session changes
  useEffect(() => {
    console.log ("Second Use effect");
    setHasSpokenInitialQuestion(false);
  }, [sessionId]);

  // Cleanup audio element when component unmounts
  useEffect(() => {
    return () => {
      if (audioElement) {
        audioElement.pause();
        setAudioElement(null);
      }
    };
  }, [audioElement]); 

  // Timer effect for countdown
  useEffect(() => {
    if (recording && timeLeft > 0) {
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            stopRecording();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else if (!recording) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [recording, timeLeft]);

  // Reset timer when question changes
  useEffect(() => {
    setTimeLeft(60);
  }, [currentQuestionIndex]);

  const resetAndFetchQuestions = async () => {
    console.log("resetAndFetchQuestions called");
    try {
      // Reset questions on backend
      const resetRes = await axios.post(`${API_URL}/reset_questions`, {
        session_id: sessionId
      });
      
      if (resetRes.data.success && resetRes.data.question) {
        // Use the question from reset response
        setQuestion(resetRes.data.question.text);
        setQuestionKeywords(resetRes.data.question.keywords || []);
        setCurrentAudioId(resetRes.data.question.audio_id || '');
        
        // Fetch question count
        const countRes = await axios.get(`${API_URL}/question_count?session_id=${sessionId}`);
        setTotalQuestions(countRes.data.total);
        setCurrentQuestionIndex(countRes.data.current); 
      } else {
        // Fallback to fetching questions separately
        await fetchQuestionAndCount();
      }
    } catch (err) {
      console.error("Error resetting questions:", err);
      // Fallback to just fetching questions
      await fetchQuestionAndCount();
    }
  };

  const fetchQuestionAndCount = async () => {
    try {
      const [questionRes, countRes] = await Promise.all([
        axios.get(`${API_URL}/question?session_id=${sessionId}`),
        axios.get(`${API_URL}/question_count?session_id=${sessionId}`)
      ]);
      setQuestion(questionRes.data.text);
      setQuestionKeywords(questionRes.data.keywords || []);
      setCurrentAudioId(questionRes.data.audio_id || '');
      setTotalQuestions(countRes.data.total);
      setCurrentQuestionIndex(countRes.data.current);
    } catch (err) {
      console.error("Error fetching question data:", err);
    }
  };

  // Canvas waveform drawing
  const drawWaveform = () => {
    if (!analyserRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const WIDTH = canvas.width;
    const HEIGHT = canvas.height;
    ctx.clearRect(0, 0, WIDTH, HEIGHT);
    analyserRef.current.getByteTimeDomainData(dataArrayRef.current);
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#1565c0';
    ctx.beginPath();
    let sliceWidth = WIDTH / dataArrayRef.current.length;
    let x = 0;
    for (let i = 0; i < dataArrayRef.current.length; i++) {
      let v = dataArrayRef.current[i] / 128.0;
      let y = (v * HEIGHT) / 2;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
      x += sliceWidth;
    }
    ctx.lineTo(WIDTH, HEIGHT / 2);
    ctx.stroke();
    animationRef.current = requestAnimationFrame(drawWaveform);
  };

  // Start recording and waveform
  const startRecording = async () => {
    setResult(null);
    setRecording(true);
    setHasAnswered(true);
    
    // Mark current question as answered in backend
    try {
      await axios.post(`${API_URL}/mark_answered`, {
        session_id: sessionId,
        question_index: currentQuestionIndex
      });
    } catch (err) {
      console.error("Error marking question as answered:", err);
    }
    
    audioChunksRef.current = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    // Web Audio API setup
    audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    analyserRef.current = audioContextRef.current.createAnalyser();
    const source = audioContextRef.current.createMediaStreamSource(stream);
    sourceRef.current = source;
    source.connect(analyserRef.current);
    analyserRef.current.fftSize = 2048;
    const bufferLength = analyserRef.current.fftSize;
    dataArrayRef.current = new Uint8Array(bufferLength);
    drawWaveform();
    // MediaRecorder setup
    const mediaRecorder = new window.MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunksRef.current.push(e.data);
      }
    };
    mediaRecorder.onstop = handleStop;
    mediaRecorder.start();
  };

  // Stop recording and waveform
  const stopRecording = () => {
    setRecording(false);
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  const handleStop = async () => {
    setLoading(true);
    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('question', question);
    questionKeywords.forEach(k => formData.append('keywords', k));
    formData.append('audio', audioBlob, 'answer.wav');
    formData.append('question_index', currentQuestionIndex.toString());
    
    // Add session ID if available
    if (sessionId) {
      formData.append('session_id', sessionId);
    }
    
    try {
      const res = await axios.post(`${API_URL}/evaluate`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(res.data);
      
      // Update session stats
      setSessionStats(prev => ({
        questionsAnswered: prev.questionsAnswered + 1,
        totalRecordingTime: prev.totalRecordingTime + (res.data.audio_metrics?.duration || 0),
        averageScore: res.data.evaluation?.score || prev.averageScore
      }));
    } catch (err) {
      alert("Error during evaluation: " + err.message);
    }
    setLoading(false);
  };

  // Audio playback functions
  const playQuestion = async () => {
    if (!currentAudioId) return;
    
    try {
      setIsPlaying(true);
      
      // Get the audio URL from the backend
      const response = await axios.post(`${API_URL}/speak-audio`, {
        id: currentAudioId
      });
      
      if (response.data.success && response.data.audio_url) {
        // Create full URL
        const fullAudioUrl = `${API_URL}${response.data.audio_url}`;
        
        // Create and play audio element
        const audio = new Audio(fullAudioUrl);
        setAudioElement(audio);
        
        // Set up event listeners
        audio.onended = () => {
          setIsPlaying(false);
          setAudioElement(null);
        };
        
        audio.onerror = () => {
          setResult({ success: false, message: 'Failed to play audio file. Please try again.' });
          setIsPlaying(false);
          setAudioElement(null);
        };
        
        // Play the audio
        await audio.play();
        
      } else {
        throw new Error(response.data.message || 'Failed to get audio URL');
      }
      
    } catch (err) {
      console.error('Error playing question audio:', err);
      setResult({ success: false, message: 'Failed to play question audio. Please try again.' });
      setIsPlaying(false);
    }
  };

  const stopAudio = () => {
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
      setAudioElement(null);
    }
    setIsPlaying(false);
  };

  // Format time display
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get timer color based on time left
  const getTimerColor = () => {
    if (timeLeft > 30) return '#10b981'; // Green
    if (timeLeft > 10) return '#f59e0b'; // Orange
    return '#ef4444'; // Red
  };

  // Get session timer color based on time left
  const getSessionTimerColor = () => {
    if (sessionTimeLeft > 300) return '#10b981'; // Green (>5 mins)
    if (sessionTimeLeft > 120) return '#f59e0b'; // Orange (>2 mins)
    return '#ef4444'; // Red (<=2 mins)
  };

  // Handle session time up
  const handleSessionTimeUp = async () => {
    console.log('Session time is up! Auto-completing evaluation...');
    
    // Stop any ongoing recording
    if (recording) {
      stopRecording();
    }
    
    // Stop any playing audio
    if (audioElement) {
      audioElement.pause();
      setAudioElement(null);
    }
    setIsPlaying(false);
    
    // Mark speech test as completed in the backend
    try {
      await axios.post(`${API_URL}/mark_test_completed`, {
        session_id: sessionId,
        test_type: 'speech'
      });
      console.log('Speech test marked as completed in backend');
    } catch (err) {
      console.error('Error marking speech test as completed:', err);
      // Continue anyway - don't block user progress
    }
    
    // Complete the evaluation automatically
    if (onComplete) {
      onComplete({
        testType: 'speech',
        score: sessionStats.averageScore,
        totalQuestions: totalQuestions,
        questionsAnswered: sessionStats.questionsAnswered,
        timeUp: true
      });
    }
    
    if (onNext) {
      onNext();
    }
  };

  // Show speech evaluation instructions in the sidebar
  const renderSpeechInstructions = () => {
    return (
      <div className="stats-card">
        <h3>🎤 Speech Evaluation Instructions</h3>
        <div className="instruction-content">
          <div className="instruction-item">
            <h4>📋 How to Answer</h4>
            <p>1. Click "Play Question" to hear the question</p>
            <p>2. Think about your response</p>
            <p>3. Click "Start Answering" to record</p>
            <p>4. Speak clearly and confidently</p>
            <p>5. Click "Stop Recording" when done</p>
          </div>
          
          <div className="instruction-item">
            <h4>⏱️ Time Limits</h4>
            <p>• Maximum recording time: 60 seconds</p>
            <p>• Take your time to think before recording</p>
            <p>• Recording stops automatically at 60 seconds</p>
            <p>• Total session time: 15 minutes</p>
            <p>• Session will auto-complete when time runs out</p>
          </div>
          
          <div className="instruction-item">
            <h4>💡 Tips for Success</h4>
            <p>• Speak slowly and clearly</p>
            <p>• Use complete sentences</p>
            <p>• Stay calm and confident</p>
            <p>• Answer the question completely</p>
          </div>
        </div>
      </div>
    );
  };

  // Render skip speech evaluation UI for non-voice positions
  if (shouldSkipSpeech) {
    return (
      <div className="main-content-vertical">
        <div className="box-container" style={{ textAlign: 'center', padding: '40px' }}>
          
          <div className="skip-speech-notice" style={{
            
            color: '#2F6798',
            padding: '40px',
            borderRadius: '12px',
            margin: '20px 0',
          }}>
            <h2 style={{ marginBottom: '20px', fontSize: '28px' }}>Speech Evaluation Skipped</h2>
            <p style={{ fontSize: '18px', marginBottom: '15px', lineHeight: '1.6' }}>
              Based on your position type (<strong>{applicantInfo?.positionType}</strong>), 
              the speech evaluation has been automatically skipped.
            </p>
            <p style={{ fontSize: '16px', opacity: '0.9', marginBottom: '30px' }}>
              This test is only required for voice positions.
            </p>
            
            <button
              onClick={() => {
                // Mark speech evaluation as complete when button is clicked
                if (onComplete) {
                  onComplete({
                    testType: 'speech',
                    score: 0,
                    totalQuestions: 0,
                    questionsAnswered: 0,
                    skipped: true,
                    reason: 'Non-voice position'
                  });
                }
                
                // Move to next test
                if (onNext) {
                  onNext();
                }
              }}
              style={{
                background: 'white',
                color: '#667eea',
                border: 'none',
                padding: '15px 40px',
                fontSize: '18px',
                fontWeight: '600',
                borderRadius: '25px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 10px rgba(0, 0, 0, 0.1)'
              }}
              onMouseOver={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.15)';
              }}
              onMouseOut={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.1)';
              }}
            >
              ➡️ Continue to Next Test
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content-vertical">

      {/* Sidebar */}
      <div className="sidebar">
        {renderSpeechInstructions()}
        
        {/*<div className="stats-card">
          <h3>📊 Session Progress</h3>
          <div className="stat-item">
            <span className="stat-label">Questions</span>
            <span className="stat-value">{currentQuestionIndex + 1} / {totalQuestions}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Answered</span>
            <span className="stat-value">{sessionStats.questionsAnswered}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total Time</span>
            <span className="stat-value">{Math.round(sessionStats.totalRecordingTime)}s</span>
          </div>
          {sessionStats.averageScore > 0 && (
            <div className="stat-item">
              <span className="stat-label">Avg Score</span>
              <span className="stat-value">{sessionStats.averageScore}</span>
            </div>
          )}
        </div>*/}

      </div>
      {/* Main Content */}
      <div className="box-container" style={{ position: 'relative' }}>
        <h1 className="speech-title">Tele-net Speech Evaluation</h1>
        
        {/* Session Timer Header */}
        <div className="test-header" >
          <div className="test-info">
            <span style={{ 
              fontSize: '16px', 
              fontWeight: 'bold', 
              color: 'white',
              border: `3px solid ${getSessionTimerColor()}`, 
              borderRadius: '8px', 
              padding: '8px 16px', 
              display: 'flex', 
              justifyContent: 'flex-end', 
              maxWidth: '200px'
              }
              }>Time Left: {formatTime(sessionTimeLeft)}</span>
          </div>
          <div className="session-timer">
          </div>
        </div>
        
        <div className="question-section">
          <div className="question-counter">
            Question {currentQuestionIndex + 1} of {totalQuestions}
          </div>
        {/*  <h2>Current Question:</h2>
          <p>{question || "Loading question..."}</p>
          */}
          <div className="audio-controls">
            <button 
              onClick={playQuestion} 
              disabled={isPlaying || !currentAudioId}
              className="play-button"
            >
              {isPlaying ? '🔊 Playing...' : '🔊 Play Question'}
            </button>
            
            {isPlaying && (
              <button 
                onClick={stopAudio}
                className="stop-audio-button"
              >
                ⏹️ Stop Audio
              </button>
            )}
          </div>
          
          <div className="question-buttons">
            <button 
              onClick={startRecording} 
              disabled={loading || recording || !question || hasAnswered}
              className={hasAnswered ? 'answered-button' : ''}
            >
              {recording ? "🔴 Recording..." : hasAnswered ? "✅ Answered" : "🎙️ Start Answering"}
            </button>
            <button
              onClick={stopRecording}
              disabled={loading || !recording}
            >
              ⏹️ Stop Recording
            </button>
            {currentQuestionIndex + 1 < totalQuestions ? (
              <button
                onClick={async () => {
                  try {
                    const res = await axios.post(`${API_URL}/next_question`, {
                      session_id: sessionId
                    });
                    if (res.data.success) {
                      // Stop any currently playing audio
                      if (audioElement) {
                        audioElement.pause();
                        setAudioElement(null);
                      }
                      setIsPlaying(false);
                      
                      setQuestion(res.data.question.text);
                      setQuestionKeywords(res.data.question.keywords || []);
                      setCurrentAudioId(res.data.question.audio_id || '');
                      setCurrentQuestionIndex(res.data.currentIndex);
                      setResult(null);
                      setTimeLeft(60);
                      setHasAnswered(false);
                    } else {
                      alert(res.data.message || "No more questions.");
                    }
                  } catch (err) {
                    alert("Error fetching next question: " + err.message);
                  }
                }}
                disabled={loading || recording || !hasAnswered}
                className="next-button"
              >
                ➡️ Next Question
              </button>
            ) : (
              <button
                onClick={async () => {
                  // Mark speech test as completed in the backend
                  try {
                    await axios.post(`${API_URL}/mark_test_completed`, {
                      session_id: sessionId,
                      test_type: 'speech'
                    });
                    console.log('Speech test marked as completed in backend');
                  } catch (err) {
                    console.error('Error marking speech test as completed:', err);
                    // Continue anyway - don't block user progress
                  }
                  
                  // Complete speech evaluation and move to next test in pipeline
                  if (onComplete) {
                    onComplete({
                      testType: 'speech',
                      score: sessionStats.averageScore,
                      totalQuestions: totalQuestions,
                      questionsAnswered: sessionStats.questionsAnswered
                    });
                  }
                  
                  // Move to next test
                  if (onNext) {
                    onNext();
                  }
                }}
                disabled={loading || recording || !hasAnswered}
                className="typing-button"
              >
                🏁 Complete Speech Evaluation
              </button>
            )}
          </div>
        </div>

        {recording && (
          <div className="recording-container">
            <div className="recording-status">
              🔴 Recording in progress... Speak clearly!
              <div className="timer-display" style={{ color: getTimerColor() }}>
                ⏱️ Time Left: {formatTime(timeLeft)}
              </div>
            </div>
            <canvas
              ref={canvasRef}
              width={700}
              height={80}
              className="waveform-canvas"
            />
          </div>
        )}

        {hasAnswered && !recording && !result && (
          <div className="answered-notice">
            <p>✅ You have answered this question. Please wait for the evaluation results.</p>
          </div>
        )}

        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner" />
            <div className="loading-text">🤖 Analyzing your speech...</div>
          </div>
        )}

        {result && (
          <div className="result-section">
            <h3>✅ Answer Submitted Successfully!</h3>
            <div className="submission-notice">
              <p>Your answer has been recorded and submitted for evaluation.</p>
              <p>The results will be available to the evaluation team.</p>
            </div>
            {currentQuestionIndex + 1 >= totalQuestions && (
              <div className="typing-notice">
                <p>🎉 All speech questions completed! Click "Complete Speech Evaluation" to continue to the next test.</p>
              </div>
            )}
          </div>
        )}

      </div>

      
    </div>
  );
};

export default EvaluationPage;

