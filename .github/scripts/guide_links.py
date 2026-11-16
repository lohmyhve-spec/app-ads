#!/usr/bin/env python3
"""가이드 글 내부 링크 생성기 (저장소 루트에서 실행).

  python3 .github/scripts/guide_links.py --all          # 모든 글의 '함께 보면 좋은 글' + 모든 언어 목록 페이지 다시 만들기
  python3 .github/scripts/guide_links.py --new <글경로>  # 새 글 1편에만 관련 글 넣고, 그 언어 목록 페이지만 다시 만들기
  python3 .github/scripts/guide_links.py --check        # 검증만 (고아 글·목록 누락이 있으면 exit 1)

규칙: 기존 글의 <style> 은 건드리지 않는다. 관련 글 블록은 <!-- related --> ~ <!-- /related --> 사이만 바꾼다.
"""
import html, os, re, sys, glob

SITE = "https://mungworks.com/"
LANGS = ["ko", "en", "ja", "es", "it", "de", "fr", "pt"]
L = {  # 목록 제목, 설명, 관련 글 제목, 전체 보기
    "ko": ("사용 가이드", "Mung Works 앱으로 자주 겪는 문제를 해결하는 방법을 모았습니다.", "함께 보면 좋은 글", "가이드 전체 보기"),
    "en": ("Guides", "Step-by-step help for common problems, using Mung Works apps.", "Related guides", "All guides"),
    "ja": ("ガイド", "Mung Works のアプリでよくある困りごとを解決する方法をまとめました。", "関連ガイド", "ガイド一覧"),
    "es": ("Guías", "Ayuda paso a paso para problemas comunes con las apps de Mung Works.", "Guías relacionadas", "Todas las guías"),
    "it": ("Guide", "Aiuto passo passo per i problemi più comuni con le app di Mung Works.", "Guide correlate", "Tutte le guide"),
    "de": ("Anleitungen", "Schritt-für-Schritt-Hilfe zu häufigen Problemen mit den Apps von Mung Works.", "Verwandte Anleitungen", "Alle Anleitungen"),
    "fr": ("Guides", "Aide pas à pas pour les problèmes courants avec les applis Mung Works.", "Guides associés", "Tous les guides"),
    "pt": ("Guias", "Ajuda passo a passo para problemas comuns com os apps da Mung Works.", "Guias relacionados", "Todos os guias"),
}
APP_NAME = {"daopen": ("다오픈", "Daopen"), "feverpal": ("우리아이 열기록 (FeverPal)", "FeverPal"),
            "fastingsignal": ("단식시그널", "Fasting Signal"), "penday": ("펜데이", "PenDay"),
            "bojogeum": ("지원콕", "Jiwonkok"), "multech": ("물한잔", "Mulhanjan")}
APP_ORDER = list(APP_NAME)

def hub_path(lang): return "guide/index.html" if lang == "ko" else f"{lang}/guide/index.html"
def hub_url(lang): return SITE + ("guide/" if lang == "ko" else f"{lang}/guide/")
def app_label(app, lang):
    n = APP_NAME.get(app, (app, app)); return n[0] if lang == "ko" else n[1]

