import { useCallback, useState } from 'react'
import GameCanvas from './game/GameCanvas.jsx'
import ChatPanel from './chat/ChatPanel.jsx'

export default function App() {
  const [context, setContext] = useState({ room: 'reception' })

  const handleRoomChange = useCallback((data) => {
    setContext((prev) => ({ ...prev, room: data.room, roomName: data.name }))
  }, [])

  const handleInteract = useCallback((obj) => {
    setContext((prev) => ({ ...prev, lastInteraction: obj }))
  }, [])

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-slate-950">
      <div className="absolute inset-0">
        <GameCanvas onRoomChange={handleRoomChange} onInteract={handleInteract} />
      </div>

      <div className="absolute bottom-4 left-4 z-10 rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-2 text-xs text-slate-300 backdrop-blur">
        <span className="text-cyan-400 font-semibold">WASD / Arrows</span> to move · <span className="text-green-400 font-semibold">E</span> to interact · Green = doors
      </div>

      <aside className="absolute right-0 top-0 bottom-0 z-10 w-[380px] border-l border-slate-800 bg-slate-950/95 backdrop-blur">
        <ChatPanel context={context} />
      </aside>
    </div>
  )
}
