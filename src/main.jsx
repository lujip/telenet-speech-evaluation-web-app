import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import LandingPage from './components/landingpage/LandingPage.jsx'
import ApplicantForm from './components/applicantform/ApplicantForm.jsx'
import Admin from './components/admin/Admin.jsx'
import TechTest from './components/techtest/TechTest.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import TypingTest from './components/typingtest/TypingTest.jsx'
import { SessionProvider } from './contexts/SessionContext.jsx'
import { BrowserRouter, Routes, Route } from 'react-router-dom';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <SessionProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/app" element={
            <ProtectedRoute>
              <App />
            </ProtectedRoute>
          } />
          <Route path="/techtest" element={
            <ProtectedRoute>
              <TechTest />
            </ProtectedRoute>
          } />
          <Route path="/evaluation" element={
            <ProtectedRoute>
              <App />
            </ProtectedRoute>
          } />
          <Route path="/applicantform" element={<ApplicantForm />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/typingtest" element={<TypingTest />} />
        </Routes>
      </SessionProvider>
    </BrowserRouter>
  </StrictMode>,
)
