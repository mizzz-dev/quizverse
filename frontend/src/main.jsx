import React from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

function App() {
  return (
    <main className="min-h-screen p-8">
      <h1 className="text-3xl font-bold">QuizVerse MVP</h1>
      <p className="mt-4 text-slate-300">React + Flask + PostgreSQL の開発基盤を構築しました。</p>
    </main>
  )
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
