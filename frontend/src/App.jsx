import { useEffect, useMemo, useState } from 'react'
import { MessageSquare, Network, Users, FolderOpen, FileText, ClipboardCheck, Search, Activity, Gamepad2, PanelLeftClose, PanelLeftOpen } from 'lucide-react'

import GameCanvas from './game/GameCanvas.jsx'
import ChatPanel from './chat/ChatPanel.jsx'
import GraphPanel from './graph/GraphPanel.jsx'
import PeoplePanel from './components/PeoplePanel.jsx'
import ProjectsPanel from './components/ProjectsPanel.jsx'
import DocumentsPanel from './components/DocumentsPanel.jsx'
import DecisionsPanel from './components/DecisionsPanel.jsx'
import TicketsPanel from './components/TicketsPanel.jsx'
import SystemsPanel from './components/SystemsPanel.jsx'
import ActionsPanel from './components/ActionsPanel.jsx'
import SearchPanel from './components/SearchPanel.jsx'
import WorldInfo from './components/WorldInfo.jsx'
import { api } from './services/apiClient.js'

const PANELS = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'graph', label: 'Graph', icon: Network },
  { id: 'people', label: 'People', icon: Users },
  { id: 'projects', label: 'Projects', icon: FolderOpen },
  { id: 'documents', label: 'Docs', icon: FileText },
  { id: 'decisions', label: 'Decisions', icon: ClipboardCheck },
  { id: 'tickets', label: 'Tickets', icon: Activity },
  { id: 'systems', label: 'Systems', icon: Gamepad2 },
  { id: 'actions', label: 'Actions', icon: ClipboardCheck },
  { id: 'search', label: 'Search', icon: Search },
]

function PanelView({ active, context, onContextUpdate, onFocusEntity }) {
  switch (active) {
    case 'chat':
      return <ChatPanel context={context} onFocusEntity={onFocusEntity} />
    case 'graph':
      return <GraphPanel context={context} onFocusEntity={onFocusEntity} />
    case 'people':
      return <PeoplePanel onFocusEntity={onFocusEntity} />
    case 'projects':
      return <ProjectsPanel onFocusEntity={onFocusEntity} />
    case 'documents':
      return <DocumentsPanel onFocusEntity={onFocusEntity} />
    case 'decisions':
      return <DecisionsPanel onFocusEntity={onFocusEntity} />
    case 'tickets':
      return <TicketsPanel onFocusEntity={onFocusEntity} />
    case 'systems':
      return <SystemsPanel onFocusEntity={onFocusEntity} />
    case 'actions':
      return <ActionsPanel />
    case 'search':
      return <SearchPanel onFocusEntity={onFocusEntity} />
    default:
      return <ChatPanel context={context} onFocusEntity={onFocusEntity} />
  }
}

export default function App() {
  const [active, setActive] = useState('chat')
  const [context, setContext] = useState({ room: 'room_reception' })
  const [world, setWorld] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [focusTrigger, setFocusTrigger] = useState(null)

  useEffect(() => {
    api.get('/world').then((res) => setWorld(res.data)).catch(() => {})
  }, [])

  const roomLabel = useMemo(() => {
    if (!world) return 'NovaTech'
    const room = world.objects.find((obj) => obj.id === context.room || obj.room === context.room)
    return room?.name || 'NovaTech'
  }, [world, context.room])

  const handleContextChange = (next) => {
    setContext((prev) => ({ ...prev, ...next }))
    setActive('chat')
  }

  const handleFocusEntity = (entity) => {
    setFocusTrigger(entity)
  }

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-slate-950">
      <div className="absolute inset-x-0 top-0 z-20 flex items-center justify-between bg-slate-950/70 px-4 py-2 backdrop-blur">
        <div className="flex items-center gap-2">
          <Gamepad2 className="h-5 w-5 text-cyan-400" />
          <div>
            <div className="text-sm font-semibold">Company Brain</div>
            <div className="text-xs text-slate-400">{roomLabel}</div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {PANELS.map((panel) => {
            const Icon = panel.icon
            const activeCls = active === panel.id ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:bg-slate-800/70 hover:text-slate-200'
            return (
              <button
                key={panel.id}
                onClick={() => setActive(panel.id)}
                className={`flex items-center gap-2 rounded-md px-2 py-1 text-xs transition ${activeCls}`}
              >
                <Icon className="h-4 w-4" />
                {panel.label}
              </button>
            )
          })}
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="ml-2 rounded-md p-1 text-slate-400 hover:bg-slate-800/70 hover:text-slate-200"
          >
            {sidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
          </button>
        </div>
      </div>

      <GameCanvas context={context} onContextChange={handleContextChange} focusTrigger={focusTrigger} />
      {sidebarOpen && (
        <aside className="absolute right-0 top-0 z-20 mt-12 h-[calc(100vh-48px)] w-[380px] overflow-hidden border-l border-slate-800 bg-slate-950/85 backdrop-blur">
          <PanelView active={active} context={context} onContextUpdate={handleContextChange} onFocusEntity={handleFocusEntity} />
        </aside>
      )}
      <div className="absolute bottom-4 left-4 z-20 max-w-md rounded-lg border border-slate-800 bg-slate-950/80 p-3 text-xs text-slate-300 backdrop-blur">
        <WorldInfo context={context} />
      </div>
    </div>
  )
}
