# -*- coding: utf-8 -*-
"""Gera a aba "Loja" do site da Mega Motos a partir de tools/produtos.csv.
Uso: python tools/build_loja.py <pasta-do-repo>
- Cria /loja/ (vitrine com filtros e busca) e /loja/<produto>/ (página de cada produto).
- Atualiza a seção "Produtos" da home (só os marcados como destaque), o menu e o sitemap.
- A compra é pelo WhatsApp da Loja 1: o botão abre a conversa com a mensagem pronta.
É idempotente: edite o CSV e rode de novo. Depois rode tools/build_blog.py para o menu do blog."""
import sys, os, re, csv, json, html, shutil, unicodedata, urllib.parse

REPO = sys.argv[1]
BASE = "https://megamotos.dluz.com.br"
WA1 = "556336021643"   # Loja 1 (Centro): foco do contrato
WA2 = "556331421643"   # Loja 2

esc = lambda s: html.escape(str(s or ""), quote=True)
def slug(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:80] or "produto"
def wa(text, fone=WA1): return f"https://wa.me/{fone}?text=" + urllib.parse.quote(text)
def reais(v): return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def num(s):
    s = str(s or "").replace("R$", "").strip()
    if not s: return None
    if "," in s: s = s.replace(".", "").replace(",", ".")
    try: return float(s)
    except ValueError: return None
sim = lambda s: str(s or "").strip().lower() in ("sim", "s", "1", "x", "yes")

# ---------- produtos ----------
with open(os.path.join(REPO, "tools", "produtos.csv"), encoding="utf-8-sig") as f:
    linhas = list(csv.DictReader(f, delimiter=";"))
PRODS, vistos = [], set()
for l in linhas:
    l = {k.strip(): (v or "").strip() for k, v in l.items() if k}
    if not l.get("nome") or not sim(l.get("ativo", "sim")): continue
    s = base = slug(l["nome"]); n = 2
    while s in vistos: s = f"{base}-{n}"; n += 1
    vistos.add(s)
    PRODS.append({**l, "slug": s, "cat_slug": slug(l.get("categoria") or "outros"),
                  "preco_n": num(l.get("preco")), "antigo_n": num(l.get("preco_antigo")),
                  "destaque_b": sim(l.get("destaque"))})
CATS = []
for p in PRODS:
    if p["categoria"] and p["categoria"] not in CATS: CATS.append(p["categoria"])
MOTOS = sorted({m.strip() for p in PRODS for m in re.split(r"[,;/]", p.get("motos", "")) if m.strip() and len(m.strip()) < 30 and not m.strip().lower().startswith(("aro", "tamanho"))}, key=str.lower)

def msg_compra(p):
    preco = f" ({reais(p['preco_n'])})" if p["preco_n"] else ""
    return f"Olá, Mega Motos! Quero comprar: {p['nome']}{preco}. Vi na loja do site: {BASE}/loja/{p['slug']}/"
def msg_duvida(p): return f"Olá! Esse produto serve na minha moto? {p['nome']} ({BASE}/loja/{p['slug']}/). Minha moto é: "

def preco_html(p, grande=False):
    cls = "loja-preco" + (" g" if grande else "")
    if not p["preco_n"]:
        return f'<span class="{cls}"><b class="consulta">Preço no WhatsApp</b></span>'
    antigo = f'<s>{reais(p["antigo_n"])}</s>' if p["antigo_n"] and p["antigo_n"] > p["preco_n"] else ""
    return f'<span class="{cls}">{antigo}<b>{reais(p["preco_n"])}</b></span>'

# ---------- home: menu e seção Produtos ----------
idx_path = os.path.join(REPO, "index.html")
idx = open(idx_path, encoding="utf-8").read()
idx = idx.replace('<a href="#produtos">Produtos</a>', '<a href="/loja/">Loja</a>', 1)
if '<a href="/loja/">Loja</a>\n    <a href="#orcamento">' not in idx:
    idx = idx.replace('<a href="#produtos">Peças e pneus</a>\n    <a href="#orcamento">', '<a href="#produtos">Peças e pneus</a>\n    <a href="/loja/">Loja</a>\n    <a href="#orcamento">', 1)
