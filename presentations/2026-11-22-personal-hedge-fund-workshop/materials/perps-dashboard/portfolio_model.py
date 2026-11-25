"""Normalise read-only broker/MCP data; no network, credentials or order methods."""
import argparse,json,math,re
from datetime import datetime
from pathlib import Path


def number(v,name,nullable=False):
    if nullable and v is None:return None
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('Invalid '+name)
    return v


def timestamp(v):
    if not isinstance(v,str):raise ValueError('Timestamp required')
    dt=datetime.fromisoformat(v.replace('Z','+00:00'))
    if dt.tzinfo is None:raise ValueError('Timestamp needs timezone')
    return v


def unwrap(v):
    """Accept actual MCP result shapes or the already-decoded API payload."""
    if isinstance(v,dict) and 'jsonrpc' in v:
        if 'error' in v:raise ValueError('MCP protocol error')
        v=v['result']
    if isinstance(v,dict) and ('content' in v or 'structuredContent' in v):
        if v.get('isError'):raise ValueError('MCP tool error')
        if 'structuredContent' in v:v=v['structuredContent']
        else:
            texts=[x['text'] for x in v['content'] if x.get('type')=='text']
            if len(texts)!=1:raise ValueError('Expected one JSON text content')
            v=json.loads(texts[0])
    if isinstance(v,dict) and v.get('error'):raise ValueError('Provider error')
    return v


def array(v,key=None):
    v=unwrap(v)
    if isinstance(v,dict) and key in v:v=v[key]
    if not isinstance(v,list):raise ValueError('Expected response array')
    return v


def from_legacy(d):
    if d.get('schema_version')!=1:raise ValueError('Expected legacy v1')
    rows=[]
    for i,p in enumerate(d['positions']):
        rows.append(dict(p,id='perp-'+str(i),kind='perp',multiplier=1,quantity_unit='ед.',currency=d['currency']))
    a={k:d.get(k) for k in ['as_of','currency','equity','margin_used','source','source_url','wallet']}
    a.update(id='onchain-main',label='Hyperliquid · core + xyz',market='onchain',mode=d['mode'],positions=rows,coverage={'included':len(rows),'excluded':[]},notes=['Сумма отдельно полученных снимков core и xyz; это не единый ликвидационный запас.'])
    return {'schema_version':2,'accounts':[a]}


