import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'

export default function ChatPanel({ messages, loading, onSend, lastInteraction }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const submit = (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    onSend(input)
    setInput('')
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-800 px-4 py-3">
        <div className="text-sm font-semibold text-slate-100">Company Brain</div>
        <div className="text-xs text-slate-400">RAG over FalkorDB knowledge graph</div>
      </div>

      {lastInteraction && (
        <div className="border-b border-slate-800 bg-cyan-500/5 px-4 py-2">
          <div className="text-xs text-cyan-400">Current focus: <span className="text-slate-200">{lastInteraction.name}</span></div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'ml-6' : 'mr-6'}>
            <div className={`rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
              m.role === 'user' ? 'bg-cyan-500/15 text-cyan-100' : 'bg-slate-800/60 text-slate-200'
            }`}>{m.content}</div>
          </div>
        ))}
        {loading && <div className="mr-6 rounded-lg bg-slate-800/60 px-3 py-2 text-xs text-slate-400">Searching graph…</div>}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={submit} className="border-t border-slate-800 p-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about people, projects, decisions…"
          className="flex-1 rounded-md bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none ring-1 ring-slate-700 focus:ring-cyan-400"
        />
        <button type="submit" disabled={loading} className="rounded-md bg-cyan-500/20 px-3 py-2 text-cyan-300 hover:bg-cyan-500/30 disabled:opacity-50">
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  )
}
