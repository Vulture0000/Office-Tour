from fastapi import APIRouter

from ..graph.client import get_store

router = APIRouter()


@router.get('/office/rooms')
def get_rooms():
  store = get_store()
  rooms = []
  for row in store.execute('MATCH (r:Room) RETURN r.id as id, r.name as name, r.type as type'):
    rooms.append(row)
  return {'rooms': rooms}


@router.get('/office/room/{room_id}/objects')
def get_room_objects(room_id: str):
  store = get_store()
  nodes = []
  for row in store.execute(
    '''
    MATCH (o)-[:IN_ROOM|:FOUND_IN]->(r:Room {id: $rid})
    RETURN o.id as id, labels(o)[0] as label, o.name as name, o.type as type
    ''',
    {'rid': room_id},
  ):
    nodes.append(row)
  return {'objects': nodes}


@router.get('/office/connections/{node_id}')
def get_connections(node_id: str):
  store = get_store()
  edges = []
  for row in store.execute(
    '''
    MATCH (n {id: $nid})-[e]-(m)
    RETURN type(e) as rel, m.id as to, labels(m)[0] as toLabel, m.name as toName
    ''',
    {'nid': node_id},
  ):
    edges.append(row)
  return {'connections': edges}
