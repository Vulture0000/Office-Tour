import { useCallback, useState } from 'react'
import GameCanvas from './game/GameCanvas.jsx'
import ChatPanel from './chat/ChatPanel.jsx'
import DialogueBox from './chat/DialogueBox.jsx'
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
    setPopup({ ...obj, _nonce: Date.now() })
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

  const askInDialogue = useCallback(async (text, target) => {
    const res = await api.post('/chat', {
      message: text,
      context: {
        ...context,
        room: target.roomId || context.room,
        entity_id: target.id,
        entity_type: target.type,
        lastInteraction: target,
      },
    })
    return res.data.answer
  }, [context])

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
        <DialogueBox
          key={popup._nonce}
          target={popup}
          onAsk={(text) => askInDialogue(text, popup)}
          onClose={() => setPopup(null)}
        />
      )}
    </div>
  )
}
