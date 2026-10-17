import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { api } from '../services/apiClient.js'

export default function ChatPanel({ context }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Ask me anything about NovaTech — people, projects, decisions, systems, or what you see in the office.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text, extraCtx) => {
    if (!text.trim() || loading) return
    const q = text.trim()
    setMessages((m) => [...m, { role: 'user', content: q }])
    setInput('')
    setLoading(true)
    try {
      const res = await api.post('/chat', {
        message: q,
        context: { ...context, ...extraCtx },
      })
      setMessages((m) => [...m, { role: 'assistant', content: res.data.answer }])
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: 'Backend unavailable. Start it with ./run_backend.sh' }])
    } finally {
      setLoading(false)
    }
  }

  const askAbout = (obj) => {
    send(`Tell me about ${obj.name}`, { entity_id: obj.id, entity_type: obj.type, room: obj.roomId || context.room })
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-800 px-4 py-3">
        <div className="text-sm font-semibold text-slate-100">Company Brain</div>
        <div className="text-xs text-slate-400">RAG over FalkorDB knowledge graph</div>
      </div>

      {context.lastInteraction && (
        <div className="border-b border-slate-800 bg-cyan-500/5 px-4 py-3">
          <div className="text-xs text-cyan-400 mb-1">Interacted with</div>
          <div className="text-sm font-medium text-slate-200">{context.lastInteraction.name}</div>
          <div className="text-xs text-slate-400 mt-1">{context.lastInteraction.info}</div>
          <button
            onClick={() => askAbout(context.lastInteraction)}
            className="mt-2 rounded bg-cyan-500/20 px-2 py-1 text-xs text-cyan-300 hover:bg-cyan-500/30"
          >
            Ask about this
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'ml-4' : 'mr-4'}>
            <div className={`rounded-lg px-3 py-2 text-sm ${
              m.role === 'user' ? 'bg-cyan-500/15 text-cyan-100' : 'bg-slate-800/60 text-slate-200'
            }`}>{m.content}</div>
          </div>
        ))}
        {loading && <div className="mr-4 rounded-lg bg-slate-800/60 px-3 py-2 text-xs text-slate-400">Searching graph…</div>}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send(input) }} className="border-t border-slate-800 p-3 flex gap-2">
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
