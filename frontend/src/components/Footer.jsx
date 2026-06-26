export default function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className="bg-gray-950 border-t border-gray-800 pt-14 pb-8 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-4 gap-10 mb-12">
          {/* Brand column */}
          <div className="md:col-span-1 space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <span className="text-sm tracking-tight">
                <span className="font-extrabold text-blue-400">Cognitive</span>
                <span className="font-medium text-gray-400 ml-1">Assessment</span>
              </span>
            </div>
            <p className="text-gray-500 text-xs leading-relaxed">
              AI-powered technical assessments and career evaluation reports — built for data professionals.
            </p>
          </div>

          {/* Links columns */}
          {[
            {
              heading: 'Platform',
              links: ['Start Assessment', 'How It Works', 'Features', 'FAQ'],
            },
            {
              heading: 'Legal',
              links: ['Privacy Policy', 'Terms of Service', 'Cookie Policy'],
            },
            {
              heading: 'Connect',
              links: ['Contact Us', 'GitHub', 'LinkedIn', 'Twitter / X'],
            },
          ].map(col => (
            <div key={col.heading}>
              <h4 className="text-white text-xs font-bold uppercase tracking-widest mb-4">{col.heading}</h4>
              <ul className="space-y-2.5">
                {col.links.map(link => (
                  <li key={link}>
                    <a href="#" className="text-gray-500 text-sm hover:text-blue-400 transition-colors duration-200">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-800 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-gray-600 text-xs">
            © {year} Cognitive Assessment. All rights reserved.
          </p>
          <p className="text-gray-700 text-xs">
            Powered by Google Gemini AI &amp; FastAPI
          </p>
        </div>
      </div>
    </footer>
  )
}
