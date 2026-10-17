import Phaser from 'phaser'
import { rooms, doors, allObjects, spawn, MAP_W, MAP_H } from '../mapData.js'

export default class OfficeScene extends Phaser.Scene {
  constructor() {
    super('OfficeScene')
  }

  create() {
    this.cameras.main.setBackgroundColor('#080c18')

    const g = this.add.graphics()

    for (const r of rooms) {
      g.fillStyle(r.color, 1)
      g.fillRoundedRect(r.x, r.y, r.w, r.h, 6)
      g.lineStyle(3, 0x475569, 0.9)
      g.strokeRoundedRect(r.x, r.y, r.w, r.h, 6)

      this.add.text(r.x + r.w / 2, r.y + 16, r.name, {
        fontSize: '14px', fontFamily: 'Inter, sans-serif', color: '#94a3b8',
      }).setOrigin(0.5)
    }

    g.fillStyle(0x22c55e, 0.5)
    for (const d of doors) {
      g.fillRect(d.x, d.y, d.w, d.h)
    }

    this.objSprites = []
    for (const obj of allObjects) {
      const s = this.add.circle(obj.x, obj.y, obj.r || 12, obj.color || 0x64748b)
      s.setStrokeStyle(2, 0xffffff, 0.3)
      const label = this.add.text(obj.x, obj.y + (obj.r || 12) + 6, obj.name, {
        fontSize: '10px', fontFamily: 'Inter, sans-serif', color: '#cbd5e1',
        backgroundColor: 'rgba(0,0,0,0.5)', padding: { x: 4, y: 1 },
      }).setOrigin(0.5, 0)
      this.objSprites.push({ ...obj, sprite: s, label })
    }

    this.player = this.add.circle(spawn.x, spawn.y, 10, 0x38bdf8)
    this.player.setStrokeStyle(2, 0xe0f2fe)

    this.promptText = this.add.text(0, 0, '', {
      fontSize: '12px', fontFamily: 'Inter, sans-serif', color: '#e2e8f0',
      backgroundColor: 'rgba(15,23,42,0.92)', padding: { x: 10, y: 5 },
    }).setOrigin(0.5, 1).setDepth(500).setVisible(false)

    this.hud = this.add.text(10, 10, '', {
      fontSize: '13px', fontFamily: 'Inter, sans-serif', color: '#94a3b8',
      backgroundColor: 'rgba(15,23,42,0.8)', padding: { x: 10, y: 5 },
    }).setScrollFactor(0).setDepth(500)

    this.minimap = this.add.graphics().setScrollFactor(0).setDepth(500)
    this.drawMinimap()

    this.cameras.main.setBounds(0, 0, MAP_W, MAP_H)
    this.cameras.main.startFollow(this.player, true, 0.12, 0.12)
    this.cameras.main.setZoom(1.3)

    this.keys = this.input.keyboard.addKeys('W,A,S,D,UP,DOWN,LEFT,RIGHT,E')
    this.currentRoom = null
    this.nearby = null
    this.speed = 240

    const isTyping = () => {
      const a = document.activeElement
      return !!a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable)
    }
    this.isTyping = isTyping

    this.input.keyboard.on('keydown', (e) => {
      if (isTyping()) {
        e.stopPropagation()
      }
    })
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
    this.minimap._mw = mw
    this.minimap._mh = mh
  }

  update() {
    if (!this.player || this.isTyping()) return

    const k = this.keys
    let vx = 0, vy = 0
    if (k.LEFT.isDown || k.A.isDown) vx = -1
    else if (k.RIGHT.isDown || k.D.isDown) vx = 1
    if (k.UP.isDown || k.W.isDown) vy = -1
    else if (k.DOWN.isDown || k.S.isDown) vy = 1
    if (vx && vy) { vx *= 0.707; vy *= 0.707 }

    this.player.x = Phaser.Math.Clamp(this.player.x + vx * this.speed * this.game.loop.delta / 1000, 20, MAP_W - 20)
    this.player.y = Phaser.Math.Clamp(this.player.y + vy * this.speed * this.game.loop.delta / 1000, 20, MAP_H - 20)

    const px = this.player.x
    const py = this.player.y

    let room = null
    for (const r of rooms) {
      if (px >= r.x && px <= r.x + r.w && py >= r.y && py <= r.y + r.h) {
        room = r
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
      const d = Phaser.Math.Distance.Between(px, py, o.x, o.y)
      if (d < minD) { minD = d; nearest = o }
    }

    if (nearest) {
      this.promptText.setPosition(nearest.x, nearest.y - (nearest.r || 12) - 8)
      this.promptText.setText(`Press E — ${nearest.name}`)
      this.promptText.setVisible(true)
      if (Phaser.Input.Keyboard.JustDown(k.E)) {
        this.events.emit('interact', { id: nearest.id, name: nearest.name, type: nearest.type, info: nearest.info, roomId: nearest.roomId })
      }
    } else {
      this.promptText.setVisible(false)
    }

    if (this.minimap._sx) {
      this.minimap._dot = this.minimap._dot || this.minimap
      if (!this.minimapDot) {
        this.minimapDot = this.add.circle(0, 0, 3, 0x38bdf8).setScrollFactor(0).setDepth(501)
      }
      this.minimapDot.setPosition(
        this.minimap._ox + px * this.minimap._sx,
        this.minimap._oy + py * this.minimap._sy
      )
    }
  }
}
