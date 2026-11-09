# -*- coding: utf-8 -*-
"""Gera o blog estático da Mega Motos dentro do repositório do site.
Uso: python build_blog.py <pasta-do-repo>
É idempotente: pode rodar de novo depois de editar blog_posts.py."""
import sys, os, re, json, html, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blog_posts import POSTS

REPO = sys.argv[1]
BASE = "https://megamotos.dluz.com.br"
DATE = "2026-11-09"
DATE_BR = "9 de novembro de 2026"
WA1 = "556336021643"

idx_path = os.path.join(REPO, "index.html")
idx = open(idx_path, encoding="utf-8").read()

# ---------- pedaços reaproveitados da home ----------
def between(s, start, end, include_end=True):
    a = s.index(start); b = s.index(end, a) + (len(end) if include_end else 0)
    return s[a:b]

sprite = between(idx, '<svg width="0" height="0"', '</svg>\n\n<header', include_end=False)
header = between(idx, '<header id="top">', '</header>')
footer = between(idx, '<footer class="site-footer">', '</footer>')
floaters = between(idx, '<a class="wa-float"', '</div>\n\n<script>', include_end=False) + '</div>'

def externalize(block):
    # links de âncora da home passam a apontar para /#secao; ícones (#i-...) ficam
    block = re.sub(r'href="#(?!i-)top"', 'href="/"', block)
    block = re.sub(r'href="#(?!i-)([a-z]+)"', r'href="/#\1"', block)
    block = block.replace('src="assets/', 'src="/assets/')
    return block

header_ext = externalize(header)
footer_ext = externalize(footer)

def esc(s): return html.escape(s, quote=True)
def wa(text): return f"https://wa.me/{WA1}?text=" + urllib.parse.quote(text)

PAGE_JS = """<script>
  const header=document.querySelector('header');const onScroll=()=>header.classList.toggle('scrolled',scrollY>8);addEventListener('scroll',onScroll,{passive:true});onScroll();
  const mb=document.getElementById('menuBtn'),mm=document.getElementById('mobileMenu');mb.addEventListener('click',()=>{const o=mm.classList.toggle('open');mb.setAttribute('aria-expanded',o)});
  const y=document.getElementById('year');if(y)y.textContent=new Date().getFullYear();
</script>"""

def page(title, desc, canonical, body, jsonld, og_img="/assets/loja/loja_interior_hd.jpg", og_type="website"):
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in jsonld)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}" />
<link rel="canonical" href="{canonical}" />
<meta name="theme-color" content="#111111" />
<meta property="og:type" content="{og_type}" />
<meta property="og:locale" content="pt_BR" />
<meta property="og:site_name" content="Mega Motos Paraíso" />
<meta property="og:title" content="{esc(title)}" />
<meta property="og:description" content="{esc(desc)}" />
<meta property="og:url" content="{canonical}" />
<meta property="og:image" content="{BASE}{og_img}" />
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23111'/%3E%3Cpath d='M14 46V18h7l11 15 11-15h7v28h-7V30l-11 14-11-14v16z' fill='%23FACC15'/%3E%3C/svg%3E" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/site.css" />
<link rel="stylesheet" href="/assets/blog.css" />
{ld}
</head>
<body>
{sprite}
{header_ext}
<main>
{body}
</main>
{footer_ext}
{floaters}
{PAGE_JS}
</body>
</html>
"""

ORG = {"@type": "Organization", "name": "Mega Motos Paraíso", "url": BASE + "/",
       "logo": BASE + "/assets/logo/logo.png"}

def card(p):
    return f"""<a class="post-card" href="/blog/{p['slug']}/">
  <span class="post-card-img"><img src="{p['img']}" alt="{esc(p['img_alt'])}" loading="lazy" /></span>
  <span class="post-card-body">
    <span class="post-cat">{esc(p['cat'])} · {p['read']} min de leitura</span>
    <strong>{esc(p['title'])}</strong>
    <span class="post-excerpt">{esc(p['desc'])}</span>
    <span class="post-more">Ler artigo <svg width="16" height="16"><use href="#i-arrow"/></svg></span>
  </span>
