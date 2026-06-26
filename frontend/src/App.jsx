import { useState } from 'react'
import Navbar from './components/Navbar'
import HeroSection from './components/HeroSection'
import FeaturesSection from './components/FeaturesSection'
import Footer from './components/Footer'
import AuthModal from './components/AuthModal'
import QuizComponent from './components/QuizComponent'

export default function App() {
  // ── Global auth state ──────────────────────────────────────────────
  const [user, setUser] = useState(null)           // { name, email }
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  // ── Modal state ────────────────────────────────────────────────────
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState('signup') // 'signup' | 'signin'

  // ── Quiz view state ────────────────────────────────────────────────
  const [showQuiz, setShowQuiz] = useState(false)

  // ── Handlers ───────────────────────────────────────────────────────

  /** Called when the auth form is submitted successfully */
  function handleAuthSuccess(userData) {
    setUser(userData)
    setIsLoggedIn(true)
    setModalOpen(false)
    // If user just signed in/up via the CTA flow, go straight to quiz
    setShowQuiz(true)
  }

  /**
   * Smart CTA: 
   * - If logged in → go to quiz
   * - If not → open Sign Up modal
   */
  function handleStartAssessment() {
    if (isLoggedIn) {
      setShowQuiz(true)
    } else {
      setModalMode('signup')
      setModalOpen(true)
    }
  }

  /** Open the modal in Sign In mode (from Navbar) */
  function handleOpenSignIn() {
    setModalMode('signin')
    setModalOpen(true)
  }

  // ── Render: show Quiz view or Landing page ─────────────────────────
  if (showQuiz) {
    return <QuizComponent user={user} />
  }

  return (
    <div className="min-h-screen font-sans">
      <Navbar
        user={user}
        isLoggedIn={isLoggedIn}
        onOpenSignIn={handleOpenSignIn}
        onStartAssessment={handleStartAssessment}
      />
      <main>
        <HeroSection onStartAssessment={handleStartAssessment} />
        <FeaturesSection />
      </main>
      <Footer />

      {/* Auth Modal — rendered above everything when open */}
      {modalOpen && (
        <AuthModal
          mode={modalMode}
          onClose={() => setModalOpen(false)}
          onSuccess={handleAuthSuccess}
        />
      )}
    </div>
  )
}
