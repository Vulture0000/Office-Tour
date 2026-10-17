import { useEffect, useState } from 'react'
import { api } from '../services/apiClient.js'

export default function GraphPanel({ context }) {
  const [graph, setGraph] = useState({ nodes: [], edges: [] })

  useEffect(() => {
    const id = context.entity_id || 'atlas'
    api.get(`/api/graph/entity/${id}?depth=1`).then((res) => setGraph(res.data)).catch(() => {})
  }, [context.entity_id])

  return (
    <div className="h-full overflow-y-auto panel-scroll p-3">
      <div className="mb-2 text-sm font-semibold">Graph</div>
      <div className="text-xs text-slate-400 mb-3">Nodes: {graph.nodes.length} | Edges: {graph.edges.length}</div>
      <div className="space-y-2">
        {graph.nodes.slice(0, 20).map((n) => (
          <div key={n.id} className="rounded-md bg-slate-800/70 px-2 py-2 text-xs">
            <div className="font-medium">{n.name}</div>
            <div className="text-slate-400">{n.label} • {n.id}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
