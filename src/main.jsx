import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import LandingPage from './components/landingpage/LandingPage.jsx'
import ApplicantForm from './components/applicantform/ApplicantForm.jsx'
import Admin from './components/admin/Admin.jsx'
import TechTest from './components/techtest/TechTest.jsx'
import TestingPage from './components/testingpage/TestingPage.jsx'
import EvaluationPage from './components/evaluationpage/EvaluationPage.jsx'
import CompletionPage from './components/completionpage/CompletionPage.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import TypingTest from './components/typingtest/TypingTest.jsx'
import WrittenTest from './components/writtenTest/WrittenTest.jsx'
import { SessionProvider } from './contexts/SessionContext.jsx'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Debug logging
// console.log('TestingPage component:', TestingPage);
// console.log('All routes loaded in main.jsx');

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <SessionProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/app" element={
            <ProtectedRoute>
              <EvaluationPage />
            </ProtectedRoute>
          } />
          <Route path="/tech-test" element={
            <ProtectedRoute>
              <TechTest />
            </ProtectedRoute>
          } />
          <Route path="/testing" element={<TestingPage />} />
          <Route path="/evaluation" element={
            <ProtectedRoute>
              <EvaluationPage />
            </ProtectedRoute>
          } />
          <Route path="/applicantform" element={<ApplicantForm />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/typingtest" element={<TypingTest />} />
          <Route path="/completion" element={<CompletionPage />} />
          <Route path="/written-test" element={<WrittenTest />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </SessionProvider>
    </BrowserRouter>
  </StrictMode>,
)
