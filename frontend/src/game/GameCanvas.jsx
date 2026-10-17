import { useEffect, useRef } from 'react'

export default function GameCanvas({ context, onContextChange, focusTrigger }) {
  const containerRef = useRef(null)

  useEffect(() => {
    // Simple placeholder canvas - in full implementation Phaser 3 would render here
    const container = containerRef.current
    if (!container) return

    container.innerHTML = ''
    const canvas = document.createElement('canvas')
    canvas.style.width = '100%'
    canvas.style.height = '100%'
    container.appendChild(canvas)

    const ctx = canvas.getContext('2d')
    const resize = () => {
      canvas.width = container.clientWidth
      canvas.height = container.clientHeight
    }
    resize()
    window.addEventListener('resize', resize)

    let animationId
    const draw = () => {
      ctx.fillStyle = '#020617'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      
      // Draw grid
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)'
      ctx.lineWidth = 1
      for (let x = 0; x < canvas.width; x += 40) {
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, canvas.height)
        ctx.stroke()
      }
      for (let y = 0; y < canvas.height; y += 40) {
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(canvas.width, y)
        ctx.stroke()
      }
      
      // Draw title
      ctx.fillStyle = '#38bdf8'
      ctx.font = '24px Inter, sans-serif'
      ctx.fillText('Company Brain - 2D World', 20, 40)
      ctx.fillStyle = '#94a3b8'
      ctx.font = '14px Inter, sans-serif'
      ctx.fillText('Backend API running at http://localhost:8000', 20, 70)
      ctx.fillStyle = '#64748b'
      ctx.font = '12px Inter, sans-serif'
      ctx.fillText('Room: ' + (context.room || 'room_reception'), 20, 95)
      
      animationId = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      window.removeEventListener('resize', resize)
      if (animationId) cancelAnimationFrame(animationId)
    }
  }, [context.room])

  return <div ref={containerRef} id="game-container" className="absolute inset-0" />
}
