import Phaser from 'phaser'

const TILE_SIZE = 32
const ROOM_COLORS = {
  lobby: 0x1f2937,
  reception: 0x1f2937,
  hallway: 0x111827,
  office: 0x0f172a,
  meeting: 0x0f172a,
  breakroom: 0x0f172a,
  kitchen: 0x0f172a,
  it: 0x0f172a,
  hr: 0x0f172a,
  finance: 0x0f172a,
  storage: 0x0f172a,
  exit: 0x064e3b
}

export default class OfficeScene extends Phaser.Scene {
  constructor() {
    super('OfficeScene')
    this.player = null
    this.cursors = null
    this.walls = null
    this.doors = null
    this.interactables = null
    this.interactText = null
    this.nearby = null
    this.speed = 180
    this.roomData = null
    this.officeData = null
  }

  init(data) {
    this.officeData = data.officeData || null
    this.roomData = data.roomData || null
  }

  create() {
    this.cameras.main.setBackgroundColor('#020617')

    this.walls = this.physics.add.staticGroup()
    this.doors = this.physics.add.staticGroup()
    this.interactables = this.physics.add.group({ allowGravity: false, immovable: true })

    this.buildOffice()

    this.player = this.add.rectangle(200, 200, 16, 16, 0x38bdf8)
    this.physics.add.existing(this.player)
    this.player.body.setCollideWorldBounds(true)

    this.physics.add.collider(this.player, this.walls)
    this.physics.add.overlap(this.player, this.doors, this.handleDoorOverlap, null, this)
    this.physics.add.overlap(this.player, this.interactables, this.handleInteractOverlap, null, this)

    this.cursors = this.input.keyboard.createCursorKeys()
    this.cameras.main.startFollow(this.player, true, 0.08, 0.08)

    this.interactText = this.add.text(10, 10, '', {
      fontSize: '12px',
      fill: '#e2e8f0',
      backgroundColor: 'rgba(15, 23, 42, 0.8)',
      padding: { x: 8, y: 4 }
    }).setScrollFactor(0).setDepth(100).setVisible(false)

    this.events.emit('room:enter', { room: this.roomData?.id || 'lobby' })
  }

  buildOffice() {
    if (!this.roomData) return

    const { layout = [], doors = [], interactables = [], spawn = { x: 200, y: 200 } } = this.roomData
    if (this.player) {
      this.player.x = spawn.x
      this.player.y = spawn.y
    }

    layout.forEach((rect) => {
      const color = ROOM_COLORS[rect.type] || 0x334155
      const wall = this.add.rectangle(rect.x + rect.w / 2, rect.y + rect.h / 2, rect.w, rect.h, color, 0.3)
      this.physics.add.existing(wall, true)
      this.walls.add(wall)
    })

    doors.forEach((door) => {
      const d = this.add.rectangle(door.x + door.w / 2, door.y + door.h / 2, door.w, door.h, 0x10b981, 0.6)
      d.setData('target', door.target)
      d.setData('targetRoom', door.targetRoom || door.target)
      this.physics.add.existing(d, true)
      this.doors.add(d)
    })

    interactables.forEach((obj) => {
      const color = obj.type === 'npc' ? 0xf59e0b : obj.type === 'item' ? 0x22d3ee : obj.type === 'document' ? 0xa78bfa : 0x64748b
      const sprite = this.add.rectangle(obj.x + obj.w / 2, obj.y + obj.h / 2, obj.w, obj.h, color, 0.9)
      sprite.setData('id', obj.id)
      sprite.setData('name', obj.name)
      sprite.setData('type', obj.type)
      sprite.setData('desc', obj.desc || '')
      this.physics.add.existing(sprite, true)
      this.interactables.add(sprite)
    })
  }

  handleDoorOverlap(player, door) {
    const target = door.getData('targetRoom') || door.getData('target')
    if (target && this.officeData) {
      this.scene.start('OfficeScene', { officeData: this.officeData, roomData: this.officeData.rooms.find((r) => r.id === target) })
    }
  }

  handleInteractOverlap(player, obj) {
    this.nearby = obj
    const name = obj.getData('name') || obj.getData('id')
    const type = obj.getData('type')
    this.interactText.setText(`[E] Interact: ${name} (${type})`)
    this.interactText.setVisible(true)
  }

  update() {
    if (!this.player) return
    this.player.body.setVelocity(0)

    if (this.cursors.left.isDown || this.input.keyboard.addKey('A').isDown) {
      this.player.body.setVelocityX(-this.speed)
    } else if (this.cursors.right.isDown || this.input.keyboard.addKey('D').isDown) {
      this.player.body.setVelocityX(this.speed)
    }
    if (this.cursors.up.isDown || this.input.keyboard.addKey('W').isDown) {
      this.player.body.setVelocityY(-this.speed)
    } else if (this.cursors.down.isDown || this.input.keyboard.addKey('S').isDown) {
      this.player.body.setVelocityY(this.speed)
    }

    if (this.interactText) {
      const distance = this.nearby ? Phaser.Math.Distance.Between(this.player.x, this.player.y, this.nearby.x, this.nearby.y) : Infinity
      if (!this.nearby || distance > 40) {
        this.nearby = null
        this.interactText.setVisible(false)
      }
    }

    if (this.nearby && Phaser.Input.Keyboard.JustDown(this.input.keyboard.addKey('E'))) {
      this.events.emit('interact', { obj: this.nearby.data.values })
    }
  }
}