if '<li><a href="/loja/">Loja</a></li>' not in idx:
    idx = idx.replace('<li><a href="#produtos">Peças e pneus</a></li>', '<li><a href="#produtos">Peças e pneus</a></li>\n          <li><a href="/loja/">Loja</a></li>', 1)
if '/assets/loja.css' not in idx:
    idx = idx.replace('<link rel="stylesheet" href="/assets/site.css" />', '<link rel="stylesheet" href="/assets/site.css" />\n<link rel="stylesheet" href="/assets/loja.css" />', 1)

def card(p, img_prefix="/"):
    return f"""<article class="product" data-cat="{p['cat_slug']}" data-busca="{esc((p['nome'] + ' ' + p.get('marca','') + ' ' + p.get('categoria','') + ' ' + p.get('motos','')).lower())}" data-motos="{esc(p.get('motos','').lower())}">
          <a class="product-img" href="/loja/{p['slug']}/">{f'<img src="{esc(p["foto"])}" alt="{esc(p["nome"])}" loading="lazy" />' if p.get('foto') else ''}</a>
          <div class="product-body">
            <span class="product-cat">{esc(p['categoria'])}</span>
            <h3><a href="/loja/{p['slug']}/">{esc(p['nome'])}</a></h3>
            {f'<p>{esc(p["motos"])}</p>' if p.get('motos') else ''}
            <div class="product-foot loja-foot">{preco_html(p)}{f'<small>{esc(p["selo"])}</small>' if p.get('selo') and p['selo'] != p.get('motos') else ''}</div>
            <a class="loja-comprar" href="{esc(wa(msg_compra(p)))}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg> Comprar<span class="lc-longo">&nbsp;no WhatsApp</span></a>
          </div>
        </article>"""

def chips(cats, home=False):
    return '<button class="chip active" data-filter="todos">Todos</button>' + "".join(
        f'<button class="chip" data-filter="{slug(c)}">{esc(c)}</button>' for c in cats)

destaques = [p for p in PRODS if p["destaque_b"]][:8] or PRODS[:8]
home_cats = [c for c in CATS if any(p["categoria"] == c for p in destaques)]
home_sec = f"""<!-- LOJA-HOME:start -->
  <section id="produtos">
    <div class="wrap">
      <div class="section-head reveal">
        <div>
          <span class="eyebrow">Loja</span>
          <h2>Peças, pneus e acessórios.</h2>
        </div>
        <p>Mais de 15.000 itens para todas as marcas. Escolha aqui e finalize a compra pelo WhatsApp: a gente confirma o estoque e você retira na Loja 1, no Centro. <a href="/loja/" style="font-weight:600;text-decoration:underline;text-underline-offset:3px">Ver a loja completa</a></p>
      </div>

      <div class="filters reveal" role="group" aria-label="Filtrar produtos">
        {chips(home_cats, True)}
      </div>

      <div class="products" id="products">
        {''.join(card(p) for p in destaques)}
      </div>

      <div class="stock-cta reveal">
        <div><strong>Não achou o que procurava?</strong><span>São mais de 15.000 peças no sistema das duas lojas. Veja a loja completa ou pergunte ao balcão.</span></div>
        <div class="loja-cta-acoes"><a class="btn btn-accent" href="/loja/">Ver a loja <svg><use href="#i-arrow"/></svg></a><a class="btn btn-dark" href="{esc(wa('Olá, estou procurando uma peça específica para minha moto.'))}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg> Consultar estoque</a></div>
      </div>
    </div>
  </section>
  <!-- LOJA-HOME:end -->"""