def from_alfa(bundle,account_id,balance_group=None):
    """Official PRO MCP fields; quantity is shares/contracts, NEVER lots.

    bundle = {as_of, positions, balances, instruments, futures_info?}.
    The agent obtains each response using existing authorised API/MCP.
    No assumptions about a remote endpoint or token are made here.
    """
    if isinstance(account_id,bool) or not isinstance(account_id,int):raise ValueError('Explicit integer account_id required')
    as_of=timestamp(bundle['as_of'])
    positions=array(bundle['positions'],'positions');balances=array(bundle['balances'],'balances')
    balances=[b for b in balances if b.get('accountId')==account_id]
    if balance_group is not None:balances=[b for b in balances if b.get('balanceGroup')==balance_group]
    if len(balances)!=1:raise ValueError('Select exactly one balance group; Unified/Papers/Futures must not be summed blindly')
    b=balances[0];group=b['balanceGroup']
    positions=[p for p in positions if p.get('accountId')==account_id and p.get('balanceGroup')==group]
    instruments=bundle.get('instruments',[])
    if not isinstance(instruments,list):raise ValueError('Expected merged instrument metadata array')
    meta={x['id']:x for x in instruments};infos=bundle.get('futures_info',{})
    rows=[];excluded=[]
    for p in positions:
        qty=number(p.get('quantity'),'quantity')
        if qty==0:continue
        m=meta.get(p.get('instrumentId'))
        if not m:
            excluded.append({'instrument':str(p.get('instrumentId')),'reason':'Нет спецификации инструмента'});continue
        kind=p.get('instrumentType');label=m.get('ticker') or m.get('name') or str(m['id'])
        # All account balances are RUB; position prices may NOT be RUB.
        if m.get('currencyId')!=0:
            excluded.append({'instrument':label,'reason':'Цена не в рублях; нужен явный FX и отдельная оценка'});continue
        if kind not in ['Stock','EquityParticipation','Futures']:
            excluded.append({'instrument':label,'reason':'Нужна отдельная формула для '+str(kind)});continue
        mult=1
        if kind=='Futures':
            info=infos.get(str(p['instrumentId']),{})
            step=number(info.get('priceStep'),'priceStep',True);cost=number(info.get('priceStepCost'),'priceStepCost',True)
            if step is None or cost is None or step<=0 or cost<=0:
                excluded.append({'instrument':label,'reason':'Нет стоимости шага / шага цены фьючерса'});continue
            mult=cost/step
        mark=number(p.get('price'),'price',True);entry=number(p.get('averagePrice'),'averagePrice',True)
        if mark is not None and mark<=0:raise ValueError('Nonpositive price')
        if entry is not None and entry<=0:entry=None
        pnl=number(p.get('profitLoss'),'profitLoss',True)
        row={'id':'moex-'+str(p['instrumentId']),'symbol':label,'venue':'MOEX','kind':{'Stock':'stock','EquityParticipation':'fund','Futures':'future'}[kind], 'signed_size':qty,'quantity_unit':'контр.' if kind=='Futures' else 'шт.','currency':'RUB','entry_price':entry,'mark_price':mark,'multiplier':mult,'unrealized_pnl':pnl,'pnl_source':'profitLoss брокера','margin_used':number(p.get('warranty'),'warranty',True) if kind=='Futures' else None,'liquidation_price':None,'leverage':None}
        rows.append(row)
    equity=number(b.get('currentBalance'),'currentBalance',True)
    a={'id':'moex-main','label':'Мосбиржа · выбранный счёт','market':'moex','mode':bundle.get('mode','snapshot'),'currency':'RUB','as_of':as_of,'equity':equity,'cash':number(b.get('money'),'money',True),'margin_used':number(b.get('marginRequirement'),'marginRequirement',True),'positions':rows,'source':'Брокер · чтение API/MCP','source_url':'https://alfabank.ru/make-money/investments/pro-terminal/mcp/','coverage':{'included':len(rows),'excluded':excluded},'notes':['Баланс currentBalance уже включает позиции: деньги и стоимость бумаг повторно не прибавляются.','Группа: '+group,'Плечо и цена ликвидации акций не выдумываются; маржинальные требования показываются на уровне счёта.']}
    return {'schema_version':2,'accounts':[a]}


def combine(*docs):
    accounts=[]
    for d in docs:
        d=from_legacy(d) if d.get('schema_version')==1 else d
        if d.get('schema_version')!=2:raise ValueError('Expected schema v1 or v2')
        accounts.extend(d['accounts'])
    ids=[a['id'] for a in accounts]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate account aliases; do not double count')
    return {'schema_version':2,'accounts':accounts}


def main():
    p=argparse.ArgumentParser(description='Normalise existing authorised API/MCP results without credentials')
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('alfa');a.add_argument('--input',required=True);a.add_argument('--account-id',type=int,required=True);a.add_argument('--balance-group');a.add_argument('--output',required=True)
    c=sub.add_parser('combine');c.add_argument('--input',nargs='+',required=True);c.add_argument('--output',required=True)
    args=p.parse_args()
    if args.command=='alfa':result=from_alfa(json.loads(Path(args.input).read_text()),args.account_id,args.balance_group)
    else:result=combine(*(json.loads(Path(f).read_text()) for f in args.input))
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'accounts':len(result['accounts']),'positions':sum(len(a['positions']) for a in result['accounts']),'output':args.output}))

if __name__=='__main__':main()
