import json
import os
from typing import Any, Dict

from .client import get_graph
from .schema import validate_node_labels, validate_relationship_types

OFFICE_DATA = {
  'nodes': [],
  'edges': []
}

def load_office_data() -> Dict[str, Any]:
  return OFFICE_DATA

def seed_office() -> None:
  graph = get_graph()
  data = load_office_data()

  # Add rooms
  rooms = [
    ('lobby', 'Room', {'name': 'Lobby', 'type': 'lobby'}),
    ('reception', 'Room', {'name': 'Reception', 'type': 'reception'}),
    ('hallway1', 'Room', {'name': 'Main Hallway', 'type': 'hallway'}),
    ('meeting_room', 'Room', {'name': 'Meeting Room', 'type': 'meeting'}),
    ('it_room', 'Room', {'name': 'IT Room', 'type': 'it'}),
    ('office_area', 'Room', {'name': 'Office Area', 'type': 'office'}),
    ('kitchen', 'Room', {'name': 'Kitchen', 'type': 'kitchen'}),
  ]
  for rid, label, props in rooms:
    graph.upsert_node(rid, label, props)

  # Add people
  people = [
    ('receptionist', 'Person', {'name': 'Receptionist', 'role': 'Receptionist'}),
    ('bob', 'Person', {'name': 'Bob', 'role': 'Tech Lead'}),
    ('alice', 'Person', {'name': 'Alice', 'role': 'DevOps'}),
    ('carol', 'Person', {'name': 'Carol', 'role': 'Engineer'}),
    ('dave', 'Person', {'name': 'Dave', 'role': 'PM'}),
  ]
  for pid, label, props in people:
    graph.upsert_node(pid, label, props)

  # Add items
  items = [
    ('badge', 'Object', {'name': 'Visitor Badge', 'type': 'badge'}),
    ('directory', 'Document', {'name': 'Office Directory', 'type': 'directory'}),
    ('server_doc', 'Document', {'name': 'Server Notes', 'type': 'doc'}),
    ('atlas_doc', 'Document', {'name': 'Atlas Design Doc', 'type': 'doc'}),
    ('fridge_note', 'Object', {'name': 'Sticky Note', 'type': 'note'}),
  ]
  for iid, label, props in items:
    graph.upsert_node(iid, label, props)

  # Connect people to rooms
  graph.upsert_edge('receptionist', 'IN_ROOM', 'reception', {})
  graph.upsert_edge('bob', 'IN_ROOM', 'meeting_room', {})
  graph.upsert_edge('alice', 'IN_ROOM', 'it_room', {})
  graph.upsert_edge('carol', 'IN_ROOM', 'office_area', {})
  graph.upsert_edge('dave', 'IN_ROOM', 'office_area', {})

  # Connect items to rooms/people
  graph.upsert_edge('badge', 'FOUND_IN', 'lobby', {})
  graph.upsert_edge('directory', 'FOUND_IN', 'hallway1', {})
  graph.upsert_edge('server_doc', 'FOUND_IN', 'it_room', {})
  graph.upsert_edge('atlas_doc', 'FOUND_IN', 'office_area', {})
  graph.upsert_edge('fridge_note', 'FOUND_IN', 'kitchen', {})

  # Room connections
  graph.upsert_edge('lobby', 'CONNECTS_TO', 'reception', {})
  graph.upsert_edge('lobby', 'CONNECTS_TO', 'hallway1', {})
  graph.upsert_edge('reception', 'CONNECTS_TO', 'hallway1', {})
  graph.upsert_edge('hallway1', 'CONNECTS_TO', 'meeting_room', {})
  graph.upsert_edge('hallway1', 'CONNECTS_TO', 'it_room', {})
  graph.upsert_edge('hallway1', 'CONNECTS_TO', 'office_area', {})
  graph.upsert_edge('office_area', 'CONNECTS_TO', 'kitchen', {})