if "<!-- LOJA-HOME:start -->" in idx:
    idx = re.sub(r"<!-- LOJA-HOME:start -->.*?<!-- LOJA-HOME:end -->", lambda m: home_sec, idx, flags=re.S)
else:
    idx = re.sub(r'<section id="produtos">.*?</section>', lambda m: home_sec, idx, count=1, flags=re.S)
open(idx_path, "w", encoding="utf-8").write(idx)

# ---------- pedaços reaproveitados da home (depois do menu atualizado) ----------
def between(s, start, end, include_end=True):
    a = s.index(start); b = s.index(end, a) + (len(end) if include_end else 0)
    return s[a:b]
sprite = between(idx, '<svg width="0" height="0"', '</svg>\n\n<header', include_end=False)
header = between(idx, '<header id="top">', '</header>')
footer = between(idx, '<footer class="site-footer">', '</footer>')
floaters = between(idx, '<a class="wa-float"', '</div>\n\n<script>', include_end=False) + '</div>'
def externalize(block):
    block = re.sub(r'href="#(?!i-)top"', 'href="/"', block)
    block = re.sub(r'href="#(?!i-)([a-z]+)"', r'href="/#\1"', block)
    return block.replace('src="assets/', 'src="/assets/')
header_ext, footer_ext = externalize(header), externalize(footer)

PAGE_JS = """<script>
  const header=document.querySelector('header');const onScroll=()=>header.classList.toggle('scrolled',scrollY>8);addEventListener('scroll',onScroll,{passive:true});onScroll();
  const mb=document.getElementById('menuBtn'),mm=document.getElementById('mobileMenu');mb.addEventListener('click',()=>{const o=mm.classList.toggle('open');mb.setAttribute('aria-expanded',o)});
  const y=document.getElementById('year');if(y)y.textContent=new Date().getFullYear();
</script>"""
FILTRO_JS = """<script>
(function(){
  const cards=[...document.querySelectorAll('.loja-grade .product')],chips=[...document.querySelectorAll('.loja-filtros .chip')];
  const busca=document.getElementById('lojaBusca'),moto=document.getElementById('lojaMoto'),vazio=document.getElementById('lojaVazio'),cont=document.getElementById('lojaCont');
  let cat='todos';
  const norm=s=>s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
  function aplicar(){
    const q=norm(busca.value.trim()),m=moto?norm(moto.value):'';let n=0;
    cards.forEach(c=>{const ok=(cat==='todos'||c.dataset.cat===cat)&&(!q||q.split(/\\s+/).every(t=>norm(c.dataset.busca).includes(t)))&&(!m||!c.dataset.motos||norm(c.dataset.motos).includes(m));c.classList.toggle('hide',!ok);if(ok)n++;});
    vazio.hidden=n>0;cont.textContent=n+(n===1?' produto':' produtos');
  }
  chips.forEach(ch=>ch.addEventListener('click',()=>{cat=ch.dataset.filter;chips.forEach(c=>c.classList.toggle('active',c===ch));aplicar();}));
  busca.addEventListener('input',aplicar);if(moto)moto.addEventListener('change',aplicar);
  const q=new URLSearchParams(location.search).get('q');if(q){busca.value=q;}aplicar();
})();
</script>"""

def page(title, desc, canonical, body, jsonld, og_img="/assets/loja/loja_interior_hd.jpg", extra_js=""):
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
<meta property="og:type" content="website" />
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
<link rel="stylesheet" href="/assets/loja.css" />
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
{extra_js}
</body>
</html>
"""

COMO = f"""<ol class="loja-passos">
  <li><b>1</b><span><strong>Escolha o produto</strong>Na dúvida se serve, pergunte antes.</span></li>
  <li><b>2</b><span><strong>Toque em “Comprar no WhatsApp”</strong>A mensagem já vai pronta para a Loja 1.</span></li>
  <li><b>3</b><span><strong>Combine pagamento e retirada</strong>A loja confirma o estoque. Retire no Centro ou combine a entrega.</span></li>
