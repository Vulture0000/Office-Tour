import os

files = [
  '/Users/vulture/GraphHacks/frontend/src/App.jsx',
  '/Users/vulture/GraphHacks/frontend/src/graph/GraphPanel.jsx',
  '/Users/vulture/GraphHacks/frontend/src/chat/ChatPanel.jsx',
  '/Users/vulture/GraphHacks/frontend/src/components/PeoplePanel.jsx',
]
for fn in files:
    with open(fn, 'r') as f:
        s = f.read()
    # replace api.get('/api/xxx') with api.get('/xxx') if baseURL is /api
    s = s.replace("api.get('/api/", "api.get('/")
    s = s.replace("api.post('/api/", "api.post('/")
    s = s.replace("api.patch('/api/", "api.patch('/")
    s = s.replace("api.delete('/api/", "api.delete('/")
    with open(fn, 'w') as f:
        f.write(s)
    print('fixed', fn)
