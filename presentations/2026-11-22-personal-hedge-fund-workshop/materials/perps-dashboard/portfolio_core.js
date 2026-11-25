/* Portfolio math, no networking/credentials. Native currencies never mixed. */
(function(root){
'use strict';
const finite=x=>typeof x==='number'&&Number.isFinite(x);
function value(x,name,nullable=true){if(x==null&&nullable)return;if(!finite(x))throw Error('Некорректное поле '+name)}
function legacy(d){return {schema_version:2,accounts:[{id:'onchain-main',label:'Hyperliquid · core + xyz',market:'onchain',mode:d.mode,currency:d.currency,as_of:d.as_of,equity:d.equity,margin_used:d.margin_used,source:d.source,source_url:d.source_url,wallet:d.wallet,coverage:{included:d.positions.length,excluded:[]},positions:d.positions.map((p,i)=>({...p,id:'perp-'+i,kind:'perp',quantity_unit:'ед.',currency:d.currency,multiplier:1}))}]}}
function validate(input){
 const d=input?.schema_version===1?legacy(input):input;
 if(d?.schema_version!==2||!Array.isArray(d.accounts)||d.accounts.length>100)throw Error('Нужен portfolio JSON схемы 1 или 2');
 const ids=new Set();
 for(const a of d.accounts){
  if(typeof a.id!=='string'||ids.has(a.id)||!a.id)throw Error('Повторяющийся / пустой счёт');ids.add(a.id);
  if(!['moex','onchain'].includes(a.market)||!['RUB','USD'].includes(a.currency)||!['sample','snapshot'].includes(a.mode)||typeof a.source!=='string'||!Number.isFinite(Date.parse(a.as_of))||!/[Zz]|[+-]\d\d:\d\d$/.test(a.as_of)||!Array.isArray(a.positions)||a.positions.length>10000)throw Error('Проверьте рынок, валюту, дату с часовым поясом и позиции');
  for(const k of ['equity','margin_used','cash'])value(a[k],k);
  if(a.margin_used!=null&&a.margin_used<0)throw Error('Отрицательная маржа');
  const ps=new Set();
  for(const p of a.positions){
   if(typeof p.id!=='string'||ps.has(p.id)||typeof p.symbol!=='string'||typeof p.venue!=='string'||!['stock','fund','future','perp'].includes(p.kind))throw Error('Проверьте идентификатор и тип позиции');ps.add(p.id);
   if(a.market==='moex'&&p.kind==='perp'||a.market==='onchain'&&p.kind!=='perp')throw Error('Неверный рынок для инструмента');
   if(p.currency!==a.currency||!finite(p.signed_size)||!finite(p.multiplier)||p.multiplier<=0)throw Error('Несовместимая валюта, количество или множитель');
   if(['stock','fund'].includes(p.kind)&&p.multiplier!==1)throw Error('Количество акций/паёв должно быть в штуках, не лотах');
   for(const k of ['entry_price','mark_price','unrealized_pnl','margin_used','liquidation_price','leverage'])value(p[k],k);
   for(const k of ['entry_price','mark_price','liquidation_price','leverage'])if(p[k]!=null&&p[k]<=0)throw Error('Неположительное '+k);
   if(p.kind!=='perp'&&(p.liquidation_price!=null||p.leverage!=null))throw Error('Ликвидация/плечо брокерских инструментов не назначаются наугад');
  }
 }
 return d;
}
function position(p){
 const notional=p.mark_price==null?null:p.signed_size*p.mark_price*p.multiplier;
 const pnl=p.unrealized_pnl??(p.entry_price!=null&&p.mark_price!=null?p.signed_size*(p.mark_price-p.entry_price)*p.multiplier:null);
 const distance=p.kind!=='perp'||p.liquidation_price==null||p.mark_price==null||p.signed_size===0?null:(p.signed_size>0?p.mark_price-p.liquidation_price:p.liquidation_price-p.mark_price)/p.mark_price*100;
 return {notional,pnl,distance};
}
function calculate(input,{market='all',account='all',shift=-3,exclude=''}={}){
 const d=validate(input);if(!finite(shift)||shift< -30||shift>30)throw Error('Сценарий от −30% до +30%');
 const accounts=d.accounts.filter(a=>(market==='all'||a.market===market)&&(account==='all'||a.id===account));
 const rows=[],byCurrency={};
 for(const a of accounts){
  let c=byCurrency[a.currency]??={currency:a.currency,equity:0,equity_known:true,gross:0,net:0,pnl:0,pnl_known:true,prices_complete:true,stress:0,without:0,accounts:0};c.accounts++;
  if(a.equity==null)c.equity_known=false;else c.equity+=a.equity;
  for(const p of a.positions){
   const m=position(p),key=a.id+'::'+p.id;rows.push({account:a,p,key,...m});
   if(m.notional==null)c.prices_complete=false;else {c.gross+=Math.abs(m.notional);c.net+=m.notional;c.stress+=m.notional*shift/100;if(key!==exclude)c.without+=m.notional*shift/100;}
   if(m.pnl==null)c.pnl_known=false;else c.pnl+=m.pnl;
  }
 }
 return {accounts,rows,byCurrency};
}
const api={validate,legacy,position,calculate};root.PortfolioCore=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);
