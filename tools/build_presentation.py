#!/usr/bin/env python3
"""Build a dependency-free HTML slide deck from Markdown separated by `---`."""
from __future__ import annotations
import argparse, html, re
from pathlib import Path


def inline(text: str) -> str:
    value = html.escape(text, quote=False)
    value = re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    return value


def render_slide(markdown: str, index: int) -> str:
    lines = markdown.strip().splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1; continue
        if line.startswith("#"):
            level = min(3, len(line) - len(line.lstrip("#")))
            out.append(f"<h{level}>{inline(line[level:].strip())}</h{level}>")
            i += 1; continue
        if line.startswith("> "):
            quote = []
            while i < len(lines) and lines[i].startswith("> "):
                quote.append(lines[i][2:]); i += 1
            out.append(f"<blockquote>{inline(' '.join(quote))}</blockquote>")
            continue
        if line.startswith("| ") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-+", lines[i + 1].strip("| ")):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([cell.strip() for cell in lines[i].strip("|").split("|")]); i += 1
            header, body = rows[0], rows[2:]
            out.append("<div class=table-wrap><table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in header) + "</tr></thead><tbody>")
            for row in body:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            out.append("</tbody></table></div>")
            continue
        if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and bool(re.match(r"^\s*\d+\.\s+", lines[i])) == ordered and re.match(r"^\s*(?:[-*]|\d+\.)\s+", lines[i]):
                item = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i])
                items.append(f"<li>{inline(item)}</li>"); i += 1
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|>|\||\s*(?:[-*]|\d+\.)\s+)", lines[i]):
            paragraph.append(lines[i].strip()); i += 1
        out.append(f"<p>{inline(' '.join(paragraph))}</p>")
    classes = "slide title-slide" if index == 0 else "slide"
    return f'<section class="{classes}" data-slide="{index + 1}"><div class="content">{"".join(out)}</div></section>'


def build(source: Path, output: Path) -> None:
    slides_md = re.split(r"\n\s*---\s*\n", source.read_text(encoding="utf-8"))
    slides = "\n".join(render_slide(s, i) for i, s in enumerate(slides_md))
    document = f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>op2u — результаты экспериментов</title>
