import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

// ─── Sub-components ──────────────────────────────────────────────────────────

function LoadingScreen({ user, dots }) {
  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center px-6 text-center">
      <LogoMark />
      <div className="mb-10 space-y-3">
        <AiBadge />
        <h1 className="text-4xl md:text-5xl font-extrabold text-white leading-tight">
          Welcome, <span className="text-blue-400">{user?.name || 'there'}</span>!
        </h1>
        <p className="text-gray-400 text-base max-w-md mx-auto leading-relaxed">
          Your personalized 35-question assessment is being prepared. This covers SQL,
          Python, Pandas, Data Visualization, Applied Statistics, Machine Learning, and A/B Testing.
        </p>
      </div>
      <Spinner />
      <p className="mt-6 text-gray-300 text-base font-medium tracking-wide">
        Fetching your customized Data Science Expert assessment
        <span className="text-blue-400 font-bold inline-block w-6 text-left">{dots}</span>
      </p>
      <p className="mt-10 text-xs text-gray-600 max-w-xs">
        Powered by Gemini AI — this may take 10–20 seconds. Please do not close this tab.
      </p>
    </div>
  )
}

function ErrorScreen({ message, onRetry }) {
  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center px-6 text-center">
      <LogoMark />
      <div className="w-16 h-16 rounded-2xl bg-red-900/40 border border-red-800/50 flex items-center justify-center mb-5">
        <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h2 className="text-2xl font-bold text-white mb-2">Failed to Load Assessment</h2>
      <p className="text-gray-400 text-sm max-w-sm mb-7 leading-relaxed">{message}</p>
      <button
        onClick={onRetry}
        className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-all duration-200 hover:scale-105 shadow-lg shadow-blue-900/40"
      >
        Try Again
      </button>
    </div>
  )
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────

