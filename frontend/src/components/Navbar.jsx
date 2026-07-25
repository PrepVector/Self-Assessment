import { useState } from 'react'

const navLinks = [
  { label: 'Home',         href: '#hero' },
  { label: 'Features',     href: '#features' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'FAQs',         href: '#faqs' },
  { label: 'Contact',      href: '#contact' },
]

export default function Navbar({ user, onStartAssessment }) {
  const [menuOpen, setMenuOpen] = useState(false)

  function handleNavLinkClick(e, href) {
    e.preventDefault()
    const target = document.querySelector(href)
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' })
    }
    setMenuOpen(false)
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo */}
        <a
          href="#hero"
          className="flex items-center gap-2 select-none"
          aria-label="Go to homepage"
          onClick={(e) => handleNavLinkClick(e, '#hero')}
        >
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-md">
            <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span className="text-lg tracking-tight">
            <span className="font-extrabold text-blue-600">Cognitive</span>
            <span className="font-medium text-gray-700 ml-1">Assessment</span>
          </span>
        </a>

        {/* Desktop nav links */}
        <ul className="hidden md:flex items-center gap-8">
          {navLinks.map(link => (
            <li key={link.label}>
              <a
                href={link.href}
                onClick={(e) => handleNavLinkClick(e, link.href)}
                className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors duration-200 relative group"
              >
                {link.label}
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-blue-600 transition-all duration-300 group-hover:w-full rounded-full" />
              </a>
            </li>
          ))}
        </ul>

        {/* CTA — desktop */}
        <div className="hidden md:flex items-center gap-3">
          {user?.name ? (
            /* Active candidate: show avatar + name */
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-blue-600 text-white text-sm font-bold flex items-center justify-center select-none shadow">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <span className="text-sm font-medium text-gray-700">{user.name}</span>
            </div>
          ) : (
            <button
              id="navbar-get-started-btn"
              onClick={onStartAssessment}
              className="text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg shadow transition-all duration-200 hover:shadow-md hover:scale-105"
            >
              Get Started
            </button>
          )}
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors duration-200"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle navigation menu"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
            {menuOpen
              ? <path d="M6 18L18 6M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
              : <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" strokeLinejoin="round" />
            }
          </svg>
        </button>
      </div>

      {/* Mobile dropdown menu */}
      {menuOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 px-6 py-4 space-y-3 shadow-lg">
          {navLinks.map(link => (
            <a
              key={link.label}
              href={link.href}
              className="block text-sm font-medium text-gray-600 hover:text-blue-600 py-1.5 transition-colors duration-200"
              onClick={(e) => handleNavLinkClick(e, link.href)}
            >
              {link.label}
            </a>
          ))}
          <div className="pt-3 border-t border-gray-100">
            {user?.name ? (
              <div className="flex items-center gap-2 py-1">
                <div className="w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <span className="text-sm text-gray-700 font-medium">{user.name}</span>
              </div>
            ) : (
              <button
                id="navbar-get-started-mobile-btn"
                onClick={() => { onStartAssessment(); setMenuOpen(false) }}
                className="w-full text-sm font-semibold text-white bg-blue-600 px-4 py-2 rounded-lg text-center"
              >
                Get Started
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