def lastmods():
    sm = open("sitemap.xml", encoding="utf-8").read()
    return dict(re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", sm))

def posts():
    lm = lastmods(); out = []
    for p in sorted(glob.glob("guide/*/index.html") + glob.glob("*/guide/*/index.html")):
        m = re.fullmatch(r"(?:([a-z]{2})/)?guide/([a-z0-9-]+)/index\.html", p)
        if not m: continue
        lang = m.group(1) or "ko"; h = open(p, encoding="utf-8").read()
        t = re.search(r"<title>(.*?) \| Mung Works</title>", h)
        d = re.search(r'<meta name="description" content="([^"]*)"', h)
        app = re.search(r"mungworks\.com/go/([a-z]+)", h)
        url = SITE + p[: -len("index.html")]
        out.append(dict(path=p, lang=lang, url=url, title=html.unescape(t.group(1)) if t else m.group(2),
                        desc=html.unescape(d.group(1)) if d else "", app=app.group(1) if app else "etc",
                        date=lm.get(url, "0000-00-00")))
    return out

def related_block(post, allposts):
    lang = post["lang"]; same = [q for q in allposts if q["lang"] == lang and q["url"] != post["url"]]
    same.sort(key=lambda q: (q["app"] != post["app"], [-int(x) for x in q["date"].split("-")]))
    pick = same[:3]; lab = L[lang]
    lines = ["<!-- related -->", f"<h2>{lab[2]}</h2>", "<ul>"]
    lines += [f'<li><a href="{q["url"]}">{html.escape(q["title"])}</a></li>' for q in pick]
    lines += [f'<li><a href="{hub_url(lang)}">{lab[3]}</a></li>', "</ul>", "<!-- /related -->"]
    return "\n".join(lines)

def put_related(post, allposts):
    h = open(post["path"], encoding="utf-8").read(); blk = related_block(post, allposts)
    if "<!-- related -->" in h:
        h2 = re.sub(r"<!-- related -->.*?<!-- /related -->", lambda _: blk, h, flags=re.S)
    else:
        i = h.rfind("<footer"); assert i > 0, post["path"] + ": footer 없음"
        h2 = h[:i] + blk + "\n\n" + h[i:]
    if h2 != h: open(post["path"], "w", encoding="utf-8").write(h2)
    return h2 != h

def write_hub(lang, allposts):
    mine = [q for q in allposts if q["lang"] == lang]
    if not mine: return None
    ref = open("guide/hwp-kakao-android/index.html", encoding="utf-8").read()
    style = ref[ref.index("<style>"): ref.index("</style>") + len("</style>")]
    lab = L[lang]; url = hub_url(lang); body = []
    for app in sorted({q["app"] for q in mine}, key=lambda a: APP_ORDER.index(a) if a in APP_ORDER else 99):
        body.append(f"<h2>{html.escape(app_label(app, lang))}</h2>\n<ul>")
        for q in sorted([q for q in mine if q["app"] == app], key=lambda q: q["date"], reverse=True):
            body.append(f'<li><a href="{q["url"]}">{html.escape(q["title"])}</a></li>')
        body.append("</ul>")
    others = [l for l in LANGS if l != lang and any(q["lang"] == l for q in allposts)]
    langs = " · ".join(f'<a href="{hub_url(l)}">{L[l][0]}</a>' for l in others)
    page = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{lab[0]} | Mung Works</title>
<meta name="description" content="{html.escape(lab[1])}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{lab[0]}">
<meta property="og:description" content="{html.escape(lab[1])}">
<meta property="og:url" content="{url}">
{style}
</head>
<body>
<main>
<h1>{lab[0]}</h1>
<p class="sub">{html.escape(lab[1])}</p>

{chr(10).join(body)}

<p class="sub">{langs}</p>
<footer><a href="{SITE}">Mung Works</a> · 멍뭉이 (Mung Works) · contact@mungworks.com</footer>
</main>
</body>
</html>
"""
    p = hub_path(lang); os.makedirs(os.path.dirname(p), exist_ok=True)
    old = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    if old != page: open(p, "w", encoding="utf-8").write(page)
    return p

def check(allposts):
    bad = []
    for q in allposts:
        h = open(q["path"], encoding="utf-8").read()
        if hub_url(q["lang"]) not in h: bad.append(f"목록 링크 없음: {q['path']}")
        hub = hub_path(q["lang"])
        if not os.path.exists(hub) or q["url"] not in open(hub, encoding="utf-8").read():
            bad.append(f"목록에 빠짐: {q['path']}")
    sm = open("sitemap.xml", encoding="utf-8").read()
    for l in {q["lang"] for q in allposts}:
        if f"<loc>{hub_url(l)}</loc>" not in sm: bad.append(f"sitemap 에 목록 없음: {hub_url(l)}")
    print(f"[links] 글 {len(allposts)}편, 언어 {sorted({q['lang'] for q in allposts})}, 문제 {len(bad)}건")
    for b in bad: print(" -", b)
    return not bad

if __name__ == "__main__":
    a = sys.argv[1:]; P = posts()
    if a[:1] == ["--all"]:
        n = sum(put_related(q, P) for q in P)
        hubs = [write_hub(l, P) for l in LANGS]
        print(f"[links] 관련 글 갱신 {n}편, 목록 {[h for h in hubs if h]}")
    elif a[:1] == ["--new"] and len(a) == 2:
        q = next(q for q in P if q["path"] == a[1]); put_related(q, P); print("[links] 목록", write_hub(q["lang"], P))
    elif a[:1] != ["--check"]:
        print(__doc__); sys.exit(2)
    sys.exit(0 if check(posts()) else 1)
