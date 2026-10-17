import { useEffect, useRef } from 'react'
import Phaser from 'phaser'
import OfficeScene from './scenes/OfficeScene.js'
import { officeData } from './officeData.js'

export default function GameCanvas({ context, onContextChange, focusTrigger }) {
  const containerRef = useRef(null)
  const gameRef = useRef(null)
  const sceneRef = useRef(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.innerHTML = ''

    const config = {
      type: Phaser.AUTO,
      width: window.innerWidth,
      height: window.innerHeight,
      parent: container,
      backgroundColor: '#0b1020',
      physics: {
        default: 'arcade',
        arcade: {
          gravity: { y: 0 },
          debug: false
        }
      },
      scene: OfficeScene,
      scale: {
        mode: Phaser.Scale.RESIZE,
        autoCenter: Phaser.Scale.CENTER_BOTH
      }
    }

    const game = new Phaser.Game(config)
    gameRef.current = game

    setTimeout(() => {
      const scene = game.scene.getScene('OfficeScene')
      sceneRef.current = scene
      if (scene) {
        if (officeData && officeData.rooms && officeData.rooms.length > 0) {
          scene.start('OfficeScene', { officeData, roomData: officeData.rooms[0] })
        }
        scene.events.on('room:enter', (data) => {
          if (data?.room && onContextChange) {
            onContextChange({ room: data.room })
          }
        })
        scene.events.on('interact', (data) => {
          if (data?.obj && onContextChange) {
            onContextChange({ lastInteraction: data.obj })
          }
        })
      }
    }, 0)

    return () => {
      if (gameRef.current) {
        gameRef.current.destroy(true)
        gameRef.current = null
      }
    }
  }, [onContextChange])

  return <div ref={containerRef} id="game-container" className="absolute inset-0 h-full w-full" />
}
