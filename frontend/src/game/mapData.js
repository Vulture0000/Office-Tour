import layout from '../../../data/office_layout.json'

const hex = (value, fallback = 0x64748b) =>
  typeof value === 'string' && value.startsWith('#') ? parseInt(value.slice(1), 16) : (value ?? fallback)

export const MAP_W = layout.map.width
export const MAP_H = layout.map.height

export const rooms = layout.rooms.map((room) => ({
  ...room,
  color: hex(room.color),
  objects: (room.objects || []).map((obj) => ({ ...obj, color: hex(obj.color) })),
}))

export const doors = layout.doors

export const allObjects = rooms.flatMap((r) => r.objects.map((o) => ({ ...o, roomId: r.id })))

export const spawn = layout.map.spawn
