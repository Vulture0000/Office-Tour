import Phaser from 'phaser'
import { rooms, doors, allObjects, spawn, MAP_W, MAP_H } from '../mapData.js'

const ISO_W = 1.0
const ISO_H = 0.5
const WALL_H = 74
const PAD = 260

function shade(color, factor) {
  const r = Math.min(255, Math.floor(((color >> 16) & 0xff) * factor))
  const g = Math.min(255, Math.floor(((color >> 8) & 0xff) * factor))
  const b = Math.min(255, Math.floor((color & 0xff) * factor))
  return (r << 16) | (g << 8) | b
}

export default class OfficeScene extends Phaser.Scene {
  constructor() {
    super('OfficeScene')
  }

  create() {
    this.cameras.main.setBackgroundColor('#0a0f1a')

    const corners = [
      { x: 0, y: 0 },
      { x: MAP_W, y: 0 },
      { x: MAP_W, y: MAP_H },
      { x: 0, y: MAP_H },
    ].map((p) => this.rawIso(p.x, p.y))

    const minX = Math.min(...corners.map((c) => c.x))
    const maxX = Math.max(...corners.map((c) => c.x))
    const minY = Math.min(...corners.map((c) => c.y))
    const maxY = Math.max(...corners.map((c) => c.y))
    this.OX = PAD - minX
    this.OY = PAD - minY

    const g = this.add.graphics().setDepth(0)
    this.drawGround(g)

    // Rooms are painted back-to-front so nearer buildings overlap farther ones.
    const ordered = [...rooms].sort((a, b) => a.x + a.y + a.w + a.h - (b.x + b.y + b.w + b.h))
    for (const room of ordered) {
      this.drawBuilding(g, room)
      const objs = [...room.objects].sort((a, b) => a.x + a.y - (b.x + b.y))
      for (const obj of objs) this.drawObject(g, obj)
    }

    for (const d of doors) this.drawDoor(g, d)

    // Room name labels, floating over each floor.
    for (const room of rooms) {
      const c = this.w2s(room.x + room.w / 2, room.y + room.h / 2)
      const label = this.add.text(c.x, c.y, room.name.toUpperCase(), {
        fontSize: '12px',
        fontFamily: 'Inter, sans-serif',
        color: '#e2e8f0',
      }).setOrigin(0.5).setDepth(100 + c.y)
      label.setAlpha(0.75)
    }

    this.objSprites = []
    for (const obj of allObjects) {
      const c = this.w2s(obj.x, obj.y)
      const label = this.add.text(c.x, c.y - (obj.r || 12) - 34, obj.name, {
        fontSize: '10px',
        fontFamily: 'Inter, sans-serif',
        color: '#cbd5e1',
        backgroundColor: 'rgba(2,6,23,0.6)',
        padding: { x: 4, y: 1 },
      }).setOrigin(0.5, 1).setDepth(100 + c.y)
      this.objSprites.push({ ...obj, label })
    }

    this.playerG = this.createPlayer()
    this.player = { x: spawn.x, y: spawn.y }

    this.promptText = this.add.text(0, 0, '', {
      fontSize: '12px', fontFamily: 'Inter, sans-serif', color: '#e2e8f0',
      backgroundColor: 'rgba(15,23,42,0.92)', padding: { x: 10, y: 5 },
    }).setOrigin(0.5, 1).setDepth(6000).setVisible(false)

    this.hud = this.add.text(10, 10, '', {
      fontSize: '13px', fontFamily: 'Inter, sans-serif', color: '#94a3b8',
      backgroundColor: 'rgba(15,23,42,0.8)', padding: { x: 10, y: 5 },
    }).setScrollFactor(0).setDepth(7000)

    this.minimap = this.add.graphics().setScrollFactor(0).setDepth(7000)
    this.drawMinimap()

    const boundsW = maxX - minX + PAD * 2
    const boundsH = maxY - minY + PAD * 2 + WALL_H
    this.cameras.main.setBounds(0, 0, boundsW, boundsH)
    this.cameras.main.startFollow(this.playerG, true, 0.12, 0.12)
    this.cameras.main.setZoom(0.9)

    if (this.input.keyboard) this.input.keyboard.enabled = false

    this.currentRoom = null
    this.nearby = null
    this.speed = 240
    this.keysDown = new Set()
    this.interactLatch = false

    this.isTyping = () => {
      const a = document.activeElement
      return !!a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable)
    }

