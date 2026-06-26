import { useState, useEffect, useRef } from 'react'

const HEADLINE = 'Cognitive Career Assessment'
const TYPING_SPEED = 80
const DELETE_SPEED = 40
const PAUSE_AFTER_TYPE = 2200
const PAUSE_AFTER_DELETE = 500

export default function HeroSection({ onStartAssessment }) {
  const [displayText, setDisplayText] = useState('')
  const [phase, setPhase] = useState('typing')
  const indexRef = useRef(0)

  useEffect(() => {
    let timeout
    if (phase === 'typing') {
      if (indexRef.current < HEADLINE.length) {
        timeout = setTimeout(() => {
          setDisplayText(HEADLINE.slice(0, indexRef.current + 1))
          indexRef.current++
        }, TYPING_SPEED)
      } else {
        timeout = setTimeout(() => setPhase('deleting'), PAUSE_AFTER_TYPE)
      }
    } else if (phase === 'deleting') {
      if (indexRef.current > 0) {
        timeout = setTimeout(() => {
          indexRef.current--
          setDisplayText(HEADLINE.slice(0, indexRef.current))
        }, DELETE_SPEED)
      } else {
        timeout = setTimeout(() => setPhase('typing'), PAUSE_AFTER_DELETE)
      }
    }
    return () => clearTimeout(timeout)
  }, [phase, displayText])

  return (
    <section id="hero" className="min-h-screen bg-white flex flex-col">
      {/* Hero content */}
      <div className="flex-1 flex items-center max-w-7xl mx-auto w-full px-6 pt-24 pb-16">
        <div className="grid lg:grid-cols-2 gap-12 items-center w-full">
          {/* Left: Text */}
          <div className="space-y-7">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold px-3 py-1.5 rounded-full">
              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
              AI-Powered Career Intelligence
            </div>

            {/* Animated headline */}
            <h1 className="text-5xl lg:text-6xl font-extrabold text-gray-900 leading-tight tracking-tight">
              {displayText}
              <span className="animate-blink text-blue-600 ml-0.5">|</span>
            </h1>

            {/* Subheading */}
            <p className="text-lg text-gray-500 leading-relaxed max-w-xl">
              An AI-driven platform to test your technical skills, analyze your blind spots, and generate a comprehensive evaluation report for your career growth.
            </p>

            {/* CTA buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                id="start-assessment-btn"
                onClick={onStartAssessment}
                className="
                  inline-flex items-center gap-2 px-7 py-3.5 rounded-xl
                  bg-blue-600 text-white font-semibold text-base
                  shadow-lg shadow-blue-200
                  transition-all duration-300
                  hover:scale-105 hover:bg-blue-700
                  hover:shadow-[0_0_20px_rgba(59,130,246,0.55)]
                  active:scale-95
                "
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Start Data Science Expert Assessment
              </button>

              <a
                href="#features"
                onClick={(e) => {
                  e.preventDefault()
                  document.querySelector('#features')?.scrollIntoView({ behavior: 'smooth' })
                }}
                className="
                  inline-flex items-center gap-1.5 px-5 py-3.5 text-base font-medium text-gray-600
                  border border-gray-200 rounded-xl
                  transition-all duration-200
                  hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50
                "
              >
                Learn More
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </a>
            </div>

            {/* Social proof stats */}
            <div className="flex items-center gap-8 pt-4 border-t border-gray-100">
              {[
                { value: '5K+', label: 'Assessments Taken' },
                { value: '98%', label: 'Accuracy Rate' },
                { value: '35', label: 'Questions Generated' },
              ].map(stat => (
                <div key={stat.label}>
                  <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                  <div className="text-xs text-gray-400 font-medium mt-0.5">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Decorative visual */}
          <div className="relative hidden lg:flex items-center justify-center">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-72 h-72 rounded-full bg-blue-50 opacity-60" />
              <div className="absolute w-56 h-56 rounded-full bg-blue-100 opacity-40" />
            </div>

            <div className="relative z-10 space-y-4">
              {/* Assessment card */}
              <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 w-80">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-semibold text-gray-700">Data Science Expert Assessment</span>
                  <span className="bg-green-100 text-green-600 text-xs font-semibold px-2 py-0.5 rounded-full">AI Generated</span>
                </div>
                <div className="space-y-2.5">
                  {['SQL', 'Python', 'Pandas', 'Data Visualization', 'Applied Statistics', 'Machine Learning', 'A/B Testing'].map((topic, i) => (
                    <div key={topic} className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${i < 2 ? 'bg-blue-500' : 'bg-gray-200'}`} />
                      <span className="text-sm text-gray-500">{topic}</span>
                      {i < 2 && <span className="ml-auto text-xs text-blue-500 font-medium">✓</span>}
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Progress</span>
                    <span>2 / 7 sections</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full w-1/3 bg-blue-600 rounded-full" />
                  </div>
                </div>
              </div>

              {/* Report card */}
              <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-xl p-5 w-72 ml-auto border border-gray-700">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0120 9.414V19a2 2 0 01-2 2z" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  <span className="text-white text-sm font-semibold">AI Evaluation Report</span>
                </div>
                <div className="text-gray-400 text-xs leading-relaxed">
                  Strong SQL fundamentals. Growth opportunity identified in window functions and advanced aggregations...
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <div className="flex-1 h-1 bg-gray-700 rounded-full overflow-hidden">
                    <div className="h-full w-4/5 bg-gradient-to-r from-blue-500 to-blue-400 rounded-full" />
                  </div>
                  <span className="text-blue-400 text-xs font-bold">80%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="flex justify-center pb-8 animate-bounce">
        <svg className="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M19 9l-7 7-7-7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </section>
  )
}
