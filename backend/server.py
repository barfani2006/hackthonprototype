import asyncio, json, math, random, sqlite3, time
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
ROOT=Path(__file__).resolve().parents[1]; DB=ROOT/'data'/'mine.db'; DB.parent.mkdir(exist_ok=True)
app=FastAPI(title='Advanced Coal Mine Digital Twin'); app.mount('/static',StaticFiles(directory=ROOT/'frontend'),name='static')
with sqlite3.connect(DB) as c:
 c.execute("CREATE TABLE IF NOT EXISTS events(ts REAL,kind TEXT,message TEXT)"); c.execute("CREATE TABLE IF NOT EXISTS telemetry(ts REAL,production REAL,methane REAL,temperature REAL,water REAL,ventilation REAL)")
class Simulation:
 def __init__(self):
  self.t=0.; self.production=0.; self.alarm=False; self.scenario='none'; self.paused=False; self.speed=1.; self.machines=[]
  specs=[('EX-01','excavator',-38,-18,-12),('EX-02','excavator',35,-20,-12),('TR-01','truck',-18,-8,-8),('TR-02','truck',0,-8,-8),('TR-03','truck',18,-8,-8),('CV-01','conveyor',0,0,-18),('P-01','pump',-48,12,-25),('F-01','fan',48,12,-25)]
  for i,(name,kind,x,y,z) in enumerate(specs): self.machines.append({'id':name,'kind':kind,'x':x,'y':y,'z':z,'health':random.uniform(.82,1),'state':'running','phase':i*.8})
 def log(self,k,msg):
  with sqlite3.connect(DB) as c:c.execute('INSERT INTO events VALUES (?,?,?)',(time.time(),k,msg))
 def snapshot(self):
  methane=.55+.18*math.sin(self.t/7)+random.uniform(-.04,.04); temp=29+2*math.sin(self.t/13)+random.uniform(-.5,.5); water=max(0,18+8*math.sin(self.t/17)+random.uniform(-2,2)); vent=max(55,92+8*math.sin(self.t/11))
  if self.alarm:
   if self.scenario in ('gas','general'): methane += 3.8; vent=max(25,vent-35)
   elif self.scenario=='fire': temp += 32; vent=max(20,vent-25)
   elif self.scenario=='flood': water += 65; vent=max(35,vent-10)
   elif self.scenario=='equipment': vent=max(30,vent-20)
  for m in self.machines:
   if m['state']=='running':
    m['health']=max(.05,m['health']-random.uniform(0,.0007))
    if m['health']<.18 and random.random()<.015: m['state']='failed'; self.log('failure',m['id']+' failed')
   elif m['state']=='failed' and random.random()<.01:m['state']='maintenance'
   elif m['state']=='maintenance' and random.random()<.02:m['state']='running';m['health']=.95;self.log('maintenance',m['id']+' restored')
   m['phase']+=.035*self.speed
   if m['kind']=='truck' and m['state']=='running':m['x']=-25+50*((math.sin(m['phase'])+1)/2);m['z']=-8+3*math.sin(m['phase']*2)
   if m['kind']=='excavator' and m['state']=='running':m['y']=-18+2*math.sin(m['phase'])
  active=sum(m['state']=='running' for m in self.machines); self.production+=active*.035*self.speed
  with sqlite3.connect(DB) as c:c.execute('INSERT INTO telemetry VALUES (?,?,?,?,?,?)',(time.time(),self.production,methane,temp,water,vent))
  return {'time':round(self.t,1),'production':round(self.production,2),'alarm':self.alarm,'scenario':self.scenario,'paused':self.paused,'metrics':{'methane':round(methane,2),'temperature':round(temp,1),'water':round(water,1),'ventilation':round(vent,1),'active_machines':active,'total_machines':len(self.machines)},'machines':self.machines}
sim=Simulation()
@app.get('/')
def index():return FileResponse(ROOT/'frontend'/'index.html')
@app.post('/api/alarm/{state}')
def alarm(state:str):
 sim.alarm=state.lower() in ('on','true','1'); sim.scenario='general' if sim.alarm else 'none'; sim.log('alarm','Emergency '+('activated' if sim.alarm else 'cleared')); return {'alarm':sim.alarm,'scenario':sim.scenario}
@app.post('/api/emergency/{scenario}')
def emergency(scenario:str):
 scenario=scenario.lower()
 if scenario in ('clear','off','none'):
  sim.alarm=False; sim.scenario='none'; msg='Emergency cleared'
 elif scenario in ('gas','fire','flood','equipment','general'):
  sim.alarm=True; sim.scenario=scenario; msg='Emergency scenario activated: '+scenario
 else:
  return {'error':'Unknown scenario','allowed':['gas','fire','flood','equipment','clear']}
 sim.log('alarm',msg); return {'alarm':sim.alarm,'scenario':sim.scenario}
@app.post('/api/pause/{state}')
def pause(state:str):sim.paused=state.lower() in ('on','true','1');return {'paused':sim.paused}
@app.post('/api/speed/{value}')
def speed(value:float):sim.speed=max(.25,min(5,value));return {'speed':sim.speed}
@app.get('/api/history')
def history():
 with sqlite3.connect(DB) as c: rows=c.execute('SELECT * FROM telemetry ORDER BY ts DESC LIMIT 100').fetchall()
 return rows
@app.websocket('/ws')
async def ws(websocket:WebSocket):
 await websocket.accept()
 try:
  while True:
   if not sim.paused:sim.t+=.25*sim.speed
   await websocket.send_text(json.dumps(sim.snapshot()));await asyncio.sleep(.5)
 except (WebSocketDisconnect,RuntimeError):pass
if __name__=='__main__':
 import os, uvicorn
 uvicorn.run('backend.server:app', host='0.0.0.0', port=int(os.environ.get('PORT', '8000')), reload=False)
