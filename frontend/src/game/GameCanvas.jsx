import { useEffect, useRef } from 'react'
import Phaser from 'phaser'
import OfficeScene from './scenes/OfficeScene.js'

export default function GameCanvas({ onRoomChange, onInteract }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current) return

    const game = new Phaser.Game({
      type: Phaser.AUTO,
      parent: ref.current,
      width: ref.current.clientWidth,
      height: ref.current.clientHeight,
      backgroundColor: '#080c18',
      scale: { mode: Phaser.Scale.RESIZE, autoCenter: Phaser.Scale.CENTER_BOTH },
      physics: { default: 'arcade', arcade: { gravity: { y: 0 }, debug: false } },
      scene: OfficeScene,
    })

    const onReady = () => {
      const scene = game.scene.getScene('OfficeScene')
      if (scene) {
        scene.events.on('room:enter', onRoomChange)
        scene.events.on('interact', onInteract)
      }
    }
    game.events.once(Phaser.Core.Events.READY, onReady)

    return () => {
      game.destroy(true)
    }
  }, [onRoomChange, onInteract])

  return <div ref={ref} className="absolute inset-0 h-full w-full" />
}
