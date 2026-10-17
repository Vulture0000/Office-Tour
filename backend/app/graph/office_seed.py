from .client import get_store


def seed_office() -> None:
  store = get_store()

  # Add rooms
  rooms = [
    ('lobby', 'Room', {'id': 'lobby', 'name': 'Lobby', 'type': 'lobby'}),
    ('reception', 'Room', {'id': 'reception', 'name': 'Reception', 'type': 'reception'}),
    ('hallway1', 'Room', {'id': 'hallway1', 'name': 'Main Hallway', 'type': 'hallway'}),
    ('meeting_room', 'Room', {'id': 'meeting_room', 'name': 'Meeting Room', 'type': 'meeting'}),
    ('it_room', 'Room', {'id': 'it_room', 'name': 'IT Room', 'type': 'it'}),
    ('office_area', 'Room', {'id': 'office_area', 'name': 'Office Area', 'type': 'office'}),
    ('kitchen', 'Room', {'id': 'kitchen', 'name': 'Kitchen', 'type': 'kitchen'}),
  ]
  for rid, label, props in rooms:
    store.create_node(label, props)

  # Add people
  people = [
    ('receptionist', 'Person', {'id': 'receptionist', 'name': 'Receptionist', 'role': 'Receptionist'}),
    ('bob', 'Person', {'id': 'bob', 'name': 'Bob', 'role': 'Tech Lead'}),
    ('alice', 'Person', {'id': 'alice', 'name': 'Alice', 'role': 'DevOps'}),
    ('carol', 'Person', {'id': 'carol', 'name': 'Carol', 'role': 'Engineer'}),
    ('dave', 'Person', {'id': 'dave', 'name': 'Dave', 'role': 'PM'}),
  ]
  for pid, label, props in people:
    store.create_node(label, props)

  # Add items
  items = [
    ('badge', 'Object', {'id': 'badge', 'name': 'Visitor Badge', 'type': 'badge'}),
    ('directory', 'Document', {'id': 'directory', 'name': 'Office Directory', 'type': 'directory', 'title': 'Office Directory'}),
    ('server_doc', 'Document', {'id': 'server_doc', 'name': 'Server Notes', 'type': 'doc', 'title': 'Server Notes'}),
    ('atlas_doc', 'Document', {'id': 'atlas_doc', 'name': 'Atlas Design Doc', 'type': 'doc', 'title': 'Atlas Design Doc'}),
    ('fridge_note', 'Object', {'id': 'fridge_note', 'name': 'Sticky Note', 'type': 'note'}),
  ]
  for iid, label, props in items:
    store.create_node(label, props)

  # Connect people to rooms
  store.create_edge('receptionist', 'reception', 'IN_ROOM')
  store.create_edge('bob', 'meeting_room', 'IN_ROOM')
  store.create_edge('alice', 'it_room', 'IN_ROOM')
  store.create_edge('carol', 'office_area', 'IN_ROOM')
  store.create_edge('dave', 'office_area', 'IN_ROOM')

  # Connect items to rooms/people
  store.create_edge('badge', 'lobby', 'FOUND_IN')
  store.create_edge('directory', 'hallway1', 'FOUND_IN')
  store.create_edge('server_doc', 'it_room', 'FOUND_IN')
  store.create_edge('atlas_doc', 'office_area', 'FOUND_IN')
  store.create_edge('fridge_note', 'kitchen', 'FOUND_IN')

  # Room connections
  store.create_edge('lobby', 'reception', 'CONNECTS_TO')
  store.create_edge('lobby', 'hallway1', 'CONNECTS_TO')
  store.create_edge('reception', 'hallway1', 'CONNECTS_TO')
  store.create_edge('hallway1', 'meeting_room', 'CONNECTS_TO')
  store.create_edge('hallway1', 'it_room', 'CONNECTS_TO')
  store.create_edge('hallway1', 'office_area', 'CONNECTS_TO')
  store.create_edge('office_area', 'kitchen', 'CONNECTS_TO')