</ol>"""

# ---------- limpa e recria /loja ----------
loja_dir = os.path.join(REPO, "loja")
if os.path.isdir(loja_dir): shutil.rmtree(loja_dir)
os.makedirs(loja_dir)

loja_url = f"{BASE}/loja/"
motos_sel = ("<label class=\"loja-moto\"><span>Para qual moto?</span><select id=\"lojaMoto\"><option value=\"\">Todas</option>"
             + "".join(f"<option>{esc(m)}</option>" for m in MOTOS) + "</select></label>") if len(MOTOS) >= 3 else ""
loja_body = f"""
<section class="blog-hero loja-hero">
  <div class="wrap">
    <nav class="crumbs" aria-label="Você está em"><a href="/">Início</a><span>/</span><span>Loja</span></nav>
    <span class="eyebrow">Loja Mega Motos</span>
    <h1>Peças e acessórios para a sua moto.</h1>
    <p>Escolha aqui e compre pelo WhatsApp. A gente confirma o estoque, combina o pagamento e você retira na Loja 1, no Centro de Paraíso do Tocantins.</p>
    {COMO}
  </div>
</section>
<section class="loja-lista">
  <div class="wrap">
    <div class="loja-ferramentas">
      <label class="loja-busca"><span class="sr-only">Buscar produto</span><input id="lojaBusca" type="search" placeholder="Buscar peça, marca ou moto" autocomplete="off" /></label>
      {motos_sel}
    </div>
    <div class="filters loja-filtros" role="group" aria-label="Filtrar por categoria">{chips(CATS)}</div>
    <p class="loja-cont" id="lojaCont">{len(PRODS)} produtos</p>
    <div class="products loja-grade">
      {''.join(card(p) for p in PRODS)}
    </div>
    <div class="stock-cta" id="lojaVazio" hidden>
      <div><strong>Não achamos isso na loja do site.</strong><span>São mais de 15.000 peças nas duas lojas. Pergunte no WhatsApp.</span></div>
      <a class="btn btn-dark" href="{esc(wa('Olá, estou procurando uma peça para minha moto: '))}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg> Perguntar</a>
    </div>
    <div class="stock-cta loja-rodape-cta">
      <div><strong>Não achou a peça?</strong><span>Mande o modelo e o ano da moto que a gente confere no estoque das duas lojas.</span></div>
      <a class="btn btn-dark" href="{esc(wa('Olá! Estou procurando uma peça. Minha moto (modelo e ano): '))}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg> Chamar no WhatsApp</a>
    </div>
  </div>
</section>"""
loja_ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Loja Mega Motos", "url": loja_url, "inLanguage": "pt-BR",
            "mainEntity": {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "url": f"{BASE}/loja/{p['slug']}/", "name": p["nome"]} for i, p in enumerate(PRODS)]}}]
open(os.path.join(loja_dir, "index.html"), "w", encoding="utf-8").write(
    page("Loja Mega Motos | Peças, pneus e acessórios de moto em Paraíso do Tocantins",
         "Peças, pneus, óleo, capacetes e acessórios de moto da Mega Motos. Escolha no site, compre pelo WhatsApp e retire na loja em Paraíso do Tocantins/TO.",
         loja_url, loja_body, loja_ld, extra_js=FILTRO_JS))

for p in PRODS:
    url = f"{BASE}/loja/{p['slug']}/"
    rel = [q for q in PRODS if q is not p and q["categoria"] == p["categoria"]][:4]
    if len(rel) < 4: rel += [q for q in PRODS if q is not p and q not in rel][:4 - len(rel)]
    body = f"""
