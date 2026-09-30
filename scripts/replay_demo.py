import json,os,urllib.request
base=os.getenv('SKYGUARD_URL','http://127.0.0.1:8010')
data=json.dumps({'scenario':'temperature_spike','station_id':'AWS-IND-024','steps':3,'seed':26073}).encode()
req=urllib.request.Request(base+'/api/v1/simulator/run',data=data,headers={'Content-Type':'application/json','X-API-Key':os.getenv('SKYGUARD_API_KEY','')})
with urllib.request.urlopen(req,timeout=120) as r: print(json.dumps(json.load(r),indent=2))
