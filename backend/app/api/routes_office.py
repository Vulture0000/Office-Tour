from fastapi import APIRouter

from ..graph.client import get_store

router = APIRouter(prefix="/api", tags=["office"])


@router.get('/office/rooms')
def get_rooms():
  store = get_store()
  nodes = store.list_nodes('Room')
  rooms = []
  for n in nodes:
    props = n.get('props') or {}
    rooms.append({
      'id': props.get('id') or n.get('id'),
      'name': props.get('name'),
      'type': props.get('type')
    })
  return {'rooms': rooms}


@router.get('/office/room/{room_id}/objects')
def get_room_objects(room_id: str):
  store = get_store()
  nodes, _ = store.expand(room_id, rels=['IN_ROOM', 'FOUND_IN'], depth=1)
  objs = []
  for n in nodes:
    props = n.get('props') or {}
    nid = props.get('id') or n.get('id')
    if nid == room_id:
      continue
    objs.append({
      'id': nid,
      'label': n.get('label'),
      'name': props.get('name'),
      'type': props.get('type')
    })
  return {'objects': objs}


@router.get('/office/connections/{node_id}')
def get_connections(node_id: str):
  store = get_store()
  nodes, edges = store.expand(node_id, depth=1)
  # build map
  node_map = {}
  for n in nodes:
    props = n.get('props') or {}
    nid = props.get('id') or n.get('id')
    node_map[nid] = n
  conns = []
  for e in edges:
    if e['source'] == node_id:
      to = e['target']
    elif e['target'] == node_id:
      to = e['source']
    else:
      to = e['target']
    target = node_map.get(to) or {}
    tprops = target.get('props') or {}
    conns.append({
      'rel': e['rel'],
      'to': to,
      'toLabel': target.get('label'),
      'toName': tprops.get('name')
    })
  return {'connections': conns}
