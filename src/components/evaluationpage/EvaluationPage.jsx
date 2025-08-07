import React, { useEffect, useState, useRef } from 'react';
import './EvaluationPage.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../../contexts/SessionContext.jsx';

const EvaluationPage = () => {
  console.log("EvaluationPage component mounted");
  const navigate = useNavigate();
  const { applicantInfo, sessionId, startEvaluation, clearSession } = useSession();
  
  const [question, setQuestion] = useState('');
  const [questionKeywords, setQuestionKeywords] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [timeLeft, setTimeLeft] = useState(60);
  const [hasAnswered, setHasAnswered] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const [audioUrl, setAudioUrl] = useState(null);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const sourceRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const [sessionStats, setSessionStats] = useState({
    questionsAnswered: 0,
    totalRecordingTime: 0,
    averageScore: 0
  });
  const [hasSpokenInitialQuestion, setHasSpokenInitialQuestion] = useState(false);

  // Reset evaluation state when component mounts (new session)
  useEffect(() => {
    if (applicantInfo && sessionId && !hasSpokenInitialQuestion) {
      // Check current session state from backend
      checkSessionState();
      setHasSpokenInitialQuestion(true);
    }
  }, [applicantInfo, sessionId]);

  // Check current session state from backend
  const checkSessionState = async () => {
    try {
      // Get current question and count for this session
      const [questionRes, countRes] = await Promise.all([
        axios.get(`http://localhost:5000/question?session_id=${sessionId}`),
        axios.get(`http://localhost:5000/question_count?session_id=${sessionId}`)
      ]);
      
      setQuestion(questionRes.data.text);
      setQuestionKeywords(questionRes.data.keywords || []);
      setTotalQuestions(countRes.data.total);
      setCurrentQuestionIndex(countRes.data.current);
      
      // Check if current question has been answered
      const statusRes = await axios.get(`http://localhost:5000/question_status?session_id=${sessionId}`);
      setHasAnswered(statusRes.data.has_answered);
      
      // Speak the current question if it exists
      if (questionRes.data.text) {
        try {
          await axios.post("http://localhost:5000/speak", {
            text: questionRes.data.text
          });
        } catch (speakErr) {
          console.error("Error speaking question:", speakErr);
        }
      }
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
      const resetRes = await axios.post("http://localhost:5000/reset_questions", {
        session_id: sessionId
      });
      
      if (resetRes.data.success && resetRes.data.question) {
        // Use the question from reset response
        setQuestion(resetRes.data.question.text);
        setQuestionKeywords(resetRes.data.question.keywords || []);
        
        // Fetch question count
        const countRes = await axios.get(`http://localhost:5000/question_count?session_id=${sessionId}`);
        setTotalQuestions(countRes.data.total);
        setCurrentQuestionIndex(countRes.data.current);
        
        // Speak the first question
        if (resetRes.data.question.text) {
          try {
            await axios.post("http://localhost:5000/speak", {
              text: resetRes.data.question.text
            });
          } catch (speakErr) {
            console.error("Error speaking question:", speakErr);
          }
        } 
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
        axios.get(`http://localhost:5000/question?session_id=${sessionId}`),
        axios.get(`http://localhost:5000/question_count?session_id=${sessionId}`)
      ]);
      setQuestion(questionRes.data.text);
      setQuestionKeywords(questionRes.data.keywords || []);
      setTotalQuestions(countRes.data.total);
      setCurrentQuestionIndex(countRes.data.current);
      
      // Speak the question
      if (questionRes.data.text) {
        try {
          await axios.post("http://localhost:5000/speak", {
            text: questionRes.data.text
          });
        } catch (speakErr) {
          console.error("Error speaking question:", speakErr);
        }
      }
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
    setAudioUrl(null);
    setHasAnswered(true);
    
    // Mark current question as answered in backend
    try {
      await axios.post("http://localhost:5000/mark_answered", {
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
    setAudioUrl(URL.createObjectURL(audioBlob));
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
      const res = await axios.post("http://localhost:5000/evaluate", formData, {
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

  const handleFinishEvaluation = async () => {
    try {
      if (sessionId) {
        const requestData = { session_id: sessionId };
        await axios.post("http://localhost:5000/finish_evaluation", requestData);
      }
      
      // Clear session data
      clearSession();
      
      // Navigate to a completion page or back to landing
      navigate('/');
    } catch (err) {
      alert("Error finishing evaluation: " + err.message);
    }
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

  // Show applicant info in the sidebar
  const renderApplicantInfo = () => {
    if (!applicantInfo) return null;
    
    return (
      <div className="stats-card">
        <h3>👤 Applicant Info</h3>
        <div className="stat-item">
          <span className="stat-label">Name</span>
          <span className="stat-value">{applicantInfo.fullName}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Role</span>
          <span className="stat-value">{applicantInfo.role}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Email</span>
          <span className="stat-value">{applicantInfo.email}</span>
        </div>
        {applicantInfo.phone && (
          <div className="stat-item">
            <span className="stat-label">Phone</span>
            <span className="stat-value">{applicantInfo.phone}</span>
          </div>
        )}
        {applicantInfo.experience && (
          <div className="stat-item">
            <span className="stat-label">Experience</span>
            <span className="stat-value">{applicantInfo.experience}</span>
          </div>
        )}
      </div>
    );
  };


  return (
    <div className="main-content-vertical">
      {/* Main Content */}
      <div className="box-container" style={{ position: 'relative' }}>
        <h1 className="speech-title">Tele-net Speech Evaluation</h1>
        
        <div className="question-section">
          <div className="question-counter">
            Question {currentQuestionIndex + 1} of {totalQuestions}
          </div>
          <h2>Current Question:</h2>
          <p>{question || "Loading question..."}</p>
          
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
                    const res = await axios.post("http://localhost:5000/next_question", {
                      session_id: sessionId
                    });
                    if (res.data.success) {
                      setQuestion(res.data.question.text);
                      setQuestionKeywords(res.data.question.keywords || []);
                      setCurrentQuestionIndex(res.data.currentIndex);
                      setResult(null);
                      setAudioUrl(null);
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
                onClick={handleFinishEvaluation}
                disabled={loading || recording || !hasAnswered}
                className="finish-button"
              >
                🏁 Finish Evaluation
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
          </div>
        )}
      </div>

      {/* Sidebar */}
      <div className="sidebar">
        {renderApplicantInfo()}

        <div className="stats-card">
          <h3>💡 Tips</h3>
          <div style={{color: '#4a5568', fontSize: '0.9rem', lineHeight: '1.5'}}>
            <p>• Speak clearly and at a moderate pace</p>
            <p>• Use specific examples in your answers</p>
            <p>• Stay calm and confident</p>
            <p>• Address all parts of the question</p>
            <p>• You have 60 seconds per answer</p>
          </div>
        </div>

        <div className="stats-card">
          <h3>📊 Session Stats</h3>
          <div className="stat-item">
            <span className="stat-label">Questions Remaining</span>
            <span className="stat-value">{totalQuestions - (currentQuestionIndex + 1)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Current Question</span>
            <span className="stat-value">{currentQuestionIndex + 1} of {totalQuestions}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Recording Time</span>
            <span className="stat-value">{sessionStats.totalRecordingTime.toFixed(2)}s</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Status</span>
            <span className="stat-value">{hasAnswered ? 'Answered' : 'Pending'}</span>
          </div>
        </div>


      </div>
    </div>
  );
};

export default EvaluationPage;

