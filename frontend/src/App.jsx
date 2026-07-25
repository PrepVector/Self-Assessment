import { useState } from 'react'
import Navbar from './components/Navbar'
import HeroSection from './components/HeroSection'
import FeaturesSection from './components/FeaturesSection'
import Footer from './components/Footer'
import AuthModal from './components/AuthModal'
import QuizComponent from './components/QuizComponent'

export default function App() {
  // ── Candidate state ────────────────────────────────────────────────
  // user: { name } — populated after the intake form is submitted
  const [user, setUser] = useState(null)

  // ── Modal state ────────────────────────────────────────────────────
  const [modalOpen, setModalOpen] = useState(false)

  // ── Quiz view state ────────────────────────────────────────────────
  const [showQuiz, setShowQuiz] = useState(false)

  // ── Handlers ───────────────────────────────────────────────────────

  /** Called when the intake form is submitted successfully */
  function handleAuthSuccess(userData) {
    setUser(userData)
    setModalOpen(false)
    setShowQuiz(true)
  }

  /**
   * Opens the intake modal (if no candidate yet) or goes straight to the quiz.
   * Both the hero CTA and the Navbar "Get Started" button call this.
   */
  function handleStartAssessment() {
    if (user) {
      setShowQuiz(true)
    } else {
      setModalOpen(true)
    }
  }

  // ── Render: show Quiz view or Landing page ─────────────────────────
  if (showQuiz) {
    return <QuizComponent user={user} />
  }

  return (
    <div className="min-h-screen font-sans">
      <Navbar
        user={user}
        onStartAssessment={handleStartAssessment}
      />
      <main>
        <HeroSection onStartAssessment={handleStartAssessment} />
        <FeaturesSection />
      </main>
      <Footer />

      {/* Intake Modal — rendered above everything when open */}
      {modalOpen && (
        <AuthModal
          onClose={() => setModalOpen(false)}
          onSuccess={handleAuthSuccess}
        />
      )}
    </div>
  )
}