function Sidebar({ sections, activeSectionIdx, completedSections, onSectionClick }) {
  return (
    <aside className="hidden lg:flex flex-col w-64 bg-gray-900 border-r border-gray-800 min-h-screen pt-6 pb-8 px-4 flex-shrink-0">
      <LogoMark small />
      <div className="mt-8 mb-3 px-2">
        <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Sections</span>
      </div>
      <nav className="flex flex-col gap-1">
        {sections.map((section, idx) => {
          const isCompleted = completedSections.has(idx)
          const isActive = idx === activeSectionIdx
          const isLocked = idx > 0 && !completedSections.has(idx - 1)

          return (
            <button
              key={idx}
              onClick={() => !isLocked && onSectionClick(idx)}
              disabled={isLocked}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 w-full
                ${isActive
                  ? 'bg-blue-600/20 border border-blue-600/40 text-blue-300'
                  : isCompleted
                    ? 'text-green-400 hover:bg-gray-800 border border-transparent'
                    : isLocked
                      ? 'text-gray-600 cursor-not-allowed border border-transparent'
                      : 'text-gray-400 hover:bg-gray-800 hover:text-white border border-transparent'
                }
              `}
            >
              {/* Status icon */}
              <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                {isCompleted ? (
                  <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : isLocked ? (
                  <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : (
                  <span className={`w-2 h-2 rounded-full ${isActive ? 'bg-blue-400' : 'bg-gray-600'}`} />
                )}
              </span>

              {/* Section name */}
              <span className="text-sm font-medium truncate leading-tight">{section.section_name}</span>

              {/* Active indicator bar */}
              {isActive && (
                <span className="ml-auto flex-shrink-0 w-1 h-5 rounded-full bg-blue-500" />
              )}
            </button>
          )
        })}
      </nav>

      {/* Overall progress */}
      <div className="mt-auto pt-6 border-t border-gray-800">
        <div className="flex justify-between text-xs text-gray-500 mb-2">
          <span>Overall Progress</span>
          <span>{completedSections.size} / {sections.length}</span>
        </div>
        <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-500"
            style={{ width: `${(completedSections.size / sections.length) * 100}%` }}
          />
        </div>
      </div>
    </aside>
  )
}

// ─── Question Card ────────────────────────────────────────────────────────────

function QuestionCard({
  section,
  questionIdx,
  selectedOption,
  onSelectOption,
  onNext,
  onSkip,
  onSubmit,
  isLastQuestion,
  isLastSection,
  sectionProgress,   // { current, total }
}) {
  const question = section.questions[questionIdx]
  const isSubmitBtn = isLastQuestion && isLastSection
  const canProceed = selectedOption !== null

  // Difficulty badge colours
  const difficultyColor = {
    Easy: 'bg-green-900/40 text-green-400 border-green-800/40',
    Moderate: 'bg-yellow-900/40 text-yellow-400 border-yellow-800/40',
    Advanced: 'bg-red-900/40 text-red-400 border-red-800/40',
  }[question.difficulty] || 'bg-gray-800 text-gray-400 border-gray-700'

  return (
    <div className="flex flex-col h-full">
      {/* Section header */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">{section.section_name}</p>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-300">
              Question {sectionProgress.current} of {sectionProgress.total}
            </span>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${difficultyColor}`}>
              {question.difficulty}
            </span>
          </div>
        </div>
        {/* Mini progress dots */}
        <div className="flex gap-1.5">
          {section.questions.map((_, i) => (
            <span
              key={i}
              className={`w-2 h-2 rounded-full transition-all duration-300 ${i < questionIdx ? 'bg-green-500' : i === questionIdx ? 'bg-blue-500' : 'bg-gray-700'
                }`}
            />
          ))}
        </div>
      </div>

      {/* Question text — rendered as Markdown */}
      <div className="mb-6 flex-1">
        <div className="text-white text-base md:text-lg font-medium leading-relaxed prose-question">
          <ReactMarkdown components={markdownComponents} rehypePlugins={[rehypeKatex]} remarkPlugins={[remarkMath]}>{question.text}</ReactMarkdown>
        </div>
      </div>

      {/* Options */}
      <div className="space-y-3 mb-8">
        {question.options.map((option, i) => {
          const isSelected = selectedOption === option
          const letters = ['A', 'B', 'C', 'D']
          return (
            <button
              key={i}
              onClick={() => onSelectOption(option)}
              className={`
                w-full flex items-start gap-3.5 px-4 py-3.5 rounded-xl border text-left
                transition-all duration-200 group
                ${isSelected
                  ? 'border-blue-500 bg-blue-600/20 shadow-[0_0_0_1px_rgba(59,130,246,0.5)]'
                  : 'border-gray-700 bg-gray-800/60 hover:border-gray-600 hover:bg-gray-800'
                }
              `}
            >
              {/* Option letter badge */}
              <span className={`
                flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold mt-0.5
                transition-colors duration-200
                ${isSelected ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400 group-hover:bg-gray-600 group-hover:text-gray-200'}
              `}>
                {letters[i]}
              </span>
              <span className={`text-sm leading-relaxed ${isSelected ? 'text-white' : 'text-gray-300'} option-markdown`}>
                <ReactMarkdown components={optionMarkdownComponents} rehypePlugins={[rehypeKatex]} remarkPlugins={[remarkMath]}>{option}</ReactMarkdown>
              </span>
              {/* Checkmark when selected */}
              {isSelected && (
                <span className="ml-auto flex-shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Action area */}
      <div className="flex items-center justify-between">
        {/* Skip — only shown on non-submit questions */}
        {!isSubmitBtn ? (
          <button
            onClick={onSkip}
            className="text-gray-400 text-sm font-medium transition-all duration-200 hover:text-blue-400 hover:drop-shadow-[0_0_8px_rgba(59,130,246,0.5)] focus:outline-none"
          >
            Skip
          </button>
        ) : (
          <span />
        )}

        {/* Primary action */}
        {isSubmitBtn ? (
          <button
            onClick={onSubmit}
            disabled={!canProceed}
            className={`
              inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-bold text-sm
              transition-all duration-300
              ${canProceed
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40 hover:bg-blue-700 hover:scale-105 hover:shadow-[0_0_20px_rgba(59,130,246,0.4)]'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
              }
            `}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Submit Assessment
          </button>
        ) : (
          <button
            onClick={onNext}
            disabled={!canProceed}
            className={`
              inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm
              transition-all duration-200
              ${canProceed
                ? 'bg-gray-700 text-white hover:bg-blue-600 hover:scale-105 hover:shadow-[0_0_16px_rgba(59,130,246,0.4)]'
                : 'bg-gray-800 text-gray-600 cursor-not-allowed'
              }
            `}
          >
            {isLastQuestion ? 'Next Section' : 'Next Question'}
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        )}
      </div>
    </div>
  )
}

// ─── Markdown component maps ──────────────────────────────────────────────────

/** Shared renderer for question body — full markdown support with dark-theme styling */
const markdownComponents = {
  // Fenced code blocks
  pre({ children }) {
    return (
      <pre className="mt-3 mb-3 bg-gray-900 border border-gray-800 rounded-xl p-4 text-sm text-blue-300 font-mono overflow-x-auto whitespace-pre leading-relaxed">
        {children}
      </pre>
    )
  },
  // Inline code
  code({ inline, children }) {
    if (inline) {
      return (
        <code className="bg-gray-800/80 rounded px-1.5 py-0.5 text-blue-400 font-mono text-[0.85em] border border-gray-700">
          {children}
        </code>
      )
    }
    return <code className="font-mono text-blue-400">{children}</code>
  },
  // Bold
  strong({ children }) {
    return <strong className="font-bold text-white">{children}</strong>
  },
  // Paragraphs
  p({ children }) {
    return <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
  },
  // Unordered lists
  ul({ children }) {
    return <ul className="list-disc list-inside mb-2 space-y-1 text-gray-200">{children}</ul>
  },
  // Ordered lists
  ol({ children }) {
    return <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-200">{children}</ol>
  },
  li({ children }) {
    return <li className="leading-relaxed">{children}</li>
  },
}

/** Lighter renderer for option labels — inline-only, no block elements */
const optionMarkdownComponents = {
  // Inline code inside options
  code({ inline, children }) {
    if (inline) {
      return (
        <code className="bg-gray-800/80 rounded px-1.5 py-0.5 text-blue-400 font-mono text-[0.85em] border border-gray-700">
          {children}
        </code>
      )
    }
    return <code className="font-mono text-blue-400">{children}</code>
  },
  // Bold inside options
  strong({ children }) {
    return <strong className="font-bold text-white">{children}</strong>
  },
  // Unwrap paragraphs so options stay inline
  p({ children }) {
    return <span>{children}</span>
  },
}

function LogoMark({ small }) {
  return (
    <div className={`flex items-center gap-2 select-none ${small ? '' : 'mb-10'}`}>
      <div className={`${small ? 'w-7 h-7' : 'w-9 h-9'} rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/50`}>
        <svg className={`${small ? 'w-4 h-4' : 'w-5 h-5'} text-white`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <span className={`${small ? 'text-base' : 'text-xl'} tracking-tight`}>
        <span className="font-extrabold text-blue-400">Cognitive</span>
        <span className="font-medium text-gray-400 ml-1">Assessment</span>
      </span>
    </div>
  )
}

function AiBadge() {
  return (
    <span className="inline-flex items-center gap-2 bg-blue-900/40 border border-blue-800/50 text-blue-400 text-xs font-semibold px-3 py-1.5 rounded-full">
      <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
      Data Science Expert Assessment
    </span>
  )
}

function Spinner() {
  return (
    <div className="relative">
      <div className="absolute inset-0 rounded-full bg-blue-600/20 blur-xl scale-110" />
      <div className="relative w-16 h-16">
        <svg className="w-16 h-16 animate-spin text-blue-600" viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="6" strokeOpacity="0.15" />
          <path d="M32 4a28 28 0 0 1 28 28" stroke="currentColor" strokeWidth="6" strokeLinecap="round" />
        </svg>
      </div>
    </div>
  )
}

// ─── Mobile section progress bar ─────────────────────────────────────────────

function MobileProgressBar({ sections, activeSectionIdx, completedSections }) {
  return (
    <div className="lg:hidden flex items-center gap-1.5 px-4 py-3 bg-gray-900 border-b border-gray-800 overflow-x-auto">
      {sections.map((s, idx) => {
        const isCompleted = completedSections.has(idx)
        const isActive = idx === activeSectionIdx
        return (
          <div key={idx} className="flex flex-col items-center gap-1 flex-shrink-0">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center ${isCompleted ? 'bg-green-500' : isActive ? 'bg-blue-600' : 'bg-gray-700'
              }`}>
              {isCompleted ? (
                <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                  <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              ) : (
                <span className="text-white text-xs font-bold">{idx + 1}</span>
              )}
            </div>
            <span className={`text-[9px] font-medium text-center max-w-[52px] leading-tight ${isActive ? 'text-blue-400' : isCompleted ? 'text-green-500' : 'text-gray-600'
              }`}>
              {s.section_name.split(' ')[0]}
            </span>
          </div>
        )
      })}
    </div>
  )
}

// ─── Main QuizComponent ───────────────────────────────────────────────────────

export default function QuizComponent({ user }) {
  // Fetch state
  const [quizData, setQuizData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(null)
  const [dots, setDots] = useState('.')

  // Quiz navigation state
  const [activeSectionIdx, setActiveSectionIdx] = useState(0)
  const [activeQuestionIdx, setActiveQuestionIdx] = useState(0)
  const [selectedOption, setSelectedOption] = useState(null)
  const [completedSections, setCompletedSections] = useState(new Set())

  // Track all answers: { sectionIdx-questionIdx: { question_text, user_answer, correct_answer, explanation, section_name } }
  const answersRef = useRef({})

  const fetchIdRef = useRef(0)

  // ── Animated ellipsis ──────────────────────────────────────────────
  useEffect(() => {
    if (!loading) return
    const id = setInterval(() => setDots(d => d.length >= 3 ? '.' : d + '.'), 500)
    return () => clearInterval(id)
  }, [loading])

  // ── Fetch quiz data ────────────────────────────────────────────────
  async function fetchQuiz() {
    const currentId = ++fetchIdRef.current
    setLoading(true)
    setFetchError(null)
    setQuizData(null)
    setActiveSectionIdx(0)
    setActiveQuestionIdx(0)
    setSelectedOption(null)
    setCompletedSections(new Set())
    answersRef.current = {}

    try {
      const res = await fetch('http://localhost:8000/api/generate-quiz', {
        method: 'POST',
      })
      if (!res.ok) throw new Error(`Server responded with status ${res.status}: ${res.statusText}`)
      const data = await res.json()

      if (currentId !== fetchIdRef.current) return   // stale response — ignore

      if (!data.sections || data.sections.length === 0) {
        throw new Error('The server returned an empty quiz. Please try again.')
      }
      setQuizData(data)
    } catch (err) {
      if (currentId !== fetchIdRef.current) return
      setFetchError(err.message || 'An unknown error occurred while fetching the assessment.')
    } finally {
      if (currentId === fetchIdRef.current) setLoading(false)
    }
  }

  useEffect(() => { fetchQuiz() }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  // ── Event handlers ─────────────────────────────────────────────────

  function handleSelectOption(option) {
    setSelectedOption(option)
  }

  /**
   * Central navigation helper.
   * @param {number} newSectionIdx  - Target section index.
   * @param {number} newQuestionIdx - Target question index.
   * @param {boolean} saveAnswer    - Whether to persist selectedOption before moving.
   */
  function goToQuestion(newSectionIdx, newQuestionIdx, saveAnswer = true) {
    if (!quizData) return

    // 1. Optionally persist the current answer
    if (saveAnswer && selectedOption !== null) {
      const section = quizData.sections[activeSectionIdx]
      const question = section.questions[activeQuestionIdx]
      answersRef.current[`${activeSectionIdx}-${activeQuestionIdx}`] = {
        section_name: section.section_name,
        question_text: question.text,
        user_answer: selectedOption,
        correct_answer: question.correct_answer,
        explanation: question.explanation,
      }
    }

    // 2. Navigate
    setActiveSectionIdx(newSectionIdx)
    setActiveQuestionIdx(newQuestionIdx)

    // 3. Restore a previously saved answer for the destination, or clear
    const saved = answersRef.current[`${newSectionIdx}-${newQuestionIdx}`]
    setSelectedOption(saved ? saved.user_answer : null)
  }

  function handleNext() {
    if (!quizData || selectedOption === null) return

    const section = quizData.sections[activeSectionIdx]
    const isLastQuestion = activeQuestionIdx === section.questions.length - 1

    if (isLastQuestion) {
      // Mark this section complete, then move to the first question of the next section
      setCompletedSections(prev => new Set([...prev, activeSectionIdx]))
      goToQuestion(activeSectionIdx + 1, 0, true)
    } else {
      goToQuestion(activeSectionIdx, activeQuestionIdx + 1, true)
    }
  }

  function handleSkip() {
    if (!quizData) return

    const section = quizData.sections[activeSectionIdx]
    const isLastQuestion = activeQuestionIdx === section.questions.length - 1

    if (isLastQuestion) {
      // Move to next section without saving an answer or marking complete
      goToQuestion(activeSectionIdx + 1, 0, false)
    } else {
      goToQuestion(activeSectionIdx, activeQuestionIdx + 1, false)
    }
  }

  function handleSubmit() {
    if (!quizData || selectedOption === null) return

    const section = quizData.sections[activeSectionIdx]
    const question = section.questions[activeQuestionIdx]

    // Record the final answer
    answersRef.current[`${activeSectionIdx}-${activeQuestionIdx}`] = {
      section_name: section.section_name,
      question_text: question.text,
      user_answer: selectedOption,
      correct_answer: question.correct_answer,
      explanation: question.explanation,
    }

    // Mark final section complete
    setCompletedSections(prev => new Set([...prev, activeSectionIdx]))

    // Tally results
    const allAnswers = Object.values(answersRef.current)
    const wrongAnswers = allAnswers.filter(a => a.user_answer !== a.correct_answer)
    const score = allAnswers.length - wrongAnswers.length

    // ── Show score alert INSTANTLY (synchronous, never blocked) ───────────
    alert(`✅ Assessment complete!\nScore: ${score} / ${allAnswers.length}\n\nYour results are being saved in the background.`)

    // ── Build per-section score breakdown ─────────────────────────────────
    const sectionScores = {}
    quizData.sections.forEach(sec => {
      const secAnswers = allAnswers.filter(a => a.section_name === sec.section_name)
      const secCorrect = secAnswers.filter(a => a.user_answer === a.correct_answer).length
      sectionScores[sec.section_name] = secCorrect
    })

    // ── Fire-and-forget POST — do NOT await, do NOT block UI ──────────────
    fetch('http://localhost:8000/api/submit-answers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name:            user?.name  || 'Anonymous',
        email:           user?.email || '',
        score,
        total_questions: allAnswers.length,
        wrong_answers:   wrongAnswers,
        section_scores:  sectionScores,
      }),
    }).catch(err => console.warn('Background submission error (non-fatal):', err))
  }

  function handleSectionClick(idx) {
    goToQuestion(idx, 0, true)
  }

  // ── Render states ──────────────────────────────────────────────────

  if (loading) {
    return <LoadingScreen user={user} dots={dots} />
  }

  if (fetchError) {
    return <ErrorScreen message={fetchError} onRetry={fetchQuiz} />
  }

  if (!quizData) return null

  const sections = quizData.sections
  const activeSection = sections[activeSectionIdx]
  const isLastSection = activeSectionIdx === sections.length - 1
  const isLastQuestion = activeQuestionIdx === activeSection.questions.length - 1

  return (
    <div className="flex min-h-screen bg-gray-950">
      {/* Sidebar */}
      <Sidebar
        sections={sections}
        activeSectionIdx={activeSectionIdx}
        completedSections={completedSections}
        onSectionClick={handleSectionClick}
      />

      {/* Main area */}
      <div className="flex flex-col flex-1 min-h-screen">
        {/* Top bar */}
        <header className="flex items-center justify-between px-6 py-4 bg-gray-900 border-b border-gray-800 lg:hidden">
          <LogoMark small />
          <span className="text-sm text-gray-400 font-medium">
            Hi, <span className="text-white font-semibold">{user?.name}</span>
          </span>
        </header>

        {/* Desktop top bar */}
        <header className="hidden lg:flex items-center justify-between px-8 py-4 bg-gray-900 border-b border-gray-800">
          <div>
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">
              {activeSection.section_name}
            </span>
            <p className="text-sm text-gray-300 font-medium mt-0.5">
              Q{activeQuestionIdx + 1} of {activeSection.questions.length}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400">
              Hi, <span className="text-white font-semibold">{user?.name}</span>
            </span>
            <div className="w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-bold flex items-center justify-center">
              {user?.name?.charAt(0).toUpperCase() || '?'}
            </div>
          </div>
        </header>

        {/* Mobile section progress */}
        <MobileProgressBar
          sections={sections}
          activeSectionIdx={activeSectionIdx}
          completedSections={completedSections}
        />

        {/* Question area */}
        <main className="flex-1 overflow-y-auto px-6 md:px-12 lg:px-16 py-10 max-w-3xl w-full mx-auto">
          <QuestionCard
            key={`${activeSectionIdx}-${activeQuestionIdx}`}
            section={activeSection}
            questionIdx={activeQuestionIdx}
            selectedOption={selectedOption}
            onSelectOption={handleSelectOption}
            onNext={handleNext}
            onSkip={handleSkip}
            onSubmit={handleSubmit}
            isLastQuestion={isLastQuestion}
            isLastSection={isLastSection}
            sectionProgress={{
              current: activeQuestionIdx + 1,
              total: activeSection.questions.length,
            }}
          />
        </main>
      </div>
    </div>
  )
}
