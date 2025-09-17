  import React, { useState, useEffect, useRef } from 'react';
  import { useSession } from '../../contexts/SessionContext.jsx';
  import axios from 'axios';
  import './ListenTest.css';

  const API_URL = import.meta.env.VITE_API_URL;

  const ListenTest = ({ onComplete, onNext }) => {
    console.log("ListenTest component mounted");
    const { applicantInfo, sessionId } = useSession();
    
    // Test states
    const [currentQuestion, setCurrentQuestion] = useState('');
  const [currentAudioId, setCurrentAudioId] = useState('');
  const [audioElement, setAudioElement] = useState(null);

    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [totalQuestions, setTotalQuestions] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [hasAnswered, setHasAnswered] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [submissionComplete, setSubmissionComplete] = useState(false);
    
    // Session timer state (10 minutes)
    const [sessionTimeLeft, setSessionTimeLeft] = useState(600); // 10 minutes in seconds
    const [isSessionStarted, setIsSessionStarted] = useState(false);
    
    // Audio refs
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const streamRef = useRef(null);
    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const sourceRef = useRef(null);
    const animationRef = useRef(null);
    const canvasRef = useRef(null);
    const dataArrayRef = useRef(null);

      // Initialize listening test when component mounts
  useEffect(() => {
    if (applicantInfo && sessionId) {
      initializeListeningTest();
    }
  }, [applicantInfo, sessionId]);

  // Cleanup audio element when component unmounts
  useEffect(() => {
    return () => {
      if (audioElement) {
        audioElement.pause();
        setAudioElement(null);
      }
    };
  }, [audioElement]);

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

    const initializeListeningTest = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Reset listening test questions
        const resetResponse = await axios.post(`${API_URL}/listening-test-reset`, {
          session_id: sessionId
        });
        
        if (resetResponse.data.success) {
          // Get question count
          const countResponse = await axios.get(`${API_URL}/listening-test-question-count?session_id=${sessionId}`);
          setTotalQuestions(countResponse.data.total);
          
          // Get first question
          const questionResponse = await axios.get(`${API_URL}/listening-test-question?session_id=${sessionId}`);
          if (questionResponse.data.text) {
            setCurrentQuestion(questionResponse.data.text);
            setCurrentAudioId(questionResponse.data.audio_id || '');
            setCurrentQuestionIndex(0);
            
            // Start session timer
            setIsSessionStarted(true);
          }
        }
      } catch (err) {
        console.error('Error initializing listening test:', err);
        setError('Failed to initialize listening test. Please try again.');
      } finally {
        setLoading(false);
      }
    };

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
            setError('Failed to play audio file. Please try again.');
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
        if (err.response && err.response.data && err.response.data.message) {
          setError(`Failed to play question audio: ${err.response.data.message}`);
        } else {
          setError('Failed to play question audio. Please try again.');
        }
        setIsPlaying(false);
      }
    };

    const startRecording = async () => {
      if (hasAnswered) return;
      
      try {
        setError(null);
        setIsRecording(true);
        setHasAnswered(true);
        
        // Get microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          } 
        });
        
        streamRef.current = stream;
        
        // Setup audio visualization
        setupAudioVisualization(stream);
        
        // Setup MediaRecorder
        audioChunksRef.current = [];
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };
        
        mediaRecorder.onstop = handleRecordingStop;
        mediaRecorder.start();
        
      } catch (err) {
        console.error('Error starting recording:', err);
        setError('Failed to access microphone. Please check permissions and try again.');
        setIsRecording(false);
        setHasAnswered(false);
      }
    };

    const stopRecording = () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      
      setIsRecording(false);
      
      // Cleanup audio visualization
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



    const handleRecordingStop = async () => {
      try {
        setLoading(true);
        setSubmissionComplete(true); // Show submission complete immediately
        
        // Create audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Create form data for upload
        const formData = new FormData();
        formData.append('audio', audioBlob);
        formData.append('question_text', currentQuestion);
        formData.append('session_id', sessionId);
        formData.append('question_index', currentQuestionIndex);
        
        // Send for evaluation
        const response = await axios.post(`${API_URL}/evaluate-listening-test`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        if (response.data) {
          console.log('Recording submitted successfully');
        }
        
      } catch (err) {
        console.error('Error evaluating recording:', err);
        setError('Failed to evaluate recording. Please try again.');
        setSubmissionComplete(false); // Hide submission complete on error
      } finally {
        setLoading(false);
      }
    };

    const setupAudioVisualization = (stream) => {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      sourceRef.current = source;
      
      analyser.fftSize = 256;
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      dataArrayRef.current = dataArray;
      
      source.connect(analyser);
      drawWaveform();
    };

    const drawWaveform = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      const analyser = analyserRef.current;
      const dataArray = dataArrayRef.current;
      
      if (!analyser || !dataArray) return;
      
      analyser.getByteFrequencyData(dataArray);
      
      ctx.fillStyle = 'rgb(0, 0, 0)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      const barWidth = (canvas.width / dataArray.length) * 2.5;
      let barHeight;
      let x = 0;
      
      for (let i = 0; i < dataArray.length; i++) {
        barHeight = dataArray[i] / 2;
        
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, '#667eea');
        gradient.addColorStop(1, '#764ba2');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        
        x += barWidth + 1;
      }
      
      animationRef.current = requestAnimationFrame(drawWaveform);
    };

    const nextQuestion = async () => {
      try {
        setLoading(true);
        setError(null);
        setSubmissionComplete(false);
        
        const response = await axios.post(`${API_URL}/listening-test-next-question`, {
          session_id: sessionId
        });
        
        if (response.data.success) {
          // Stop any currently playing audio
          if (audioElement) {
            audioElement.pause();
            setAudioElement(null);
          }
          setIsPlaying(false);
          
          setCurrentQuestion(response.data.question.text);
          setCurrentAudioId(response.data.question.audio_id || '');
          setCurrentQuestionIndex(response.data.currentIndex);
          setHasAnswered(false);
        } else {
          // No more questions, test complete
          handleTestComplete();
        }
        
      } catch (err) {
        console.error('Error moving to next question:', err);
        setError('Failed to move to next question. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    const handleTestComplete = () => {
      // Call onComplete callback with results
      if (onComplete) {
        onComplete({
          testType: 'listening',
          score: 0, // Score will be calculated by admin
          totalQuestions: totalQuestions,
          completed: true
        });
      }
      
      // Move to next test
      if (onNext) {
        onNext();
      }
    };

    // Handle session time up
    const handleSessionTimeUp = () => {
      console.log('Session time is up! Auto-completing listening test...');
      
      // Stop any ongoing recording
      if (isRecording) {
        stopRecording();
      }
      
      // Stop any playing audio
      if (audioElement) {
        audioElement.pause();
        setAudioElement(null);
      }
      setIsPlaying(false);
      
      // Complete the test automatically
      handleTestComplete();
    };

    // Format time display
    const formatTime = (seconds) => {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    // Get session timer color based on time left
    const getSessionTimerColor = () => {
      if (sessionTimeLeft > 180) return '#10b981'; // Green (>3 mins)
      if (sessionTimeLeft > 60) return '#f59e0b'; // Orange (>1 min)
      return '#ef4444'; // Red (<=1 min)
    };

    if (loading && !currentQuestion) {
      return (
        <div className="listen-test-container">
          <div className="loading-spinner"></div>
          <p>Initializing listening test...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="listen-test-container">
          <div className="error-message">
            <h2>❌ Error</h2>
            <p>{error}</p>
            <button onClick={initializeListeningTest} className="retry-button">
              🔄 Retry
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="listen-test-container">
        <div className="box-container">
          <div className="listen-test-header">
            <div className="header-left">
              <h1 className="listen-title">Listening Test</h1>
              <div className="progress-info">
                Question {currentQuestionIndex + 1} of {totalQuestions}
              </div>
            </div>
            <div className="header-right">
              <div className="session-timer-container">
                <span 
                  className={`session-time-remaining ${sessionTimeLeft <= 60 ? 'warning' : ''}`}
                  style={{ 
                    fontSize: '16px', 
                    fontWeight: 'bold', 
                    color: getSessionTimerColor(),
                    padding: '8px 16px',
                    border: `2px solid ${getSessionTimerColor()}`,
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.9)',
                    display: 'inline-block',
                    marginBottom: '1rem'
                  }}
                >
                  ⏰ Time Left: {formatTime(sessionTimeLeft)}
                </span>
              </div>
              <div className="instructions">
                <h3>Instructions:</h3>
                <ul>
                  <li>Click the "Play Audio" button to hear the audio phrase</li>
                  <li>Listen carefully to the pronunciation and intonation</li>
                  <li>Click "Start Recording" when you're ready to repeat</li>
                  <li>Speak clearly and try to match the audio exactly</li>
                  <li>Click "Stop Recording" when you're finished</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="question-section">
            <h2>Listen to the Audio Phrase:</h2>
            <div className="audio-controls">
              <button 
                onClick={playQuestion} 
                disabled={isPlaying || !currentAudioId}
                className="play-button"
              >
                {isPlaying ? '🔊 Playing...' : '🔊 Play Audio'}
              </button>
            </div>
            
            <p className="audio-note">
              {currentAudioId 
                ? 'Click the button above to hear the audio phrase you need to repeat'
                : 'Audio not available for this question'
              }
            </p>
          </div>

          <div className="recording-section">
            {!hasAnswered ? (
              <button 
                onClick={startRecording} 
                className="start-recording-button"
              >
                🎙️ Start Recording
              </button>
            ) : (
              <div className="recording-controls">
                {isRecording ? (
                  <>
                  <p className="recording-status">Recording... Speak now!</p>
                    <div className="waveform-container">
                      <canvas 
                        ref={canvasRef} 
                        width="400" 
                        height="100" 
                        className="waveform-canvas"
                      />
                    </div>
                    <button 
                      onClick={stopRecording} 
                      className="stop-recording-button"
                    >
                      ⏹️ Stop Recording
                    </button>
                    
                  </>
                ) : (
                  <div className="submission-notice">
                <p>Your answer has been recorded and submitted for evaluation.</p>
                <p>The results will be available to the evaluation team.</p>
              </div>
                )}
              </div>
            )}
          </div>

          {submissionComplete && (
            <div className="submission-complete">
              {currentQuestionIndex + 1 < totalQuestions ? (
                <button onClick={nextQuestion} className="next-question-button">
                  ➡️ Next Question
                </button>
              ) : (
                <button onClick={handleTestComplete} className="complete-test-button">
                  🏁 Complete Listening Test
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  export default ListenTest;