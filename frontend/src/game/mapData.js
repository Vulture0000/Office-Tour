export const MAP_W = 1280
export const MAP_H = 860

export const rooms = [
  {
    id: 'reception', name: 'Reception', x: 40, y: 40, w: 300, h: 220,
    color: 0x1e3a5f, desc: 'Front desk where visitors check in.',
    objects: [
      { id: 'receptionist', name: 'Receptionist', type: 'npc', x: 140, y: 150, r: 14, color: 0xf59e0b,
        info: 'Welcome to NovaTech! I manage visitor check-ins and can direct you to anyone in the company.' },
      { id: 'badge', name: 'Visitor Badge', type: 'item', x: 260, y: 170, r: 10, color: 0x06b6d4,
        info: 'A NovaTech visitor badge. Required to enter the server room and restricted areas.' },
    ],
  },
  {
    id: 'lobby', name: 'Lobby', x: 40, y: 320, w: 300, h: 260,
    color: 0x1a2744, desc: 'Open lobby with company displays.',
    objects: [
      { id: 'plant', name: 'Plant', type: 'furniture', x: 300, y: 550, r: 12, color: 0x22c55e,
        info: 'A potted fern. Watered weekly by facilities.' },
    ],
  },
  {
    id: 'corridor', name: 'Main Corridor', x: 380, y: 140, w: 100, h: 460,
    color: 0x111827, desc: 'Central hallway connecting all rooms.',
    objects: [],
  },
  {
    id: 'meeting', name: 'Meeting Room', x: 530, y: 40, w: 340, h: 260,
    color: 0x2d1b4e, desc: 'Where the team holds sprint planning and reviews.',
    objects: [
      { id: 'whiteboard', name: 'Whiteboard', type: 'furniture', x: 600, y: 70, r: 10, color: 0xe2e8f0,
        info: 'Sprint planning: Atlas migration Phase 2. PostgreSQL rollout by Q4. Decision ADR-018 approved.' },
      { id: 'bob', name: 'Bob – Tech Lead', type: 'npc', x: 720, y: 180, r: 14, color: 0xf59e0b,
        info: 'I lead the Atlas migration project. We chose PostgreSQL over MySQL for better JSON support and reliability.' },
    ],
  },
  {
    id: 'it_room', name: 'IT Room', x: 530, y: 360, w: 340, h: 260,
    color: 0x1a2e1a, desc: 'Server room and DevOps workspace.',
    objects: [
      { id: 'alice', name: 'Alice – DevOps', type: 'npc', x: 600, y: 450, r: 14, color: 0xf59e0b,
        info: 'I manage our infrastructure. PostgreSQL primary runs on sys_primary_db. FalkorDB handles our knowledge graph.' },
      { id: 'server_doc', name: 'Server Notes', type: 'item', x: 760, y: 480, r: 10, color: 0xa855f7,
        info: 'DB migration log: PostgreSQL 14 to 16 upgrade completed. Read replicas added for Atlas. See ADR-018.' },
    ],
  },
  {
    id: 'office_area', name: 'Office Area', x: 920, y: 40, w: 320, h: 260,
    color: 0x1e293b, desc: 'Open-plan engineering floor.',
    objects: [
      { id: 'carol', name: 'Carol – Engineer', type: 'npc', x: 1000, y: 140, r: 14, color: 0xf59e0b,
        info: 'I built the Atlas data pipeline. PostgreSQL is our primary datastore. Ask me about the migration.' },
      { id: 'dave', name: 'Dave – PM', type: 'npc', x: 1180, y: 200, r: 14, color: 0xf59e0b,
        info: 'I manage Project Atlas timeline. We shipped Phase 1 in September. Phase 2 is in progress.' },
      { id: 'atlas_doc', name: 'Atlas Design Doc', type: 'item', x: 1100, y: 100, r: 10, color: 0xa855f7,
        info: 'Project Atlas architecture: PostgreSQL primary, FalkorDB for graph queries, Redis cache. See ADR-018.' },
    ],
  },
  {
    id: 'kitchen', name: 'Kitchen', x: 920, y: 360, w: 320, h: 260,
    color: 0x3b2f1a, desc: 'Break room and kitchen.',
    objects: [
      { id: 'fridge_note', name: 'Sticky Note', type: 'item', x: 1000, y: 440, r: 10, color: 0xfbbf24,
        info: 'Reminder: PostgreSQL ADR discussion Thursday 3pm. Bring questions about read replicas.' },
      { id: 'coffee', name: 'Coffee Machine', type: 'furniture', x: 1160, y: 420, r: 12, color: 0x92400e,
        info: 'The only thing keeping engineering alive. Runs on caffeine and PostgreSQL.' },
    ],
  },
  {
    id: 'storage', name: 'Storage', x: 40, y: 640, w: 300, h: 180,
    color: 0x292524, desc: 'Supply closet and storage.',
    objects: [
      { id: 'boxes', name: 'Supply Boxes', type: 'furniture', x: 160, y: 730, r: 14, color: 0x57534e,
        info: 'Boxes of old hardware. Some still running legacy MySQL instances.' },
    ],
  },
  {
    id: 'exit_hall', name: 'Exit Hall', x: 920, y: 680, w: 320, h: 160,
    color: 0x14532d, desc: 'Emergency exit and loading dock.',
    objects: [
      { id: 'exit_door', name: 'Main Exit', type: 'furniture', x: 1080, y: 760, r: 14, color: 0x22c55e,
        info: 'Main office exit. Fire exit to the left.' },
    ],
  },
]

export const doors = [
  { x: 165, y: 255, w: 60, h: 20 },
  { x: 165, y: 575, w: 60, h: 20 },
  { x: 165, y: 815, w: 60, h: 20 },
  { x: 370, y: 140, w: 20, h: 60 },
  { x: 370, y: 420, w: 20, h: 60 },
  { x: 470, y: 140, w: 20, h: 60 },
  { x: 470, y: 420, w: 20, h: 60 },
  { x: 670, y: 295, w: 60, h: 20 },
  { x: 670, y: 615, w: 60, h: 20 },
  { x: 910, y: 140, w: 20, h: 60 },
  { x: 910, y: 420, w: 20, h: 60 },
  { x: 1050, y: 670, w: 60, h: 20 },
]

export const allObjects = rooms.flatMap(r => r.objects.map(o => ({ ...o, roomId: r.id })))

export const spawn = { x: 190, y: 150 }