</a>"""

# ---------- artigos ----------
for i, p in enumerate(POSTS):
    url = f"{BASE}/blog/{p['slug']}/"
    others = [POSTS[(i + k) % len(POSTS)] for k in (1, 2, 3)]
    faq_html = "".join(f"<details><summary>{esc(q)}<i></i></summary><p>{esc(a)}</p></details>" for q, a in p["faq"])
    body = f"""
<article class="post">
  <div class="wrap post-wrap">
    <nav class="crumbs" aria-label="Você está em"><a href="/">Início</a><span>/</span><a href="/blog/">Blog</a><span>/</span><span>{esc(p['cat'])}</span></nav>
    <header class="post-head">
      <span class="eyebrow">{esc(p['cat'])}</span>
      <h1>{esc(p['title'])}</h1>
      <p class="post-meta">Por Equipe Mega Motos · <time datetime="{DATE}">{DATE_BR}</time> · {p['read']} min de leitura</p>
    </header>
    <figure class="post-cover"><img src="{p['img']}" alt="{esc(p['img_alt'])}" /></figure>
    <div class="prose">
      {p['body'].strip()}
      <aside class="post-cta">
        <div><strong>Precisa de ajuda com isso?</strong><span>Fale com a Mega Motos. São duas lojas em Paraíso do Tocantins: Centro e Saída p/ Divinópolis.</span></div>
        <a class="btn btn-accent" href="{wa(p['wa'])}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg> Chamar no WhatsApp</a>
      </aside>
      <h2>Perguntas frequentes</h2>
      <div class="post-faq">{faq_html}</div>
    </div>
  </div>
</article>
<section class="related">
  <div class="wrap">
    <h2>Leia também</h2>
    <div class="post-grid">{''.join(card(q) for q in others)}</div>
  </div>
</section>"""
    jsonld = [
        {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "description": p["desc"],
         "image": BASE + p["img"], "datePublished": DATE, "dateModified": DATE, "inLanguage": "pt-BR",
         "author": ORG, "publisher": ORG, "mainEntityOfPage": url},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": url}]},
    ]
    out = os.path.join(REPO, "blog", p["slug"]); os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(
        page(p["title"] + " | Mega Motos Paraíso", p["desc"], url, body, jsonld, og_img=p["img"], og_type="article"))

# ---------- índice do blog ----------
blog_url = BASE + "/blog/"
blog_body = f"""
<section class="blog-hero">
  <div class="wrap">
    <nav class="crumbs" aria-label="Você está em"><a href="/">Início</a><span>/</span><span>Blog</span></nav>
    <span class="eyebrow">Blog Mega Motos</span>
    <h1>Dicas de manutenção e segurança para a sua moto.</h1>
    <p>Guias práticos escritos pela equipe da oficina Mega Motos, em Paraíso do Tocantins, sobre óleo, pneus, freios, kit relação, capacete e muito mais.</p>
  </div>
</section>
<section class="blog-list">
  <div class="wrap"><div class="post-grid">{''.join(card(p) for p in POSTS)}</div></div>
