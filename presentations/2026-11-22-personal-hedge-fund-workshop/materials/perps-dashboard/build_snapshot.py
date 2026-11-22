#!/usr/bin/env python3
"""Read-only Hyperliquid perpetual positions → dashboard JSON. No credentials."""
import argparse,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
DEFAULT='0xa00db4fbef1fe1dae76e3b975d0969663c11690c'
def info(body):
 req=urllib.request.Request('https://api.hyperliquid.xyz/info',json.dumps(body).encode(),{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=25)as r:return json.load(r)
def normalize(wallet,state):
 rows=[]
 for item in state['assetPositions']:
  p=item['position'];size=float(p['szi'])
  if not size:continue
  rows.append({'symbol':p['coin'],'venue':'Hyperliquid','signed_size':size,'entry_price':float(p['entryPx']),'mark_price':float(p['positionValue'])/abs(size),'liquidation_price':float(p['liquidationPx'])if p.get('liquidationPx')is not None else None,'leverage':p['leverage'].get('value'),'margin_mode':p['leverage'].get('type'),'margin_used':float(p['marginUsed']),'unrealized_pnl':float(p['unrealizedPnl'])})
 return {'schema_version':1,'mode':'snapshot','currency':'USD','wallet':wallet,'source':'Hyperliquid · '+wallet,'source_url':'https://intel.trade/address/'+wallet,'api_source':'https://api.hyperliquid.xyz/info','as_of':datetime.fromtimestamp(state['time']/1000,timezone.utc).isoformat(),'equity':float(state['marginSummary']['accountValue']),'margin_used':float(state['marginSummary']['totalMarginUsed']),'positions':rows}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--wallet',default=DEFAULT);parser.add_argument('--output',default='portfolio.json');args=parser.parse_args()
 if not re.fullmatch('0x[0-9a-fA-F]{40}',args.wallet):parser.error('Expected a public 0x wallet address')
 state=info({'type':'clearinghouseState','user':args.wallet});d=normalize(args.wallet,state);Path(args.output).write_text(json.dumps(d,ensure_ascii=False,indent=2));print(json.dumps({'positions':len(d['positions']),'as_of':d['as_of'],'output':args.output}))
if __name__=='__main__':main()
