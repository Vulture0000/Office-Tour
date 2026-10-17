import { useEffect, useState } from 'react'
import { api } from '../services/apiClient.js'

export default function PeoplePanel() {
  const [people, setPeople] = useState([])

  useEffect(() => {
    api.get('/people').then((res) => setPeople(res.data)).catch(() => {})
  }, [])

  return (
    <div className="h-full overflow-y-auto panel-scroll p-3">
      <div className="mb-3 text-sm font-semibold">People</div>
      <div className="space-y-2">
        {people.map((p) => (
          <div key={p.id} className="rounded-md bg-slate-800/70 px-2 py-2 text-xs">
            <div className="font-medium">{p.name}</div>
            <div className="text-slate-400">{p.role} • {p.team}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
