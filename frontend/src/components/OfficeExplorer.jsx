import { useEffect, useState } from 'react'
import { api } from '../services/apiClient.js'

export default function OfficeExplorer({ onFocusEntity }) {
  const [rooms, setRooms] = useState([])
  const [selectedRoom, setSelectedRoom] = useState('lobby')
  const [objects, setObjects] = useState([])
  const [selected, setSelected] = useState(null)
  const [connections, setConnections] = useState([])

  useEffect(() => {
    api.get('/office/rooms').then((res) => setRooms(res.data.rooms || [])).catch(() => {})
  }, [])

  useEffect(() => {
    api.get(`/office/room/${selectedRoom}/objects`).then((res) => setObjects(res.data.objects || [])).catch(() => {})
    setSelected(null)
    setConnections([])
  }, [selectedRoom])

  const handleSelect = (obj) => {
    setSelected(obj)
    api.get(`/office/connections/${obj.id}`).then((res) => setConnections(res.data.connections || [])).catch(() => {})
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-800 px-4 py-2">
        <div className="text-sm font-semibold">Office Explorer</div>
        <div className="text-xs text-slate-400">Find things using graph data</div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <div>
          <label className="text-xs text-slate-400">Room</label>
          <select
            className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm"
            value={selectedRoom}
            onChange={(e) => setSelectedRoom(e.target.value)}
          >
            {rooms.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </div>
        <div>
          <div className="text-xs text-slate-400 mb-1">Objects in room</div>
          <div className="space-y-1">
            {objects.map((obj) => (
              <button
                key={obj.id}
                className={`w-full text-left rounded px-2 py-1 text-sm ${selected?.id === obj.id ? 'bg-cyan-500/20 text-cyan-300' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'}`}
                onClick={() => handleSelect(obj)}
              >
                {obj.name} <span className="text-xs text-slate-500">({obj.label})</span>
              </button>
            ))}
            {objects.length === 0 && <div className="text-xs text-slate-500">Nothing here</div>}
          </div>
        </div>
        {selected && (
          <div>
            <div className="text-xs text-slate-400 mb-1">Connected to</div>
            <div className="space-y-1">
              {connections.map((c, i) => (
                <div key={i} className="rounded bg-slate-900 px-2 py-1 text-xs text-slate-300">
                  <span className="text-cyan-400">{c.rel}</span> → {c.toName} <span className="text-slate-500">({c.toLabel})</span>
                </div>
              ))}
              {connections.length === 0 && <div className="text-xs text-slate-500">No connections</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
