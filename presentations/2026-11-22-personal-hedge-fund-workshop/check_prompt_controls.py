"""Exercise slide-local copy affordances, not just the off-slide toolbar."""
from pathlib import Path
import argparse,json
from playwright.sync_api import sync_playwright

def main():
 d=Path(__file__).resolve().parent;a=argparse.ArgumentParser();a.add_argument('--url');a.add_argument('--report');a.add_argument('--screenshots');args=a.parse_args();P=json.loads((d/'prompts.json').read_text());E=json.loads((d/'exercises.json').read_text());report={'copy_checks':0,'read_checks':0,'visible_control_checks':0,'fallback':'pending','errors':[]}
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
  try:
   c=b.new_context(permissions=['clipboard-read','clipboard-write'],viewport={'width':1920,'height':1192});g=c.new_page();g.on('pageerror',lambda e:report['errors'].append(str(e)));g.goto(args.url or (d/'slides.html').as_uri());g.evaluate('document.fonts.ready');g.wait_for_function('window.__deck?.count===21')
   for size in [(1920,1192),(1366,768),(1024,768),(390,844),(320,568),(844,390)]:
    g.set_viewport_size({'width':size[0],'height':size[1]});g.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    for i,(sid,e) in enumerate(E.items()):
     g.evaluate('(i)=>__deck.show(i)',i)
     probe=g.locator('.slide.active .slide-prompt-controls').evaluate('''el=>{const r=el.getBoundingClientRect(),s=el.closest('.slide').getBoundingClientRect(),h=el.closest('.slide').querySelector('header').getBoundingClientRect();return {within:r.left>=s.left&&r.right<=s.right&&r.top>=s.top&&r.bottom<h.top,buttons:[...el.querySelectorAll('button')].every(b=>{const t=b.getBoundingClientRect(),hit=document.elementFromPoint(t.x+t.width/2,t.y+t.height/2);return hit===b||b.contains(hit)})}}''')
     assert probe['within'] and probe['buttons'],(sid,size,probe);assert not g.evaluate('document.documentElement.scrollWidth>innerWidth+1');report['visible_control_checks']+=1
     if size==(1920,1192):
      for button in g.locator('.slide.active [data-prompt]').all():
       key=button.get_attribute('data-prompt');button.click();assert g.evaluate('navigator.clipboard.readText()')==P[key];report['copy_checks']+=1
      g.locator('.slide.active .slide-open-prompt').click();assert g.locator('#prompt-text').inner_text()==P[e['prompt']];g.keyboard.press('Escape');assert g.locator('#prompt-panel').get_attribute('aria-hidden')=='true';report['read_checks']+=1
   # Mobile tap copies from the unscaled, 44px toolbar; keyboard also activates the in-slide button.
   g.set_viewport_size({'width':390,'height':844});g.evaluate('__deck.show(1)');g.locator('#copy-slide-prompt').click();assert g.evaluate('navigator.clipboard.readText()')==P[E['setup']['prompt']]
   g.set_viewport_size({'width':1920,'height':1192});g.locator('.slide.active .slide-copy-prompt').focus();g.keyboard.press('Enter');assert g.evaluate('navigator.clipboard.readText()')==P[E['setup']['prompt']]
   # Clipboard denial must expose selectable text, never a fake success.
   g.evaluate("()=>{navigator.clipboard.writeText=()=>Promise.reject(new Error('denied'))}");g.locator('.slide.active .slide-copy-prompt').click();assert g.locator('#prompt-panel').get_attribute('aria-hidden')=='false';assert 'Ctrl+C' in g.locator('.prompt-status').inner_text();assert g.locator('#prompt-text').inner_text()==P[E['setup']['prompt']];report['fallback']='manual selection passed';g.keyboard.press('Escape')
   if args.screenshots:
    out=Path(args.screenshots);out.mkdir(parents=True,exist_ok=True)
    for i in range(21):g.evaluate('(i)=>__deck.show(i)',i);g.locator('.slide.active').screenshot(path=str(out/f'{i+1:02d}.png'))
   assert not report['errors'];print(json.dumps(report,ensure_ascii=False,indent=2))
   if args.report:Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2))
  finally:b.close()
if __name__=='__main__':main()
