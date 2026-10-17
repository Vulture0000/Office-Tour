import { useCallback, useState, useEffect } from 'react'
import { X, MessageCircle } from 'lucide-react'
import GameCanvas from './game/GameCanvas.jsx'
import ChatPanel from './chat/ChatPanel.jsx'
import { api } from './services/apiClient.js'

export default function App() {
  const [context, setContext] = useState({ room: 'reception' })
  const [popup, setPopup] = useState(null)
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: 'Ask me anything about NovaTech — people, projects, decisions, systems, or what you see in the office.' },
  ])
  const [chatLoading, setChatLoading] = useState(false)

  const handleRoomChange = useCallback((data) => {
    setContext((prev) => ({ ...prev, room: data.room, roomName: data.name }))
  }, [])

  const handleInteract = useCallback((obj) => {
    setContext((prev) => ({ ...prev, lastInteraction: obj }))
    setPopup(obj)
  }, [])

  const sendChat = useCallback(async (text, extraCtx) => {
    if (!text.trim() || chatLoading) return
    const q = text.trim()
    setChatMessages((m) => [...m, { role: 'user', content: q }])
    setChatLoading(true)
    try {
      const res = await api.post('/chat', {
        message: q,
        context: { ...context, ...extraCtx },
      })
      setChatMessages((m) => [...m, { role: 'assistant', content: res.data.answer }])
    } catch {
      setChatMessages((m) => [...m, { role: 'assistant', content: 'Backend unavailable. Start it with ./run_backend.sh' }])
    } finally {
      setChatLoading(false)
    }
  }, [context, chatLoading])

  const askAboutPopup = () => {
    if (!popup) return
    sendChat(`Tell me about ${popup.name}`, { entity_id: popup.id, entity_type: popup.type, room: popup.roomId || context.room })
    setPopup(null)
  }

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-slate-950">
      <div className="absolute inset-0">
        <GameCanvas onRoomChange={handleRoomChange} onInteract={handleInteract} />
      </div>

      <div className="absolute bottom-4 left-4 z-10 rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-2 text-xs text-slate-300 backdrop-blur">
        <span className="text-cyan-400 font-semibold">WASD / Arrows</span> to move · <span className="text-green-400 font-semibold">E</span> to interact · Green = doors
      </div>

      <aside className="absolute right-0 top-0 bottom-0 z-10 w-[380px] border-l border-slate-800 bg-slate-950/95 backdrop-blur">
        <ChatPanel
          messages={chatMessages}
          loading={chatLoading}
          onSend={sendChat}
          lastInteraction={context.lastInteraction}
        />
      </aside>

      {popup && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setPopup(null)}>
          <div
            className="w-[420px] rounded-xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-700 bg-slate-800/50 px-4 py-3">
              <div className="flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: popup.type === 'npc' ? '#f59e0b' : popup.type === 'item' ? '#06b6d4' : '#64748b' }}
                />
                <div>
                  <div className="text-sm font-semibold text-slate-100">{popup.name}</div>
                  <div className="text-xs text-slate-400 capitalize">{popup.type}</div>
                </div>
              </div>
              <button onClick={() => setPopup(null)} className="rounded p-1 text-slate-400 hover:bg-slate-700 hover:text-slate-200">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="px-4 py-4 text-sm text-slate-300 leading-relaxed">
              {popup.info}
            </div>
            <div className="flex gap-2 border-t border-slate-700 px-4 py-3">
              <button
                onClick={askAboutPopup}
                className="flex items-center gap-2 rounded-lg bg-cyan-500/20 px-3 py-2 text-sm text-cyan-300 hover:bg-cyan-500/30"
              >
                <MessageCircle className="h-4 w-4" />
                Ask about this
              </button>
              <button
                onClick={() => setPopup(null)}
                className="rounded-lg bg-slate-700/50 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
