"""Manual browser regression for slide/footer clearance; no app/content changes."""
from pathlib import Path
import argparse,json


def main():
    from importlib import import_module
    sync_playwright=import_module('playwright.sync_api').sync_playwright
    parser=argparse.ArgumentParser();parser.add_argument('--url');parser.add_argument('--render-dir');parser.add_argument('--report');args=parser.parse_args()
    d=Path(__file__).resolve().parent
    url=args.url or (d/'slides.html').as_uri()
    sizes=[(1920,1192),(1920,1080),(1440,900),(1366,768),(1280,720),(1024,768),(768,1024),(390,844),(844,390)]
    problems=[];checks=0;minimum=None;errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
        try:
            page=browser.new_page(viewport={'width':1920,'height':1192});page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url,wait_until='load');page.evaluate('document.fonts.ready');page.wait_for_function('window.__deck?.count===22')
            for width,height in sizes:
                page.set_viewport_size({'width':width,'height':height})
                for i in range(22):
                    page.evaluate('(i)=>window.__deck.show(i)',i)
                    result=page.evaluate('''()=>{
                        const s=document.querySelector('.slide.active'),r=s.getBoundingClientRect(),f=s.querySelector('.slide-footer').getBoundingClientRect(),scale=r.width/1600;
                        const elements=[...s.querySelectorAll('.content,.content>*,.content h3,.content p,.content img,.action-row,.takeaway,.ph-source')].filter(e=>getComputedStyle(e).display!=='none');
                        const boxes=elements.map(e=>{const b=e.getBoundingClientRect();return {element:e.className||e.tagName,bottom:b.bottom,gap:(f.top-b.bottom)/scale}}).filter(x=>x.bottom>r.top);
                        return {slide:s.id,minimum:Math.min(...boxes.map(x=>x.gap)),overlaps:boxes.filter(x=>x.gap<7.5),pageOverflow:document.documentElement.scrollWidth>innerWidth+1};
                    }''')
                    checks+=1
                    minimum=result['minimum'] if minimum is None else min(minimum,result['minimum'])
                    if result['overlaps'] or result['pageOverflow']:problems.append(dict(viewport=[width,height],**result))
            # Controls must survive the CSS patch: one keypress, notes and exact copy payload.
            page.set_viewport_size({'width':1920,'height':1192});page.evaluate('window.__deck.show(14)');page.keyboard.press('ArrowRight');assert page.evaluate('window.__deck.current')==15
            page.keyboard.press('ArrowLeft');assert page.evaluate('window.__deck.current')==14
            page.keyboard.press('n');assert page.locator('.notes').evaluate("x=>x.classList.contains('open')");page.keyboard.press('Escape');page.wait_for_timeout(250)
            if args.render_dir:
                out=Path(args.render_dir);out.mkdir(parents=True,exist_ok=True)
                for i in range(22):
                    page.mouse.move(0,0);page.evaluate('(i)=>window.__deck.show(i)',i);page.wait_for_timeout(60);page.locator('.slide.active').screenshot(path=str(out/f'{i+1:02d}.png'),animations='disabled')
            report={'slides':22,'viewports':len(sizes),'layout_checks':checks,'minimum_footer_gap_native_px':minimum,'problems':problems,'console_errors':errors,'navigation':'passed','notes':'passed'}
            if args.report:Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(report,ensure_ascii=False,indent=2))
            assert not problems and not errors,'Footer/layout regression failed'
        finally:browser.close()

if __name__=='__main__':main()