</section>"""
blog_ld = [{"@context": "https://schema.org", "@type": "Blog", "name": "Blog Mega Motos Paraíso", "url": blog_url,
            "inLanguage": "pt-BR", "publisher": ORG,
            "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": f"{BASE}/blog/{p['slug']}/",
                          "datePublished": DATE} for p in POSTS]}]
os.makedirs(os.path.join(REPO, "blog"), exist_ok=True)
open(os.path.join(REPO, "blog", "index.html"), "w", encoding="utf-8").write(
    page("Blog Mega Motos | Dicas de manutenção de moto em Paraíso do Tocantins",
         "Dicas de manutenção, segurança e peças para motos, da oficina Mega Motos em Paraíso do Tocantins: óleo, pneus, freios, kit relação, capacete e injeção.",
         blog_url, blog_body, blog_ld))

# ---------- home: link "Blog", seção de dicas, canonical e dados da empresa ----------
s = idx
if 'href="/blog/"' not in s:
    s = s.replace('<a href="#duvidas">Dúvidas</a>\n    </nav>', '<a href="#duvidas">Dúvidas</a>\n      <a href="/blog/">Blog</a>\n    </nav>', 1)
    s = s.replace('<a href="#duvidas">Dúvidas</a>\n    <a class="btn btn-dark"', '<a href="#duvidas">Dúvidas</a>\n    <a href="/blog/">Blog</a>\n    <a class="btn btn-dark"', 1)
    s = s.replace('<li><a href="#orcamento">Orçamento</a></li>', '<li><a href="#orcamento">Orçamento</a></li>\n          <li><a href="/blog/">Blog</a></li>', 1)
home_tips = f"""<!-- BLOG-HOME:start -->
  <section id="dicas" style="padding-top:0">
    <div class="wrap">
      <div class="section-head reveal">
        <div><span class="eyebrow">Blog</span><h2>Dicas da oficina.</h2></div>
        <p>Guias rápidos para cuidar da sua moto e rodar com segurança em Paraíso e região. <a href="/blog/" style="font-weight:600;text-decoration:underline;text-underline-offset:3px">Ver todos os artigos</a></p>
      </div>
      <div class="post-grid">{''.join(card(p) for p in POSTS[:3])}</div>
    </div>
  </section>
  <!-- BLOG-HOME:end -->"""
s = re.sub(r'<!-- BLOG-HOME:start -->.*?<!-- BLOG-HOME:end -->', '', s, flags=re.S)
s = s.replace('  <!-- FAQ -->', home_tips + '\n\n  <!-- FAQ -->', 1)
if '/assets/blog.css' not in s:
    s = s.replace('<link rel="stylesheet" href="/assets/site.css" />', '<link rel="stylesheet" href="/assets/site.css" />\n<link rel="stylesheet" href="/assets/blog.css" />', 1)
if 'rel="canonical"' not in s:
    s = s.replace('<meta name="theme-color"', f'<link rel="canonical" href="{BASE}/" />\n<meta name="theme-color"', 1)
biz = {"@context": "https://schema.org", "@type": "AutoPartsStore", "name": "Mega Motos Paraíso", "url": BASE + "/",
       "logo": BASE + "/assets/logo/logo.png", "image": BASE + "/assets/loja/loja_interior_hd.jpg", "foundingDate": "1997",
       "sameAs": ["https://www.instagram.com/megamotospso/"],
       "department": [
        {"@type": "MotorcycleRepair", "name": "Mega Motos – Loja 1 (Centro)", "telephone": "+55-63-3602-1643",
         "email": "megamotospso@gmail.com",
         "address": {"@type": "PostalAddress", "streetAddress": "Av. Marechal Castelo Branco, 1475", "addressLocality": "Paraíso do Tocantins", "addressRegion": "TO", "postalCode": "77600-000", "addressCountry": "BR"},
         "openingHours": ["Mo-Fr 07:00-18:00", "Sa 07:00-12:00"]},
        {"@type": "MotorcycleRepair", "name": "Mega Motos – Loja 2 (Saída para Divinópolis)", "telephone": "+55-63-3142-1643",
         "email": "megamotospso2@gmail.com",
         "address": {"@type": "PostalAddress", "streetAddress": "Av. Bernardo Sayão, 2601", "addressLocality": "Paraíso do Tocantins", "addressRegion": "TO", "addressCountry": "BR"},
         "openingHours": ["Mo-Fr 07:00-18:00", "Sa 07:00-12:00"]}]}
s = re.sub(r'<script type="application/ld\+json" id="biz">.*?</script>\n?', '', s, flags=re.S)
s = s.replace('</head>', f'<script type="application/ld+json" id="biz">{json.dumps(biz, ensure_ascii=False)}</script>\n</head>', 1)
open(idx_path, "w", encoding="utf-8").write(s)

# ---------- sitemap e robots ----------
urls = [(BASE + "/", "weekly", "1.0"), (blog_url, "weekly", "0.8")] + [(f"{BASE}/blog/{p['slug']}/", "monthly", "0.7") for p in POSTS]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
    f"  <url><loc>{u}</loc><lastmod>{DATE}</lastmod><changefreq>{c}</changefreq><priority>{pr}</priority></url>\n" for u, c, pr in urls) + "</urlset>\n"
open(os.path.join(REPO, "sitemap.xml"), "w", encoding="utf-8").write(sm)
open(os.path.join(REPO, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
print("ok:", len(POSTS), "artigos")