    this._onKeyDown = (e) => {
      if (this.isTyping()) return
      this.keysDown.add(e.code)
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
        e.preventDefault()
      }
    }
    this._onKeyUp = (e) => {
      this.keysDown.delete(e.code)
    }
    this._onBlur = () => this.keysDown.clear()

    window.addEventListener('keydown', this._onKeyDown)
    window.addEventListener('keyup', this._onKeyUp)
    window.addEventListener('blur', this._onBlur)

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
      window.removeEventListener('keydown', this._onKeyDown)
      window.removeEventListener('keyup', this._onKeyUp)
      window.removeEventListener('blur', this._onBlur)
    })
  }

  rawIso(x, y) {
    return { x: (x - y) * ISO_W, y: (x + y) * ISO_H }
  }

  w2s(x, y) {
    const p = this.rawIso(x, y)
    return { x: p.x + this.OX, y: p.y + this.OY }
  }

  drawGround(g) {
    const c0 = this.w2s(0, 0)
    const c1 = this.w2s(MAP_W, 0)
    const c2 = this.w2s(MAP_W, MAP_H)
    const c3 = this.w2s(0, MAP_H)
    g.fillStyle(0x0d1524, 1)
    g.fillPoints([c0, c1, c2, c3], true)

    g.lineStyle(1, 0x1e293b, 0.6)
    const step = 160
    for (let x = 0; x <= MAP_W; x += step) {
      const a = this.w2s(x, 0)
      const b = this.w2s(x, MAP_H)
      g.lineBetween(a.x, a.y, b.x, b.y)
    }
    for (let y = 0; y <= MAP_H; y += step) {
      const a = this.w2s(0, y)
      const b = this.w2s(MAP_W, y)
      g.lineBetween(a.x, a.y, b.x, b.y)
    }
  }

  drawBuilding(g, room) {
    const { x, y, w, h, color } = room
    const c0 = this.w2s(x, y)
    const c1 = this.w2s(x + w, y)
    const c2 = this.w2s(x + w, y + h)
    const c3 = this.w2s(x, y + h)
    const H = WALL_H

    const up = (p, d) => ({ x: p.x, y: p.y - d })

    // Right (north-east) wall.
    g.fillStyle(shade(color, 0.72), 1)
    g.fillPoints([c0, c1, up(c1, H), up(c0, H)], true)
    // Left (north-west) wall.
    g.fillStyle(shade(color, 0.5), 1)
    g.fillPoints([c0, c3, up(c3, H), up(c0, H)], true)
    // Floor.
    g.fillStyle(color, 1)
    g.fillPoints([c0, c1, c2, c3], true)
    // Silhouette + top edge highlights.
    g.lineStyle(2, shade(color, 1.5), 0.85)
    g.lineBetween(up(c0, H).x, up(c0, H).y, up(c1, H).x, up(c1, H).y)
    g.lineBetween(up(c0, H).x, up(c0, H).y, up(c3, H).x, up(c3, H).y)
    g.strokePoints([up(c1, H), c1, c2, c3, up(c3, H)], false)
    g.lineStyle(1.5, 0x0b1220, 0.5)
    g.strokePoints([c0, c1, c2, c3], true)
  }

  drawObject(g, obj) {
    const half = obj.r || 12
    const height = obj.type === 'npc' ? 40 : obj.type === 'furniture' ? 28 : 20
    const color = obj.color || 0x64748b
    const c0 = this.w2s(obj.x - half, obj.y - half)
    const c1 = this.w2s(obj.x + half, obj.y - half)
    const c2 = this.w2s(obj.x + half, obj.y + half)
    const c3 = this.w2s(obj.x - half, obj.y + half)
    const up = (p, d) => ({ x: p.x, y: p.y - d })

    // Contact shadow.
    g.fillStyle(0x000000, 0.28)
    g.fillPoints([c0, c1, c2, c3], true)

    g.fillStyle(shade(color, 0.7), 1)
    g.fillPoints([c0, c1, up(c1, height), up(c0, height)], true)
    g.fillStyle(shade(color, 0.52), 1)
    g.fillPoints([c0, c3, up(c3, height), up(c0, height)], true)
    g.fillStyle(color, 1)
    g.fillPoints([up(c0, height), up(c1, height), up(c2, height), up(c3, height)], true)

    if (obj.type === 'npc') {
      const head = this.w2s(obj.x, obj.y)
      const hx = head.x
      const hy = head.y - height - 10
      g.fillStyle(0x0f172a, 0.35)
      g.fillEllipse(hx, hy - 2, 26, 26)
      g.fillStyle(shade(color, 1.25), 1)
      g.fillEllipse(hx, hy, 22, 22)
    } else {
      g.lineStyle(1, 0x0b1220, 0.4)
      g.strokePoints([up(c0, height), up(c1, height), up(c2, height), up(c3, height)], true)
    }
  }

  drawDoor(g, door) {
    const c0 = this.w2s(door.x, door.y)
    const c1 = this.w2s(door.x + door.w, door.y)
    const c2 = this.w2s(door.x + door.w, door.y + door.h)
    const c3 = this.w2s(door.x, door.y + door.h)
    g.fillStyle(0x22c55e, 0.35)
    g.fillPoints([c0, c1, c2, c3], true)
  }

  createPlayer() {
    const container = this.add.container(0, 0).setDepth(5000)
    const shadow = this.add.ellipse(0, 0, 26, 12, 0x000000, 0.35)
    const body = this.add.ellipse(0, -16, 18, 30, 0x38bdf8)
    body.setStrokeStyle(2, 0xe0f2fe, 0.9)
    const head = this.add.circle(0, -38, 9, 0xe0f2fe)
    container.add([shadow, body, head])
    return container
  }

  drawMinimap() {
    const mw = 180
    const mh = Math.round(mw * MAP_H / MAP_W)
    const ox = 10
    const oy = 40
    const sx = mw / MAP_W
    const sy = mh / MAP_H

    this.minimap.clear()
    this.minimap.fillStyle(0x0f172a, 0.85)
    this.minimap.fillRoundedRect(ox - 4, oy - 4, mw + 8, mh + 8, 4)

    for (const r of rooms) {
      this.minimap.fillStyle(r.color, 0.8)
      this.minimap.fillRect(ox + r.x * sx, oy + r.y * sy, r.w * sx, r.h * sy)
    }
    this.minimap._ox = ox
    this.minimap._oy = oy
    this.minimap._sx = sx
    this.minimap._sy = sy
  }

  update() {
    if (!this.player) return

    const down = (code) => this.keysDown.has(code)
    const typing = this.isTyping()

    // Screen-aligned movement mapped onto the isometric plane.
    let u = 0, d = 0, l = 0, r = 0
    if (!typing) {
      if (down('ArrowUp') || down('KeyW')) u = 1
      else if (down('ArrowDown') || down('KeyS')) d = 1
      if (down('ArrowLeft') || down('KeyA')) l = 1
      else if (down('ArrowRight') || down('KeyD')) r = 1
    }
    let vx = -u + d - l + r
    let vy = -u + d + l - r
    const len = Math.hypot(vx, vy)
    if (len > 0) { vx /= len; vy /= len }

    this.player.x = Phaser.Math.Clamp(this.player.x + vx * this.speed * this.game.loop.delta / 1000, 20, MAP_W - 20)
    this.player.y = Phaser.Math.Clamp(this.player.y + vy * this.speed * this.game.loop.delta / 1000, 20, MAP_H - 20)

    const px = this.player.x
    const py = this.player.y
    const screen = this.w2s(px, py)
    this.playerG.setPosition(screen.x, screen.y)

    let room = null
    for (const r2 of rooms) {
      if (px >= r2.x && px <= r2.x + r2.w && py >= r2.y && py <= r2.y + r2.h) {
        room = r2
        break
      }
    }
    if (room && room.id !== this.currentRoom) {
      this.currentRoom = room.id
      this.events.emit('room:enter', { room: room.id, name: room.name, desc: room.desc })
    }
    this.hud.setText(`Room: ${room ? room.name : '—'}`)

    let nearest = null
    let minD = 70
    for (const o of this.objSprites) {
      const dd = Phaser.Math.Distance.Between(px, py, o.x, o.y)
      if (dd < minD) { minD = dd; nearest = o }
    }

    if (nearest) {
      const ns = this.w2s(nearest.x, nearest.y)
      this.promptText.setPosition(ns.x, ns.y - (nearest.r || 12) - 46)
      this.promptText.setText(`Press E — ${nearest.name}`)
      this.promptText.setVisible(true)
      const eDown = down('KeyE')
      if (eDown && !this.interactLatch && !typing) {
        this.interactLatch = true
        this.events.emit('interact', { id: nearest.id, name: nearest.name, type: nearest.type, info: nearest.info, roomId: nearest.roomId })
      }
    } else {
      this.promptText.setVisible(false)
    }
    if (!down('KeyE')) this.interactLatch = false

    if (this.minimap._sx) {
      if (!this.minimapDot) {
        this.minimapDot = this.add.circle(0, 0, 3, 0x38bdf8).setScrollFactor(0).setDepth(7001)
      }
      this.minimapDot.setPosition(
        this.minimap._ox + px * this.minimap._sx,
        this.minimap._oy + py * this.minimap._sy
      )
    }
  }
}
