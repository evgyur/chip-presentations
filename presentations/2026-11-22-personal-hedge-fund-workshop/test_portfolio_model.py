import copy,importlib.util,json,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('portfolio_model',D/'materials/perps-dashboard/portfolio_model.py');assert spec is not None and spec.loader is not None;m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture():
 return {'mode':'sample','as_of':'2026-11-22T12:00:00+03:00','positions':[{'accountId':77,'balanceGroup':'Papers','instrumentId':1,'instrumentType':'Stock','quantity':300,'price':300,'averagePrice':290,'profitLoss':3000}],'balances':[{'accountId':77,'balanceGroup':'Papers','currentBalance':1000000,'money':910000,'marginRequirement':0}],'instruments':[{'id':1,'ticker':'SBER','currencyId':0}]}

class ModelTests(unittest.TestCase):
 def test_stock_units_not_lots(self):
  a=m.from_alfa(fixture(),77)['accounts'][0];p=a['positions'][0]
  self.assertEqual(p['signed_size'],300);self.assertEqual(p['multiplier'],1);self.assertEqual(p['signed_size']*p['mark_price'],90000)
  self.assertEqual(a['equity'],1000000);self.assertEqual(a['cash'],910000);self.assertIsNone(p['leverage']);self.assertIsNone(p['liquidation_price'])
  self.assertNotIn('accountId',json.dumps(a));self.assertNotIn('77',a['id'])
 def test_decode_mcp_json_text(self):
  d=fixture();d['positions']={'jsonrpc':'2.0','result':{'content':[{'type':'text','text':json.dumps(d['positions'])}],'isError':False}}
  self.assertEqual(len(m.from_alfa(d,77)['accounts'][0]['positions']),1)
 def test_provider_error_rejected(self):
  d=fixture();d['positions']={'content':[{'type':'text','text':'failure'}],'isError':True}
  with self.assertRaises(ValueError):m.from_alfa(d,77)
 def test_balance_groups_not_doublecounted(self):
  d=fixture();d['balances'].append(dict(d['balances'][0],balanceGroup='Unified'))
  with self.assertRaises(ValueError):m.from_alfa(d,77)
  self.assertEqual(m.from_alfa(d,77,'Papers')['accounts'][0]['equity'],1000000)
 def test_explicit_account(self):
  for bad in [None,True,'77']:
   with self.assertRaises(ValueError):m.from_alfa(fixture(),bad)
  d=fixture();d['positions'].append(dict(d['positions'][0],accountId=88));self.assertEqual(len(m.from_alfa(d,77)['accounts'][0]['positions']),1)
 def test_futures_multiplier_and_short(self):
  d=fixture();d['positions'][0].update(instrumentType='Futures',quantity=-2,price=100,averagePrice=120,profitLoss=200,warranty=100)
  d['futures_info']={'1':{'priceStep':2,'priceStepCost':10}}
  p=m.from_alfa(d,77)['accounts'][0]['positions'][0];self.assertEqual(p['multiplier'],5);self.assertEqual(p['signed_size']*p['mark_price']*p['multiplier'],-1000)
  del d['futures_info'];a=m.from_alfa(d,77)['accounts'][0];self.assertEqual(a['positions'],[]);self.assertEqual(len(a['coverage']['excluded']),1)
 def test_unsupported_visible(self):
  d=fixture();d['positions'][0]['instrumentType']='Bond';a=m.from_alfa(d,77)['accounts'][0];self.assertEqual(a['positions'],[]);self.assertIn('Bond',a['coverage']['excluded'][0]['reason'])
  d=fixture();d['instruments'][0]['currencyId']=9;a=m.from_alfa(d,77)['accounts'][0];self.assertEqual(len(a['coverage']['excluded']),1)
 def test_unknown_price_and_time(self):
  d=fixture();d['positions'][0]['price']=None;self.assertIsNone(m.from_alfa(d,77)['accounts'][0]['positions'][0]['mark_price'])
  d['as_of']='2026-11-22T12:00:00'
  with self.assertRaises(ValueError):m.from_alfa(d,77)
 def test_legacy_and_duplicate(self):
  d=json.loads((D/'portfolio.json').read_text());a=m.from_legacy(d);self.assertEqual(len(a['accounts'][0]['positions']),4)
  with self.assertRaises(ValueError):m.combine(a,a)
 def test_demo_native_currencies(self):
  d=json.loads((D/'combined-demo.json').read_text());self.assertEqual({a['currency'] for a in d['accounts']},{'USD','RUB'})
  moex=next(a for a in d['accounts'] if a['market']=='moex');self.assertEqual(moex['mode'],'sample');self.assertEqual(len(moex['positions']),3)
  self.assertEqual(sum(abs(p['signed_size']*p['mark_price']*p['multiplier']) for p in moex['positions']),190000)
  self.assertEqual(sum(p['unrealized_pnl'] for p in moex['positions']),2000)

if __name__=='__main__':unittest.main()
