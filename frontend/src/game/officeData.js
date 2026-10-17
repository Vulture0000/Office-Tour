export const officeData = {
  rooms: [
    {
      id: 'lobby',
      name: 'Lobby',
      layout: [
        { x: 50, y: 50, w: 500, h: 20, type: 'wall' },
        { x: 50, y: 50, w: 20, h: 250, type: 'wall' },
        { x: 530, y: 50, w: 20, h: 250, type: 'wall' },
        { x: 50, y: 280, w: 220, h: 20, type: 'wall' },
        { x: 330, y: 280, w: 220, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 270, y: 280, w: 60, h: 20, target: 'reception', targetRoom: 'reception' },
        { x: 530, y: 165, w: 20, h: 60, target: 'hallway1', targetRoom: 'hallway1' }
      ],
      interactables: [
        { id: 'receptionist', name: 'Receptionist', type: 'npc', x: 120, y: 120, w: 16, h: 16, desc: 'Greets visitors and answers questions' },
        { id: 'badge', name: 'Visitor Badge', type: 'item', x: 400, y: 150, w: 12, h: 12, desc: 'Access badge for office areas' }
      ],
      spawn: { x: 300, y: 200 }
    },
    {
      id: 'reception',
      name: 'Reception Area',
      layout: [
        { x: 50, y: 50, w: 500, h: 20, type: 'wall' },
        { x: 50, y: 50, w: 20, h: 250, type: 'wall' },
        { x: 530, y: 50, w: 20, h: 250, type: 'wall' },
        { x: 50, y: 280, w: 220, h: 20, type: 'wall' },
        { x: 330, y: 280, w: 220, h: 20, type: 'wall' },
        { x: 50, y: 20, w: 220, h: 20, type: 'wall' },
        { x: 330, y: 20, w: 220, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 270, y: 20, w: 60, h: 20, target: 'lobby', targetRoom: 'lobby' },
        { x: 270, y: 280, w: 60, h: 20, target: 'hallway1', targetRoom: 'hallway1' }
      ],
      interactables: [
        { id: 'frontdesk', name: 'Front Desk', type: 'object', x: 220, y: 90, w: 160, h: 20, desc: 'Has office maps and forms' }
      ],
      spawn: { x: 300, y: 120 }
    },
    {
      id: 'hallway1',
      name: 'Main Hallway',
      layout: [
        { x: 40, y: 120, w: 520, h: 20, type: 'wall' },
        { x: 40, y: 220, w: 520, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 540, y: 150, w: 20, h: 60, target: 'it_room', targetRoom: 'it_room' },
        { x: 40, y: 150, w: 20, h: 60, target: 'reception', targetRoom: 'reception' },
        { x: 260, y: 120, w: 80, h: 20, target: 'meeting_room', targetRoom: 'meeting_room' },
        { x: 260, y: 220, w: 80, h: 20, target: 'office_area', targetRoom: 'office_area' }
      ],
      interactables: [
        { id: 'directory', name: 'Office Directory', type: 'document', x: 120, y: 180, w: 16, h: 16, desc: 'Shows who sits where and teams' }
      ],
      spawn: { x: 300, y: 170 }
    },
    {
      id: 'meeting_room',
      name: 'Meeting Room',
      layout: [
        { x: 80, y: 60, w: 440, h: 20, type: 'wall' },
        { x: 80, y: 60, w: 20, h: 220, type: 'wall' },
        { x: 500, y: 60, w: 20, h: 220, type: 'wall' },
        { x: 80, y: 260, w: 440, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 260, y: 260, w: 80, h: 20, target: 'hallway1', targetRoom: 'hallway1' }
      ],
      interactables: [
        { id: 'whiteboard', name: 'Whiteboard', type: 'object', x: 120, y: 110, w: 120, h: 40, desc: 'Notes about projects and deadlines' },
        { id: 'bob', name: 'Bob', type: 'npc', x: 420, y: 180, w: 16, h: 16, desc: 'Tech lead - knows about Atlas migration' }
      ],
      spawn: { x: 300, y: 230 }
    },
    {
      id: 'it_room',
      name: 'IT Room',
      layout: [
        { x: 80, y: 60, w: 440, h: 20, type: 'wall' },
        { x: 80, y: 60, w: 20, h: 220, type: 'wall' },
        { x: 500, y: 60, w: 20, h: 220, type: 'wall' },
        { x: 80, y: 260, w: 200, h: 20, type: 'wall' },
        { x: 320, y: 260, w: 200, h: 20, type: 'wall' },
        { x: 500, y: 120, w: 20, h: 100, type: 'wall' }
      ],
      doors: [
        { x: 260, y: 260, w: 80, h: 20, target: 'hallway1', targetRoom: 'hallway1' }
      ],
      interactables: [
        { id: 'alice', name: 'Alice', type: 'npc', x: 140, y: 120, w: 16, h: 16, desc: 'DevOps engineer - knows systems and databases' },
        { id: 'server_doc', name: 'Server Notes', type: 'document', x: 420, y: 180, w: 16, h: 16, desc: 'PostgreSQL setup and migration notes' }
      ],
      spawn: { x: 300, y: 230 }
    },
    {
      id: 'office_area',
      name: 'Office Area',
      layout: [
        { x: 60, y: 60, w: 480, h: 20, type: 'wall' },
        { x: 60, y: 60, w: 20, h: 240, type: 'wall' },
        { x: 520, y: 60, w: 20, h: 240, type: 'wall' },
        { x: 60, y: 280, w: 220, h: 20, type: 'wall' },
        { x: 320, y: 280, w: 220, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 260, y: 60, w: 80, h: 20, target: 'hallway1', targetRoom: 'hallway1' },
        { x: 260, y: 280, w: 80, h: 20, target: 'kitchen', targetRoom: 'kitchen' }
      ],
      interactables: [
        { id: 'carol', name: 'Carol', type: 'npc', x: 140, y: 140, w: 16, h: 16, desc: 'Engineer - worked on Atlas project' },
        { id: 'dave', name: 'Dave', type: 'npc', x: 460, y: 200, w: 16, h: 16, desc: 'PM - knows decisions and timelines' },
        { id: 'atlas_doc', name: 'Atlas Design Doc', type: 'document', x: 320, y: 140, w: 16, h: 16, desc: 'Atlas migration design document' }
      ],
      spawn: { x: 300, y: 200 }
    },
    {
      id: 'kitchen',
      name: 'Kitchen',
      layout: [
        { x: 80, y: 80, w: 440, h: 20, type: 'wall' },
        { x: 80, y: 80, w: 20, h: 200, type: 'wall' },
        { x: 500, y: 80, w: 20, h: 200, type: 'wall' },
        { x: 80, y: 260, w: 440, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 260, y: 80, w: 80, h: 20, target: 'office_area', targetRoom: 'office_area' }
      ],
      interactables: [
        { id: 'fridge_note', name: 'Sticky Note', type: 'item', x: 200, y: 150, w: 12, h: 12, desc: 'Reminder about PostgreSQL ADR discussion' }
      ],
      spawn: { x: 300, y: 230 }
    }
  ]
}
