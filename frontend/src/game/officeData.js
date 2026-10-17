export const officeData = {
  rooms: [
    {
      id: 'lobby',
      name: 'Lobby',
      layout: [
        { x: 100, y: 100, w: 400, h: 20, type: 'wall' },
        { x: 100, y: 100, w: 20, h: 200, type: 'wall' },
        { x: 480, y: 100, w: 20, h: 200, type: 'wall' },
        { x: 100, y: 280, w: 180, h: 20, type: 'wall' },
        { x: 320, y: 280, w: 180, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 280, y: 280, w: 40, h: 20, target: 'reception', targetRoom: 'reception' },
        { x: 480, y: 180, w: 20, h: 40, target: 'hallway1', targetRoom: 'hallway1' }
      ],
      interactables: [
        { id: 'receptionist', name: 'Receptionist', type: 'npc', x: 150, y: 130, w: 16, h: 16, desc: 'Greets visitors and answers questions' },
        { id: 'badge', name: 'Visitor Badge', type: 'item', x: 350, y: 150, w: 12, h: 12, desc: 'Access badge for office areas' }
      ],
      spawn: { x: 300, y: 200 }
    },
    {
      id: 'reception',
      name: 'Reception Area',
      layout: [
        { x: 100, y: 100, w: 400, h: 20, type: 'wall' },
        { x: 100, y: 100, w: 20, h: 200, type: 'wall' },
        { x: 480, y: 100, w: 20, h: 200, type: 'wall' },
        { x: 100, y: 280, w: 180, h: 20, type: 'wall' },
        { x: 320, y: 280, w: 180, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 280, y: 100, w: 40, h: 20, target: 'lobby', targetRoom: 'lobby' },
        { x: 280, y: 280, w: 40, h: 20, target: 'hallway1', targetRoom: 'hallway1' }
      ],
      interactables: [
        { id: 'frontdesk', name: 'Front Desk', type: 'object', x: 250, y: 130, w: 100, h: 20, desc: 'Has office maps and forms' }
      ],
      spawn: { x: 300, y: 150 }
    },
    {
      id: 'hallway1',
      name: 'Main Hallway',
      layout: [
        { x: 60, y: 140, w: 480, h: 20, type: 'wall' },
        { x: 60, y: 240, w: 480, h: 20, type: 'wall' },
        { x: 60, y: 140, w: 20, h: 120, type: 'wall' },
        { x: 520, y: 140, w: 20, h: 120, type: 'wall' }
      ],
      doors: [
        { x: 520, y: 180, w: 20, h: 40, target: 'it_room', targetRoom: 'it_room' },
        { x: 60, y: 180, w: 20, h: 40, target: 'lobby', targetRoom: 'lobby' },
        { x: 280, y: 140, w: 40, h: 20, target: 'meeting_room', targetRoom: 'meeting_room' },
        { x: 280, y: 240, w: 40, h: 20, target: 'office_area', targetRoom: 'office_area' }
      ],
      interactables: [
        { id: 'directory', name: 'Office Directory', type: 'document', x: 120, y: 190, w: 16, h: 16, desc: 'Shows who sits where and teams' }
      ],
      spawn: { x: 300, y: 190 }
    },
    {
      id: 'meeting_room',
      name: 'Meeting Room',
      layout: [
        { x: 100, y: 100, w: 400, h: 20, type: 'wall' },
        { x: 100, y: 100, w: 20, h: 200, type: 'wall' },
        { x: 480, y: 100, w: 20, h: 200, type: 'wall' },
        { x: 100, y: 280, w: 400, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 280, y: 280, w: 40, h: 20, target: 'hallway1', targetRoom: 'hallway1' }
      ],
      interactables: [
        { id: 'whiteboard', name: 'Whiteboard', type: 'object', x: 150, y: 150, w: 80, h: 40, desc: 'Notes about projects and deadlines' },
        { id: 'bob', name: 'Bob', type: 'npc', x: 380, y: 200, w: 16, h: 16, desc: 'Tech lead - knows about Atlas migration' }
      ],
      spawn: { x: 300, y: 240 }
    },
    {
      id: 'it_room',
      name: 'IT Room',
      layout: [
        { x: 100, y: 80, w: 400, h: 20, type: 'wall' },
        { x: 100, y: 80, w: 20, h: 220, type: 'wall' },
        { x: 480, y: 80, w: 20, h: 220, type: 'wall' },
        { x: 100, y: 280, w: 180, h: 20, type: 'wall' },
        { x: 320, y: 280, w: 180, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 280, y: 280, w: 40, h: 20, target: 'hallway1', targetRoom: 'hallway1' }
      ],
      interactables: [
        { id: 'alice', name: 'Alice', type: 'npc', x: 150, y: 140, w: 16, h: 16, desc: 'DevOps engineer - knows systems and databases' },
        { id: 'server_doc', name: 'Server Notes', type: 'document', x: 400, y: 180, w: 16, h: 16, desc: 'PostgreSQL setup and migration notes' }
      ],
      spawn: { x: 300, y: 240 }
    },
    {
      id: 'office_area',
      name: 'Office Area',
      layout: [
        { x: 80, y: 80, w: 440, h: 20, type: 'wall' },
        { x: 80, y: 80, w: 20, h: 240, type: 'wall' },
        { x: 500, y: 80, w: 20, h: 240, type: 'wall' },
        { x: 80, y: 300, w: 200, h: 20, type: 'wall' },
        { x: 320, y: 300, w: 200, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 280, y: 80, w: 40, h: 20, target: 'hallway1', targetRoom: 'hallway1' },
        { x: 280, y: 300, w: 40, h: 20, target: 'kitchen', targetRoom: 'kitchen' }
      ],
      interactables: [
        { id: 'carol', name: 'Carol', type: 'npc', x: 140, y: 140, w: 16, h: 16, desc: 'Engineer - worked on Atlas project' },
        { id: 'dave', name: 'Dave', type: 'npc', x: 440, y: 200, w: 16, h: 16, desc: 'PM - knows decisions and timelines' },
        { id: 'atlas_doc', name: 'Atlas Design Doc', type: 'document', x: 320, y: 140, w: 16, h: 16, desc: 'Atlas migration design document' }
      ],
      spawn: { x: 300, y: 200 }
    },
    {
      id: 'kitchen',
      name: 'Kitchen',
      layout: [
        { x: 100, y: 100, w: 400, h: 20, type: 'wall' },
        { x: 100, y: 100, w: 20, h: 180, type: 'wall' },
        { x: 480, y: 100, w: 20, h: 180, type: 'wall' },
        { x: 100, y: 260, w: 400, h: 20, type: 'wall' }
      ],
      doors: [
        { x: 280, y: 100, w: 40, h: 20, target: 'office_area', targetRoom: 'office_area' }
      ],
      interactables: [
        { id: 'fridge_note', name: 'Sticky Note', type: 'item', x: 200, y: 150, w: 12, h: 12, desc: 'Reminder about PostgreSQL ADR discussion' }
      ],
      spawn: { x: 300, y: 220 }
    }
  ]
}
