import { useState, useRef, useEffect } from 'react'
import { Send, X } from 'lucide-react'

function accent(type) {
  if (type === 'npc') return { dot: '#f59e0b', ring: 'ring-amber-500/40', text: 'text-amber-300' }
  if (type === 'item') return { dot: '#06b6d4', ring: 'ring-cyan-500/40', text: 'text-cyan-300' }
  return { dot: '#64748b', ring: 'ring-slate-500/40', text: 'text-slate-300' }
}

export default function DialogueBox({ target, onAsk, onClose }) {
  const [messages, setMessages] = useState(() => [
    { role: 'npc', content: target.info || `You look closely at ${target.name}.` },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const a = accent(target.type)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const submit = async (e) => {
    e.preventDefault()
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: q }])
    setLoading(true)
    try {
      const answer = await onAsk(q)
      setMessages((m) => [...m, { role: 'npc', content: answer }])
    } catch {
      setMessages((m) => [...m, { role: 'npc', content: 'The signal fades… (backend unavailable)' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="pointer-events-none absolute bottom-0 left-0 right-[380px] z-40 flex justify-center px-4 pb-5">
      <div className={`pointer-events-auto w-full max-w-3xl overflow-hidden rounded-2xl border border-slate-700 bg-slate-900/95 shadow-2xl ring-1 backdrop-blur ${a.ring}`}>
        <div className="flex items-center justify-between border-b border-slate-700 bg-slate-800/60 px-4 py-2.5">
          <div className="flex items-center gap-3">
            <div
              className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-slate-900"
              style={{ backgroundColor: a.dot }}
            >
              {target.name?.slice(0, 1)?.toUpperCase() || '?'}
            </div>
            <div>
              <div className={`text-sm font-semibold ${a.text}`}>{target.name}</div>
              <div className="text-[11px] uppercase tracking-wide text-slate-500">{target.type}</div>
            </div>
          </div>
          <button
            onClick={onClose}
            title="Leave conversation (Esc)"
            className="rounded p-1 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="max-h-[38vh] space-y-2 overflow-y-auto px-4 py-3">
          {messages.map((m, i) =>
            m.role === 'user' ? (
              <div key={i} className="flex items-start justify-end gap-2">
                <div className="max-w-[80%] whitespace-pre-wrap rounded-lg rounded-tr-sm bg-cyan-500/15 px-3 py-2 text-sm text-cyan-100">
                  {m.content}
                </div>
                <div className="mt-0.5 h-6 w-6 shrink-0 rounded-full bg-cyan-500/30 text-center text-xs leading-6 text-cyan-200">
                  You
                </div>
              </div>
            ) : (
              <div key={i} className="flex items-start gap-2">
                <div
                  className="mt-0.5 h-6 w-6 shrink-0 rounded-full text-center text-xs font-bold leading-6 text-slate-900"
                  style={{ backgroundColor: a.dot }}
                >
                  {target.name?.slice(0, 1)?.toUpperCase() || '?'}
                </div>
                <div className="max-w-[80%] whitespace-pre-wrap rounded-lg rounded-tl-sm bg-slate-800/70 px-3 py-2 text-sm text-slate-200">
                  {m.content}
                </div>
              </div>
            ),
          )}
          {loading && (
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <div className="h-6 w-6 rounded-full bg-slate-700/60" />
              {target.name} is thinking…
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={submit} className="flex gap-2 border-t border-slate-700 bg-slate-800/30 p-3">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask ${target.name} something…`}
            className="flex-1 rounded-md bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none ring-1 ring-slate-700 focus:ring-cyan-400"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-cyan-500/20 px-3 py-2 text-cyan-300 hover:bg-cyan-500/30 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  )
}
