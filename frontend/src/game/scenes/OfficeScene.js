import Phaser from 'phaser'

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
    this.speed = 220
    this.roomData = null
    this.officeData = null
    this.infoText = null
  }

  init(data) {
    this.officeData = data.officeData || null
    this.roomData = data.roomData || null
  }

  create() {
    this.cameras.main.setBackgroundColor('#0b1020')

    this.walls = this.physics.add.staticGroup()
    this.doors = this.physics.add.staticGroup()
    this.interactables = this.physics.add.group({ allowGravity: false, immovable: true })

    this.buildOffice()

    const spawn = this.roomData?.spawn || { x: 400, y: 300 }
    this.player = this.add.circle(spawn.x, spawn.y, 10, 0x38bdf8)
    this.physics.add.existing(this.player)
    if (this.player.body) {
      this.player.body.setCollideWorldBounds(false)
      this.player.body.setCircle(8)
    }

    this.physics.add.collider(this.player, this.walls)
    this.physics.add.overlap(this.player, this.doors, this.handleDoorOverlap, null, this)
    this.physics.add.overlap(this.player, this.interactables, this.handleInteractOverlap, null, this)

    this.cursors = this.input.keyboard.createCursorKeys()
    this.cameras.main.startFollow(this.player, true, 0.15, 0.15)
    this.cameras.main.setZoom(1.5)

    this.interactText = this.add.text(10, 10, '', {
      fontSize: '14px',
      fill: '#e2e8f0',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      padding: { x: 10, y: 6 }
    }).setScrollFactor(0).setDepth(200).setVisible(false)

    this.infoText = this.add.text(10, 45, `Room: ${this.roomData?.name || this.roomData?.id || 'lobby'}`, {
      fontSize: '13px',
      fill: '#94a3b8',
      backgroundColor: 'rgba(15, 23, 42, 0.7)',
      padding: { x: 8, y: 4 }
    }).setScrollFactor(0).setDepth(200)

    this.events.emit('room:enter', { room: this.roomData?.id || 'lobby' })
  }

  buildOffice() {
    if (!this.roomData) return
    const { layout = [], doors = [], interactables = [] } = this.roomData

    layout.forEach((rect) => {
      const wall = this.add.rectangle(rect.x + rect.w / 2, rect.y + rect.h / 2, rect.w, rect.h, 0x1e293b)
      wall.setStrokeStyle(2, 0x475569)
      this.physics.add.existing(wall, true)
      this.walls.add(wall)
    })

    doors.forEach((door) => {
      const d = this.add.rectangle(door.x + door.w / 2, door.y + door.h / 2, door.w, door.h, 0x22c55e)
      d.setAlpha(0.8)
      d.setStrokeStyle(2, 0x86efac)
      d.setData('target', door.target)
      d.setData('targetRoom', door.targetRoom || door.target)
      this.physics.add.existing(d, true)
      this.doors.add(d)
    })

    interactables.forEach((obj) => {
      const color = obj.type === 'npc' ? 0xf59e0b : obj.type === 'item' ? 0x06b6d4 : obj.type === 'document' ? 0xa855f7 : 0x64748b
      const sprite = this.add.circle(obj.x + (obj.w || 16) / 2, obj.y + (obj.h || 16) / 2, 12, color)
      sprite.setStrokeStyle(2, 0xfbbf24)
      sprite.setData('id', obj.id)
      sprite.setData('name', obj.name)
      sprite.setData('type', obj.type)
      this.physics.add.existing(sprite, true)
      this.interactables.add(sprite)
      const label = this.add.text(sprite.x - 20, sprite.y + 16, obj.name, {
        fontSize: '10px',
        fill: '#cbd5e1',
        backgroundColor: 'rgba(15,23,42,0.6)',
        padding: { x: 4, y: 2 }
      }).setOrigin(0.5)
    })
  }

  handleDoorOverlap(player, door) {
    const target = door.getData('targetRoom') || door.getData('target')
    if (target && this.officeData) {
      const nextRoom = this.officeData.rooms.find((r) => r.id === target)
      if (nextRoom) {
        this.scene.start('OfficeScene', { officeData: this.officeData, roomData: nextRoom })
      }
    }
  }

  handleInteractOverlap(player, obj) {
    this.nearby = obj
    const name = obj.getData('name') || obj.getData('id')
    const type = obj.getData('type')
    this.interactText.setText(`[E] Interact • ${name} (${type})`)
    this.interactText.setVisible(true)
  }

  update() {
    if (!this.player || !this.player.body) return
    this.player.body.setVelocity(0)

    const keys = this.input.keyboard
    if (this.cursors.left.isDown || keys.addKey('A').isDown) {
      this.player.body.setVelocityX(-this.speed)
    } else if (this.cursors.right.isDown || keys.addKey('D').isDown) {
      this.player.body.setVelocityX(this.speed)
    }
    if (this.cursors.up.isDown || keys.addKey('W').isDown) {
      this.player.body.setVelocityY(-this.speed)
    } else if (this.cursors.down.isDown || keys.addKey('S').isDown) {
      this.player.body.setVelocityY(this.speed)
    }

    if (this.interactText) {
      const distance = this.nearby ? Phaser.Math.Distance.Between(this.player.x, this.player.y, this.nearby.x, this.nearby.y) : Infinity
      if (!this.nearby || distance > 70) {
        this.nearby = null
        this.interactText.setVisible(false)
      }
    }

    if (this.nearby && Phaser.Input.Keyboard.JustDown(keys.addKey('E'))) {
      this.events.emit('interact', { obj: this.nearby.data.values })
    }
  }
}
