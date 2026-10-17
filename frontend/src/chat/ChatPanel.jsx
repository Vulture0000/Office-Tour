import { useState } from 'react'
import { Send } from 'lucide-react'
import { api } from '../services/apiClient.js'

export default function ChatPanel({ context, onFocusEntity }) {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! I am the Company Brain. Ask me anything about people, projects, decisions, or the graph.' }
  ])
  const [loading, setLoading] = useState(false)

  const handleSend = async (e) => {
    e.preventDefault()
    if (!message.trim()) return
    const userMsg = { role: 'user', content: message }
    setMessages((m) => [...m, userMsg])
    setMessage('')
    setLoading(true)
    try {
      const res = await api.post('/chat', {
        message: message.trim(),
        context
      })
      setMessages((m) => [...m, { role: 'assistant', content: res.data.answer }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: 'Sorry, something went wrong. Check the backend.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-800 p-3">
        <div className="text-sm font-semibold">Chat</div>
        <div className="text-xs text-slate-400">Ask about NovaTech knowledge graph</div>
      </div>
      <div className="flex-1 overflow-y-auto panel-scroll p-3 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === 'user' ? 'ml-auto max-w-[85%]' : 'mr-auto max-w-[85%]'}>
            <div className={`rounded-lg px-3 py-2 text-sm ${msg.role === 'user' ? 'bg-cyan-500/20 text-cyan-100' : 'bg-slate-800/70 text-slate-200'}`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="mr-auto max-w-[85%] rounded-lg bg-slate-800/70 px-3 py-2 text-xs text-slate-400">
            Thinking...
          </div>
        )}
      </div>
      <form onSubmit={handleSend} className="border-t border-slate-800 p-3 flex gap-2">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask something..."
          className="flex-1 rounded-md bg-slate-900/70 px-3 py-2 text-sm text-slate-200 outline-none ring-1 ring-slate-700 focus:ring-cyan-400"
        />
        <button type="submit" disabled={loading} className="rounded-md bg-cyan-500/20 px-2 py-2 text-cyan-300 hover:bg-cyan-500/30 disabled:opacity-50">
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  )
}
