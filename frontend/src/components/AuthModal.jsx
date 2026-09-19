import { useEffect, useRef, useState } from 'react'

export default function AuthModal({ onClose, onSuccess }) {
  const [firstName, setFirstName] = useState('')
  const [lastName,  setLastName]  = useState('')
  const [error,     setError]     = useState('')
  const backdropRef = useRef(null)

  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  // Prevent background scroll while modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  function handleBackdropClick(e) {
    if (e.target === backdropRef.current) onClose()
  }

  function handleSubmit(e) {
    e.preventDefault()
    setError('')

    const trimFirst = firstName.trim()
    const trimLast  = lastName.trim()

    if (!trimFirst) {
      setError('Please enter your first name.')
      return
    }
    if (!trimLast) {
      setError('Please enter your last name.')
      return
    }

    // Concatenate for downstream quiz & PDF generator (expects a single name string)
    const fullName = `${trimFirst} ${trimLast}`
    onSuccess({ name: fullName })
    onClose()
  }

  return (
    <div
      ref={backdropRef}
      onClick={handleBackdropClick}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      style={{ backdropFilter: 'blur(8px)', backgroundColor: 'rgba(0,0,0,0.5)' }}
      role="dialog"
      aria-modal="true"
      aria-label="Begin assessment dialog"
    >
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-[fadeInScale_0.2s_ease-out]">

        {/* Top accent bar */}
        <div className="h-1 w-full bg-gradient-to-r from-blue-500 via-blue-600 to-indigo-600" />

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-all duration-150"
          aria-label="Close modal"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M6 18L18 6M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        <div className="px-8 py-8">
          {/* Header */}
          <div className="mb-7">
            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mb-4">
              {/* Clipboard / assessment icon */}
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h2 className="text-2xl font-extrabold text-gray-900">
              Begin Your Assessment
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Enter your details to personalize your AI assessment.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>

            {/* First Name */}
            <div>
              <label htmlFor="intake-first-name" className="block text-sm font-medium text-gray-700 mb-1.5">
                First Name
              </label>
              <input
                id="intake-first-name"
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="e.g. Alex"
                autoFocus
                autoComplete="given-name"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm text-gray-900 placeholder-gray-400 bg-gray-50
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:bg-white
                  transition-all duration-200"
              />
            </div>

            {/* Last Name */}
            <div>
              <label htmlFor="intake-last-name" className="block text-sm font-medium text-gray-700 mb-1.5">
                Last Name
              </label>
              <input
                id="intake-last-name"
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="e.g. Johnson"
                autoComplete="family-name"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm text-gray-900 placeholder-gray-400 bg-gray-50
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:bg-white
                  transition-all duration-200"
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="flex items-center gap-2 text-red-500 bg-red-50 border border-red-100 px-3 py-2 rounded-lg text-xs font-medium">
                <svg className="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              id="intake-start-btn"
              type="submit"
              className="w-full py-3.5 rounded-xl bg-blue-600 text-white text-sm font-bold
                shadow-lg shadow-blue-200
                transition-all duration-300
                hover:bg-blue-700 hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(59,130,246,0.4)]
                active:scale-[0.98] mt-2"
            >
              Start Assessment
            </button>
          </form>

          {/* Footer note */}
          <p className="text-center text-xs text-gray-400 mt-5">
            By continuing, you agree to our{' '}
            <a href="#" className="text-blue-500 hover:underline">Terms of Service</a>
            {' '}and{' '}
            <a href="#" className="text-blue-500 hover:underline">Privacy Policy</a>.
          </p>
        </div>
      </div>
    </div>
  )
}