<style>
:root{{--bg:#08111f;--panel:#0e1b2d;--text:#eef5ff;--muted:#9bb0ca;--cyan:#47d7ff;--green:#5cf2b2;--orange:#ffbd66;--line:#203650}}
*{{box-sizing:border-box}} html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
body:before{{content:"";position:fixed;inset:0;background:radial-gradient(circle at 85% 5%,#123d5c 0,transparent 32%),radial-gradient(circle at 5% 100%,#133b35 0,transparent 30%);pointer-events:none}}
.deck{{height:100%;position:relative}} .slide{{position:absolute;inset:0;display:none;padding:5vh 7vw 7vh;overflow:auto}} .slide.active{{display:flex;animation:enter .26s ease-out}} .content{{margin:auto;width:min(1180px,100%)}}
@keyframes enter{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
h1{{font-size:clamp(2.1rem,5vw,4.8rem);line-height:1.02;margin:0 0 .45em;letter-spacing:-.035em;background:linear-gradient(100deg,#fff 20%,var(--cyan));-webkit-background-clip:text;color:transparent}}
h2{{font-size:clamp(1.25rem,2.5vw,2.2rem);color:var(--green);margin:.2em 0 .8em}} h3{{color:var(--orange);font-size:1.3rem;margin:1em 0 .35em}}
p,li{{font-size:clamp(1rem,1.65vw,1.48rem);line-height:1.48}} p{{margin:.65em 0}} li{{margin:.25em 0}} ul,ol{{padding-left:1.4em}}
strong{{color:#fff}} code{{background:#162840;color:var(--cyan);padding:.12em .36em;border-radius:.3em}} a{{color:var(--cyan);text-decoration:none;border-bottom:1px solid #47d7ff66}}
blockquote{{margin:1.1em 0;padding:.8em 1em;border-left:5px solid var(--green);background:#10251f;border-radius:0 12px 12px 0;font-size:clamp(1.15rem,2vw,1.75rem);line-height:1.45}}
.table-wrap{{overflow:auto;margin:1em 0;border:1px solid var(--line);border-radius:14px}} table{{width:100%;border-collapse:collapse;background:#0b1728dd}} th,td{{padding:.62em .8em;text-align:left;border-bottom:1px solid var(--line);font-size:clamp(.83rem,1.28vw,1.13rem)}} th{{color:var(--cyan);background:#12243a}} tr:last-child td{{border:0}}
.title-slide .content{{text-align:center}} .title-slide h1{{font-size:clamp(3rem,7vw,7rem)}} .title-slide p{{color:var(--muted)}}
.hud{{position:fixed;z-index:5;left:0;right:0;bottom:0;height:5px;background:#15253a}} .progress{{height:100%;background:linear-gradient(90deg,var(--green),var(--cyan));transition:width .2s}}
.counter{{position:fixed;right:2.2vw;bottom:2vh;color:var(--muted);font-variant-numeric:tabular-nums;font-size:.85rem}} .hint{{position:fixed;left:2.2vw;bottom:2vh;color:#6f849f;font-size:.78rem}}
.overview{{overflow:auto}} .overview .deck{{height:auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px;padding:20px}} .overview .slide{{position:relative;display:block!important;min-height:260px;padding:24px;background:var(--panel);border:1px solid var(--line);border-radius:16px;overflow:hidden}} .overview .slide .content{{transform:scale(.62);transform-origin:top left;width:160%}} .overview .hud,.overview .counter,.overview .hint{{display:none}}
@media(max-width:700px){{.slide{{padding:5vh 5vw 8vh}} p,li{{font-size:1rem}} th,td{{font-size:.78rem;padding:.48em}} .hint{{display:none}}}}
@media print{{html,body{{overflow:visible;background:#fff;color:#111}} body:before,.hud,.counter,.hint{{display:none}} .slide{{position:relative;display:flex!important;page-break-after:always;min-height:100vh;background:#fff;color:#111}} h1{{color:#12243a;background:none}} h2{{color:#087a65}} blockquote{{background:#eef8f5}} table{{background:#fff}}}}
</style></head><body><main class="deck">{slides}</main><div class=hud><div class=progress></div></div><div class=counter></div><div class=hint>← → / Space · Home End · O overview</div>
<script>
const slides=[...document.querySelectorAll('.slide')], progress=document.querySelector('.progress'), counter=document.querySelector('.counter'); let current=0;
function show(n){{current=Math.max(0,Math.min(slides.length-1,n));slides.forEach((s,i)=>s.classList.toggle('active',i===current));progress.style.width=((current+1)/slides.length*100)+'%';counter.textContent=`${{current+1}} / ${{slides.length}}`;location.hash='slide-'+(current+1)}}
function fromHash(){{const n=+(location.hash.match(/slide-([0-9]+)/)||[])[1];if(n)show(n-1)}}
addEventListener('keydown',e=>{{if(['ArrowRight','PageDown',' '].includes(e.key)){{e.preventDefault();show(current+1)}}else if(['ArrowLeft','PageUp'].includes(e.key)){{e.preventDefault();show(current-1)}}else if(e.key==='Home')show(0);else if(e.key==='End')show(slides.length-1);else if(e.key.toLowerCase()==='o')document.body.classList.toggle('overview')}});
let x=null;addEventListener('touchstart',e=>x=e.touches[0].clientX);addEventListener('touchend',e=>{{if(x===null)return;let d=e.changedTouches[0].clientX-x;if(Math.abs(d)>45)show(current+(d<0?1:-1));x=null}});addEventListener('hashchange',fromHash);fromHash();show(current);
</script></body></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print(output.resolve().as_uri())


def main() -> None:
    p=argparse.ArgumentParser();p.add_argument("source",type=Path);p.add_argument("output",type=Path);a=p.parse_args();build(a.source,a.output)
if __name__=="__main__": main()
