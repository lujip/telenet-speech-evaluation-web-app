import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../../contexts/SessionContext.jsx';
import './TechTest.css';

const TechTest = () => {
  console.log("TechTest component mounted");
  const navigate = useNavigate();
  const { applicantInfo, sessionId } = useSession();
  
  // Test states
  const [micTest, setMicTest] = useState({ status: 'pending', message: '' });
  const [audioTest, setAudioTest] = useState({ status: 'pending', message: '' });
  const [internetTest, setInternetTest] = useState({ status: 'pending', message: '' });
  
  // UI states
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [testAudioUrl, setTestAudioUrl] = useState(null);
  const [allTestsPassed, setAllTestsPassed] = useState(false);
  
  // Refs for audio visualization
  const canvasRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const sourceRef = useRef(null);
  const streamRef = useRef(null);
  const animationRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Check if all tests passed
  useEffect(() => {
    const allPassed = micTest.status === 'passed' && 
                     audioTest.status === 'passed' && 
                     internetTest.status === 'passed';
    setAllTestsPassed(allPassed);
  }, [micTest, audioTest, internetTest]);

  // Initialize tests when component mounts
  useEffect(() => {
    if (applicantInfo && sessionId) {
      runInternetTest();
      runAudioTest();
      runMicTest();
    }
  }, [applicantInfo, sessionId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  // Internet connection test
  const runInternetTest = async () => {
    try {
      const startTime = Date.now();
      await fetch('https://www.google.com/favicon.ico', {
        method: 'HEAD',
        mode: 'no-cors'
      });
      const endTime = Date.now();
      const latency = endTime - startTime;
      
      if (latency < 5000) { // 5 second timeout
        setInternetTest({
          status: 'passed',
          message: `Connection stable (${latency}ms)`
        });
      } else {
        setInternetTest({
          status: 'failed',
          message: 'Slow connection detected'
        });
      }
    } catch {
      setInternetTest({
        status: 'failed',
        message: 'No internet connection'
      });
    }
  };

  // Audio playback test
  const runAudioTest = async () => {
    try {
      // Create a simple test audio
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(440, audioContext.currentTime); // A4 note
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
      
      setAudioTest({
        status: 'passed',
        message: 'Audio playback working'
      });
    } catch {
      setAudioTest({
        status: 'failed',
        message: 'Audio playback not supported'
      });
    }
  };

  // Microphone test
  const runMicTest = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      streamRef.current = stream;
      setMicTest({
        status: 'passed',
        message: 'Microphone detected'
      });
      
      // Setup audio visualization
      setupAudioVisualization(stream);
    } catch {
      setMicTest({
        status: 'failed',
        message: 'Microphone access denied'
      });
    }
  };

  // Setup audio visualization
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

  // Draw waveform
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

  // Start recording test
  const startRecordingTest = async () => {
    if (!streamRef.current) {
      setMicTest({
        status: 'failed',
        message: 'No microphone access'
      });
      return;
    }

    try {
      setIsRecording(true);
      audioChunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(streamRef.current);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        setAudioUrl(audioUrl);
        setTestAudioUrl(audioUrl);
      };
      
      mediaRecorder.start();
      
      // Stop recording after 3 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
        }
        setIsRecording(false);
      }, 3000);
      
    } catch {
      setIsRecording(false);
      setMicTest({
        status: 'failed',
        message: 'Recording failed'
      });
    }
  };

  // Play test audio
  const playTestAudio = () => {
    if (testAudioUrl) {
      const audio = new Audio(testAudioUrl);
      audio.play();
    }
  };

  // Retry failed tests
  const retryTest = (testType) => {
    switch (testType) {
      case 'mic':
        setMicTest({ status: 'pending', message: '' });
        runMicTest();
        break;
      case 'audio':
        setAudioTest({ status: 'pending', message: '' });
        runAudioTest();
        break;
      case 'internet':
        setInternetTest({ status: 'pending', message: '' });
        runInternetTest();
        break;
    }
  };

  // Start evaluation
  const startEvaluation = () => {
    if (allTestsPassed) {
      navigate('/testing');
    }
  };

  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'passed':
        return '✅';
      case 'failed':
        return '❌';
      case 'pending':
        return '⏳';
      default:
        return '⏳';
    }
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'passed':
        return '#10b981';
      case 'failed':
        return '#ef4444';
      case 'pending':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  return (
    <div className="tech-test-container">
      <div className="tech-test-content">
        <h1 className="tech-test-title">Technical Requirements Check</h1>
        <p className="tech-test-subtitle">
          Please complete all tests below before starting your evaluation
        </p>

        <div className="tests-grid">
          {/* Microphone Test */}
          <div className="test-card" data-status={micTest.status}>
            <div className="test-header">
              <h3>Microphone Test</h3>
              <span 
                className="status-icon"
                style={{ color: getStatusColor(micTest.status) }}
              >
                {getStatusIcon(micTest.status)}
              </span>
            </div>
            
            <div className="test-content">
              <div className="waveform-container">
                <canvas 
                  ref={canvasRef} 
                  width="300" 
                  height="100" 
                  className="waveform-canvas"
                />
              </div>
              
              <div className="test-actions">
                <button 
                  onClick={startRecordingTest}
                  disabled={isRecording || micTest.status === 'failed'}
                  className="test-button"
                >
                  {isRecording ? 'Recording...' : 'Test Microphone'}
                </button>
                
                {audioUrl && (
                  <button 
                    onClick={playTestAudio}
                    className="test-button secondary"
                  >
                    Play Recording
                  </button>
                )}
              </div>
              
              <p className="test-message">{micTest.message}</p>
              
              {micTest.status === 'failed' && (
                <div className="error-instructions">
                  <p>We couldn't detect your microphone. Please:</p>
                  <ul>
                    <li>Allow microphone access when prompted</li>
                    <li>Check if your microphone is connected</li>
                    <li>Refresh the page and try again</li>
                  </ul>
                  <button 
                    onClick={() => retryTest('mic')}
                    className="retry-button"
                  >
                    Retry Test
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Audio Playback Test */}
          <div className="test-card" data-status={audioTest.status}>
            <div className="test-header">
              <h3>Audio Playback Test</h3>
              <span 
                className="status-icon"
                style={{ color: getStatusColor(audioTest.status) }}
              >
                {getStatusIcon(audioTest.status)}
              </span>
            </div>
            
            <div className="test-content">
              <div className="audio-test-info">
                <p>This test checks if your device can play audio.</p>
                <p>Status: {audioTest.message}</p>
              </div>
              
              {audioTest.status === 'failed' && (
                <div className="error-instructions">
                  <p>Audio playback is not working. Please:</p>
                  <ul>
                    <li>Check your device's audio settings</li>
                    <li>Ensure your speakers/headphones are connected</li>
                    <li>Try refreshing the page</li>
                  </ul>
                  <button 
                    onClick={() => retryTest('audio')}
                    className="retry-button"
                  >
                    Retry Test
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Internet Connection Test */}
          <div className="test-card" data-status={internetTest.status}>
            <div className="test-header">
              <h3>Internet Connection Test</h3>
              <span 
                className="status-icon"
                style={{ color: getStatusColor(internetTest.status) }}
              >
                {getStatusIcon(internetTest.status)}
              </span>
            </div>
            
            <div className="test-content">
              <div className="internet-test-info">
                <p>This test checks your internet connection stability.</p>
                <p>Status: {internetTest.message}</p>
              </div>
              
              {internetTest.status === 'failed' && (
                <div className="error-instructions">
                  <p>Internet connection issues detected. Please:</p>
                  <ul>
                    <li>Check your internet connection</li>
                    <li>Try connecting to a different network</li>
                    <li>Refresh the page and try again</li>
                  </ul>
                  <button 
                    onClick={() => retryTest('internet')}
                    className="retry-button"
                  >
                    Retry Test
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Start Evaluation Button */}
        <div className="evaluation-button-container">
          <button 
            onClick={startEvaluation}
            disabled={!allTestsPassed}
            className="start-evaluation-button"
          >
            {allTestsPassed ? 'Start Evaluation' : 'Complete All Tests First'}
          </button>
          
          {!allTestsPassed && (
            <p className="completion-message">
              All tests must pass before you can start the evaluation
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TechTest;