"""Quick test for FCSTN WebSocket server"""
import json, time
import websockets.sync.client as ws

try:
    c = ws.connect('ws://localhost:8765')
    m = c.recv()
    d = json.loads(m)
    print(f'[TEST] Connected. State: {d["data"]["state_name"]}')
    c.send(json.dumps({'type': 'control', 'attention': 0.9, 'engagement': 0.8, 'workload': 0.4}))
    time.sleep(0.5)
    m2 = c.recv()
    d2 = json.loads(m2)
    print(f'[TEST] After control -> State: {d2["data"]["state_name"]}, Attn: {d2["data"]["attention"]:.2f}')
    c.send(json.dumps({'type': 'input', 'text': 'explore the cosmos', 'time_taken': 1.5}))
    time.sleep(0.5)
    m3 = c.recv()
    d3 = json.loads(m3)
    print(f'[TEST] After input -> State: {d3["data"]["state_name"]}, Eng: {d3["data"]["engagement"]:.2f}')
    c.close()
    print('[TEST] All OK!')
except Exception as e:
    print(f'[TEST] FAILED: {e}')