<section class="loja-prod">
  <div class="wrap">
    <nav class="crumbs" aria-label="Você está em"><a href="/">Início</a><span>/</span><a href="/loja/">Loja</a><span>/</span><span>{esc(p['categoria'])}</span></nav>
    <div class="loja-prod-grid">
      <figure class="loja-prod-foto">{f'<img src="{esc(p["foto"])}" alt="{esc(p["nome"])}" />' if p.get('foto') else ''}</figure>
      <div class="loja-prod-info">
        <span class="eyebrow">{esc(p['categoria'])}{(' · ' + esc(p['marca'])) if p.get('marca') else ''}</span>
        <h1>{esc(p['nome'])}</h1>
        {f'<p class="loja-serve"><strong>Serve em:</strong> {esc(p["motos"])}</p>' if p.get('motos') else ''}
        {preco_html(p, True)}
        {f'<p class="loja-selo">{esc(p["selo"])}</p>' if p.get('selo') and p['selo'] != p.get('motos') else ''}
        <a class="btn btn-accent loja-btn-g" href="{esc(wa(msg_compra(p)))}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg> Comprar no WhatsApp</a>
        <a class="btn btn-ghost loja-btn-g" href="{esc(wa(msg_duvida(p)))}" target="_blank" rel="noopener">Perguntar se serve na minha moto</a>
        {f'<div class="loja-desc"><h2>Sobre o produto</h2><p>{esc(p["descricao"])}</p></div>' if p.get('descricao') else ''}
        <ul class="loja-garantias">
          <li>Retire na <b>Loja 1</b>: Av. Marechal Castelo Branco, 1475, Centro</li>
          <li>Também na <b>Loja 2</b>: Av. Bernardo Sayão, 2601 (a loja confirma se a peça está lá)</li>
          <li>Pagamento e entrega combinados pelo WhatsApp</li>
          <li>A oficina instala, se você quiser</li>
        </ul>
      </div>
    </div>
  </div>
</section>
<section class="related">
  <div class="wrap">
    <h2>Veja também</h2>
    <div class="products">{''.join(card(q) for q in rel)}</div>
  </div>
</section>"""
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Início", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Loja", "item": loja_url},
        {"@type": "ListItem", "position": 3, "name": p["nome"], "item": url}]}]
    if p["preco_n"]:
        ld.append({"@context": "https://schema.org", "@type": "Product", "name": p["nome"], "description": p.get("descricao") or p["nome"],
                   **({"image": BASE + p["foto"]} if p.get("foto") else {}), **({"brand": {"@type": "Brand", "name": p["marca"]}} if p.get("marca") else {}),
                   "offers": {"@type": "Offer", "url": url, "priceCurrency": "BRL", "price": f"{p['preco_n']:.2f}",
                              "availability": "https://schema.org/InStock", "seller": {"@type": "Organization", "name": "Mega Motos Paraíso"}}})
    desc = f"{p['nome']}{(' para ' + p['motos']) if p.get('motos') else ''}{(' por ' + reais(p['preco_n'])) if p['preco_n'] else ''}. Compre pelo WhatsApp e retire na Mega Motos, em Paraíso do Tocantins/TO."
    out = os.path.join(loja_dir, p["slug"]); os.makedirs(out)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(
        page(f"{p['nome']} | Loja Mega Motos Paraíso", desc, url, body, ld, og_img=p.get("foto") or "/assets/loja/loja_interior_hd.jpg"))

# ---------- sitemap: troca só as linhas da loja ----------
sm_path = os.path.join(REPO, "sitemap.xml")
sm = open(sm_path, encoding="utf-8").read()
sm = re.sub(r"  <url><loc>[^<]*/loja/[^<]*</loc>.*?</url>\n", "", sm)
novas = f"  <url><loc>{loja_url}</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>\n" + "".join(
    f"  <url><loc>{BASE}/loja/{p['slug']}/</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>\n" for p in PRODS)
sm = sm.replace("</urlset>", novas + "</urlset>")
open(sm_path, "w", encoding="utf-8").write(sm)
print("ok:", len(PRODS), "produtos,", len(CATS), "categorias")
