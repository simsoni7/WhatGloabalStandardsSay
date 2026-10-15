"""Bearer gateway transport. Keys never enter prompts, returned data or logs."""
import json,os,time,urllib.request

def call_stream(model,prompt,max_tokens=24000):
 secret=os.environ['BEDROCK_API_KEY'];start=time.time();parts=[];finish=None;usage=None;first=None
 body={'model':model,'temperature':1,'reasoning_effort':'low','max_tokens':max_tokens,'stream':True,'stream_options':{'include_usage':True},'messages':[{'role':'user','content':prompt}]}
 request=urllib.request.Request('https://frontier-llmgw.aipocnhbank.com/v1/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+secret,'Content-Type':'application/json'})
 with urllib.request.urlopen(request,timeout=180) as response:
  for line in response:
   if first is None:first=round(time.time()-start,2)
   text=line.decode().strip()
   if not text.startswith('data:'):continue
   event=text[5:].strip()
   if event=='[DONE]':break
   event=json.loads(event)
   if event.get('usage'):usage=event['usage']
   for choice in event.get('choices',[]):
    delta=choice.get('delta',{}).get('content')
    if isinstance(delta,str):parts.append(delta)
    if choice.get('finish_reason'):finish=choice['finish_reason']
 text=''.join(parts)
 if secret in text:raise ValueError('Secret echo blocked')
 return {'model':model,'response':text,'usage':usage,'finish_reason':finish,'elapsed_seconds':round(time.time()-start,2),'first_byte_seconds':first,'automatically_adopted':False}
