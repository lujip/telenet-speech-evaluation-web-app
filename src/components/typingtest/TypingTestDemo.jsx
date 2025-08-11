import React from 'react'
import TypingTest from './TypingTest'

const TypingTestDemo = () => {
  const handleTestComplete = (results) => {
    console.log('Typing test completed:', results)
    alert(`Test completed! WPM: ${results.wpm}, Accuracy: ${results.accuracy}%`)
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>Typing Test Demo</h1>
      <p>This is a demo of the typing test component. Use session ID: "demo-session-123"</p>
      
      <TypingTest 
        sessionId="demo-session-123"
        onComplete={handleTestComplete}
      />
    </div>
  )
}

export default TypingTestDemo 