import { useEffect, useState } from 'react'
import { api } from '../services/apiClient.js'

export default function Panel() {
  const [data, setData] = useState([])

  useEffect(() => {
    const endpoints = {
      ProjectsPanel: '/api/projects',
      DocumentsPanel: '/api/documents',
      DecisionsPanel: '/api/decisions',
      TicketsPanel: '/api/tickets',
      SystemsPanel: '/api/systems',
      ActionsPanel: '/api/actions',
      SearchPanel: '/api/search?q=postgres',
      WorldInfo: '/api/world'
    }
    const ep = endpoints['SystemsPanel'] || endpoints[name]
    api.get(ep.replace(/^\/api/, '')).then((res) => setData(Array.isArray(res.data) ? res.data : res.data.objects || res.data.results || [])).catch(() => {})
  }, [])

  return (
    <div className="h-full overflow-y-auto panel-scroll p-3">
      <div className="mb-3 text-sm font-semibold">{name.replace('Panel', '')}</div>
      <div className="text-xs text-slate-400">{Array.isArray(data) ? data.length : 0} items</div>
    </div>
  )
}
