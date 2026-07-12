#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SiteKlonlayici v3.1 — Profesyonel Web Sitesi Klonlama Araci
Tum HTML, CSS, JS, resim, font, video dosyalarini indirir.
"""

# ── Encoding (Windows terminali icin kritik) ──────────────────────────────────
import io, sys
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "buffer"):
    sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding="utf-8", errors="replace")

# ── Otomatik kurulum ──────────────────────────────────────────────────────────
def _pip(pkg):
    import subprocess
    print(f"  Kuruluyor: {pkg}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for _mod, _pkg in [("requests","requests"),("bs4","beautifulsoup4"),
                   ("lxml","lxml"),("colorama","colorama"),("tqdm","tqdm")]:
    try: __import__(_mod)
    except ImportError: _pip(_pkg)

# ── Kutuphaneler ──────────────────────────────────────────────────────────────
import os, re, time, threading, tempfile, webbrowser, subprocess, queue
from pathlib      import Path
from datetime     import datetime
from urllib.parse import urljoin, urlparse, urlunparse

import requests, urllib3
import colorama
from colorama import Fore, Style
from bs4      import BeautifulSoup
from tqdm     import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
colorama.init(autoreset=True)

# ── Renkler ───────────────────────────────────────────────────────────────────
R, G, Y, B, C, M, W = (Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE,
                        Fore.CYAN, Fore.MAGENTA, Fore.WHITE)
DIM, BRT, RST = Style.DIM, Style.BRIGHT, Style.RESET_ALL
VER = "3.1"

BANNER = f"""{C}{BRT}
  ██████╗ ██╗████████╗███████╗    ██╗  ██╗██╗      ██████╗ ███╗   ██╗
  ██╔════╝ ██║╚══██╔══╝██╔════╝    ██║ ██╔╝██║     ██╔═══██╗████╗  ██║
  ███████╗ ██║   ██║   █████╗      █████╔╝ ██║     ██║   ██║██╔██╗ ██║
  ╚════██║ ██║   ██║   ██╔══╝      ██╔═██╗ ██║     ██║   ██║██║╚██╗██║
  ███████║ ██║   ██║   ███████╗    ██║  ██╗███████╗╚██████╔╝██║ ╚████║
  ╚══════╝ ╚═╝   ╚═╝   ╚══════╝    ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝{RST}
{W}{BRT}  ╔══════════════════════════════════════════════════════════════════╗
  ║   Profesyonel Web Sitesi Klonlama Sistemi  v{VER:<6}               ║
  ║   HTML · CSS · JS · Resim · Font · Video · PDF · JSON         ║
  ╚══════════════════════════════════════════════════════════════════╝{RST}
"""

# ── UI yardimcilari ───────────────────────────────────────────────────────────
def cls():
    os.system("cls" if os.name == "nt" else "clear")

def sep(ch="─", w=70, color=C):
    print(f"{color}{ch * w}{RST}")

def info(m):    print(f"  {C}[*]{RST} {m}")
def ok(m):      print(f"  {G}[v]{RST} {m}")
def warn(m):    print(f"  {Y}[!]{RST} {m}")
def err(m):     print(f"  {R}[x]{RST} {m}")
def step(n, m): print(f"\n  {M}{BRT}[ ADIM {n} ]{RST}  {W}{BRT}{m}{RST}")

def prompt(msg, default=None):
    hint = f" [{default}]" if default is not None else ""
    sys.stdout.write(f"\n  {C}> {RST}{W}{msg}{hint}: {C}")
    sys.stdout.flush()
    try:
        raw = sys.stdin.readline()
    except Exception:
        raw = ""
    sys.stdout.write(RST)
    val = raw.strip()
    return val if val else (str(default) if default is not None else "")

def ask_yn(msg, default="e"):
    val = prompt(msg + " [E/h]", default=default).lower()
    return val not in ("h", "hayir", "n", "no")

# ── Spinner ───────────────────────────────────────────────────────────────────
class Spinner:
    FR = ["|", "/", "-", "\\"]
    def __init__(self, msg):
        self.msg   = msg
        self._stop = threading.Event()
        self._t    = threading.Thread(target=self._run, daemon=True)
    def _run(self):
        i = 0
        while not self._stop.is_set():
            sys.stdout.write(f"\r  {C}{self.FR[i%4]}{RST}  {self.msg}...  ")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
    def start(self): self._t.start(); return self
    def stop(self, msg=""):
        self._stop.set(); self._t.join()
        sys.stdout.write("\r" + " "*74 + "\r")
        sys.stdout.flush()
        if msg: ok(msg)

# ── URL araclari ──────────────────────────────────────────────────────────────
_WIN_ILLEGAL = re.compile(r'[<>:"|?*\x00-\x1f]')

def normalize_url(u):
    u = u.strip().rstrip("/")
    if not u.startswith(("http://","https://")):
        u = "https://" + u
    return u

def clean_url(url):
    """Fragment (#...) ve bazi izleme parametrelerini cikar"""
    p = urlparse(url)
    return urlunparse(p._replace(fragment=""))

def same_domain(url, base):
    try:
        return urlparse(url).netloc.lstrip("www.") == urlparse(base).netloc.lstrip("www.")
    except Exception:
        return False

def url_to_local(url, dest: Path) -> Path:
    p    = urlparse(url)
    path = p.path.lstrip("/") or "index.html"
    if path.endswith("/"):
        path += "index.html"
    if p.query:
        safe_q = re.sub(r"[^\w\-]", "_", p.query)[:20]
        root, ext = os.path.splitext(path)
        path = f"{root}__{safe_q}{ext}"
    # Windows icin guvenli hale getir
    segs  = [_WIN_ILLEGAL.sub("_", s) for s in path.split("/")]
    return dest.joinpath(*segs)

# ── MIME → uzanti tablosu ─────────────────────────────────────────────────────
MIME_EXT = {
    "text/html":".html","text/css":".css","text/plain":".txt",
    "text/xml":".xml","text/csv":".csv",
    "application/javascript":".js","text/javascript":".js",
    "application/json":".json","application/xml":".xml",
    "image/jpeg":".jpg","image/png":".png","image/gif":".gif",
    "image/svg+xml":".svg","image/webp":".webp","image/avif":".avif",
    "image/x-icon":".ico","image/vnd.microsoft.icon":".ico",
    "font/woff":".woff","font/woff2":".woff2",
    "font/ttf":".ttf","font/otf":".otf",
    "application/font-woff":".woff","application/font-woff2":".woff2",
    "application/x-font-ttf":".ttf",
    "video/mp4":".mp4","video/webm":".webm","video/ogg":".ogv",
    "audio/mpeg":".mp3","audio/ogg":".ogg","audio/wav":".wav",
    "application/pdf":".pdf","application/zip":".zip",
}

def guess_ext(ct):
    return MIME_EXT.get(ct.split(";")[0].strip().lower(), "")

# ── CSS varlik tarayici ───────────────────────────────────────────────────────
_CSS_RE = re.compile(
    r'''url\(\s*['"]?([^'"\)\s]+)['"]?\s*\)|@import\s+['"]([^'"]+)['"]''', re.I
)

def css_assets(text, base):
    out = set()
    for m in _CSS_RE.finditer(text):
        raw = (m.group(1) or m.group(2) or "").strip()
        if raw and not raw.startswith("data:"):
            out.add(urljoin(base, raw))
    return out

# ── HTML varlik + sayfa tarayici ─────────────────────────────────────────────
_SRCSET_RE = re.compile(r'([^\s,]+)(?:\s+[\d.]+[wx])?')

_ASSET_TAGS = {
    "link":   ["href"],
    "script": ["src"],
    "img":    ["src","data-src","data-original","data-lazy","data-lazy-src","data-bg"],
    "source": ["src","srcset"],
    "video":  ["src","poster"],
    "audio":  ["src"],
    "iframe": ["src"],
    "embed":  ["src"],
    "object": ["data"],
    "input":  ["src"],
}
_SKIP_PREFIXES = ("data:","javascript:","#","mailto:","tel:")

def _add_url(s, url, base):
    url = url.strip()
    if url and not url.startswith(_SKIP_PREFIXES):
        full = urljoin(base, url)
        if full.startswith("http"):
            s.add(clean_url(full))

def extract_links(soup: BeautifulSoup, page_url, base_url):
    assets = set()
    pages  = set()

    # <a href>
    for tag in soup.find_all("a", href=True):
        href = urljoin(page_url, tag["href"].strip()).split("#")[0]
        if href.startswith("http") and same_domain(href, base_url):
            pages.add(href.rstrip("/"))

    # Varlik etiketleri
    for tag_name, attrs in _ASSET_TAGS.items():
        for tag in soup.find_all(tag_name):
            for attr in attrs:
                val = tag.get(attr,"") or ""
                if not val:
                    continue
                if attr == "srcset":
                    for m in _SRCSET_RE.finditer(val):
                        _add_url(assets, m.group(1), page_url)
                else:
                    _add_url(assets, val, page_url)

    # og:image / twitter:image meta etiketleri
    for tag in soup.find_all("meta"):
        prop = (tag.get("property","") + tag.get("name","")).lower()
        if "image" in prop or "url" in prop:
            content = tag.get("content","") or ""
            _add_url(assets, content, page_url)

    # Inline style
    for tag in soup.find_all(style=True):
        assets |= css_assets(tag["style"], page_url)
    for tag in soup.find_all("style"):
        assets |= css_assets(tag.get_text(), page_url)

    # <script> icerisindeki URL'ler (basit)
    for tag in soup.find_all("script"):
        txt = tag.get_text()
        if not txt:
            continue
        for m in re.finditer(r'''['"]((https?:)?//[^'"<>\s]{5,})['"]''', txt):
            _add_url(assets, m.group(1), page_url)

    return assets, pages

# ── Thread-guvenli sayac ──────────────────────────────────────────────────────
class _Cnt:
    def __init__(self): self.v = 0; self.l = threading.Lock()
    def inc(self, n=1):
        with self.l: self.v += n; return self.v
    @property
    def value(self): return self.v

# ── Boyut formatla ────────────────────────────────────────────────────────────
def fmtb(b):
    b = float(b)
    for u in ("B","KB","MB","GB"):
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

# ── KLONLAYICI ────────────────────────────────────────────────────────────────
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/125.0.0.0 Safari/537.36")

class Klonlayici:
    def __init__(self, base_url, dest: Path,
                 max_depth=3, max_pages=500,
                 workers=12, timeout=15):
        self.base_url  = base_url
        self.dest      = dest
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.workers   = workers
        self.timeout   = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.7",
        })
        self.session.verify = False
        self.session.max_redirects = 10

        self._lock           = threading.Lock()
        self._visited_pages  = set()
        self._visited_assets = set()

        self.c_pages  = _Cnt()
        self.c_assets = _Cnt()
        self.c_bytes  = _Cnt()
        self.c_failed = _Cnt()
        self.failed   = []           # [(url, reason)]

        # progress bar (None iken hic update etme)
        self._pbar       = None
        self._pbar_lock  = threading.Lock()

    # ── HTTP GET ─────────────────────────────────────────────────────────────
    def _get(self, url, stream=False):
        try:
            r = self.session.get(url, timeout=self.timeout,
                                 stream=stream, allow_redirects=True)
            r.raise_for_status()
            return r
        except Exception as ex:
            self.c_failed.inc()
            with self._lock:
                self.failed.append((url, str(ex)[:120]))
            return None

    # ── Diske kaydet ─────────────────────────────────────────────────────────
    def _save(self, fp: Path, data: bytes):
        try:
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(data)
        except Exception:
            pass

    # ── Ilerleme guncelle ────────────────────────────────────────────────────
    def _tick(self, n=1):
        with self._pbar_lock:
            if self._pbar is None:
                return
            try:
                self._pbar.update(n)
                self._pbar.set_postfix(
                    sayfa  = self.c_pages.value,
                    dosya  = self.c_assets.value,
                    hata   = self.c_failed.value,
                    boyut  = fmtb(self.c_bytes.value),
                    refresh= False,
                )
            except Exception:
                pass

    # ── Varlik indirici ───────────────────────────────────────────────────────
    def _dl_asset(self, url: str):
        # Tekrar kontrolu
        with self._lock:
            if url in self._visited_assets:
                return
            self._visited_assets.add(url)

        r = self._get(url, stream=True)
        if r is None:
            return

        fp = url_to_local(url, self.dest)

        # Uzanti yoksa content-type'dan bul
        if not fp.suffix:
            ext = guess_ext(r.headers.get("content-type",""))
            fp  = fp.with_suffix(ext if ext else ".bin")

        # Veriye oku
        data = bytearray()
        try:
            for chunk in r.iter_content(1 << 16):
                if chunk:
                    data.extend(chunk)
        except Exception:
            pass

        if not data:
            return

        self._save(fp, bytes(data))
        self.c_assets.inc()
        self.c_bytes.inc(len(data))
        self._tick(0)   # sadece postfix guncelle, n=0

        # CSS → ic varliklar
        if fp.suffix.lower() == ".css":
            try:
                extra = css_assets(data.decode("utf-8","replace"), url)
                self._batch_assets(extra)
            except Exception:
                pass

    # ── Varlik grubunu thread'lerle indir ─────────────────────────────────────
    def _batch_assets(self, urls: set):
        url_list = list(urls)
        # Batch'lere bol (cok fazla thread acmaktan kacin)
        batch_sz = max(1, min(self.workers, len(url_list)))
        for i in range(0, len(url_list), batch_sz):
            batch = url_list[i:i+batch_sz]
            ts = [threading.Thread(target=self._dl_asset, args=(u,), daemon=True)
                  for u in batch]
            for t in ts: t.start()
            for t in ts: t.join()

    # ── Sayfa indirici ────────────────────────────────────────────────────────
    def _dl_page(self, url: str, depth: int):
        # Tekrar kontrolu
        with self._lock:
            if url in self._visited_pages:
                return
            if self.c_pages.value >= self.max_pages:
                return
            self._visited_pages.add(url)

        r = self._get(url)
        if r is None:
            return

        ct = r.headers.get("content-type","")

        # HTML degil → varlik gibi kaydet
        if "html" not in ct.lower():
            fp   = url_to_local(url, self.dest)
            data = r.content
            if not fp.suffix:
                fp = fp.with_suffix(guess_ext(ct) or ".bin")
            self._save(fp, data)
            self.c_assets.inc()
            self.c_bytes.inc(len(data))
            self._tick(0)
            return

        # HTML decode — encoding'i dogrudan header'dan al
        enc = "utf-8"
        ct_lower = ct.lower()
        m = re.search(r"charset=([^\s;]+)", ct_lower)
        if m:
            enc = m.group(1).strip()
        try:
            html = r.content.decode(enc, errors="replace")
        except Exception:
            html = r.content.decode("utf-8", errors="replace")

        soup = BeautifulSoup(html, "lxml")

        # Kayit yolu
        fp = url_to_local(url, self.dest)
        if not fp.suffix or fp.suffix.lower() not in (".html",".htm",".php",".asp",".aspx"):
            fp = fp.with_suffix(".html")

        # Kaydet
        self._save(fp, html.encode("utf-8", errors="replace"))
        self.c_pages.inc()
        self.c_bytes.inc(len(html))
        self._tick(1)

        # Baglantilari cikar
        assets, child_pages = extract_links(soup, url, self.base_url)

        # Varliklari indir
        self._batch_assets(assets)

        # Alt sayfalar
        if depth < self.max_depth:
            with self._lock:
                new_pages = [
                    p for p in child_pages
                    if p not in self._visited_pages
                    and same_domain(p, self.base_url)
                ]
            if new_pages:
                ts = [
                    threading.Thread(target=self._dl_page, args=(p, depth+1), daemon=True)
                    for p in new_pages
                ]
                # Batch'lerle isle
                for i in range(0, len(ts), self.workers):
                    batch = ts[i:i+self.workers]
                    for t in batch: t.start()
                    for t in batch: t.join()

    # ── Ana calistirici ───────────────────────────────────────────────────────
    def calistir(self):
        print()
        sep()
        info(f"Hedef          : {BRT}{self.base_url}{RST}")
        info(f"Maks. Derinlik : {Y}{self.max_depth}{RST}")
        info(f"Maks. Sayfa    : {Y}{self.max_pages}{RST}")
        info(f"Paralel Worker : {Y}{self.workers}{RST}")
        info(f"Kayit Yeri     : {C}{self.dest}{RST}")
        sep()
        print()

        with tqdm(
            total=None,
            desc=f"  {C}Klonlanıyor{RST}",
            unit=" s",
            dynamic_ncols=True,
            colour="cyan",
            postfix={"sayfa":0,"dosya":0,"hata":0,"boyut":"0 B"},
        ) as pbar:
            with self._pbar_lock:
                self._pbar = pbar
            self._dl_page(self.base_url, 0)
            with self._pbar_lock:
                self._pbar = None

        return {
            "pages" : self.c_pages.value,
            "assets": self.c_assets.value,
            "bytes" : self.c_bytes.value,
            "failed": self.c_failed.value,
        }

# ── Dizin bilgisi ─────────────────────────────────────────────────────────────
def dir_stats(p: Path):
    files = [f for f in p.rglob("*") if f.is_file()]
    return len(files), sum(f.stat().st_size for f in files)

def open_folder(p: Path):
    if os.name == "nt":     os.startfile(str(p))
    elif sys.platform == "darwin": subprocess.Popen(["open", str(p)])
    else:                   subprocess.Popen(["xdg-open", str(p)])

# ── Ozel ayarlar menusu ───────────────────────────────────────────────────────
def ozel_menu():
    cfg = {"depth":3,"pages":500,"workers":12,"timeout":15}
    labels = [
        ("Maks. Derinlik","depth"),
        ("Maks. Sayfa",   "pages"),
        ("Worker Sayisi", "workers"),
        ("Timeout (sn)",  "timeout"),
    ]
    while True:
        print()
        sep("-", 60, Y)
        print(f"  {W}{BRT}Ozel Ayarlar:{RST}")
        for i,(lbl,key) in enumerate(labels,1):
            print(f"  {C}[{i}]{RST} {lbl:<28} {DIM}(su an: {cfg[key]}){RST}")
        print(f"  {C}[5]{RST} Tamam")
        sep("-", 60, Y)
        s = prompt("Secim (1-5)","5")
        if s == "5": break
        try:
            idx  = int(s) - 1
            _,key = labels[idx]
            val  = prompt(f"Yeni deger ({key})")
            cfg[key] = int(val)
            ok(f"{key} = {cfg[key]}")
        except Exception:
            warn("Gecersiz giris.")
    return cfg

# ── Ana mod tablosu ───────────────────────────────────────────────────────────
MODLAR = {
    "1": {"label":"Hizli Mod",    "depth":0, "pages":1,    "workers":4,  "timeout":15},
    "2": {"label":"Standart",     "depth":3, "pages":500,  "workers":12, "timeout":15},
    "3": {"label":"Derin Tarama", "depth":5, "pages":2000, "workers":20, "timeout":20},
}

# ── ANA AKIS ──────────────────────────────────────────────────────────────────
def main():
    cls()
    print(BANNER)
    time.sleep(0.1)

    sep("=", color=M)
    print(f"  {W}{BRT}Hosgeldiniz!{RST}   {DIM}Cikmak icin Ctrl+C{RST}")
    sep("=", color=M)

    # ── ADIM 1: URL ───────────────────────────────────────────────────────────
    step(1, "Kopyalamak istediginiz sitenin URL'sini girin")
    print(f"\n  {DIM}Ornek: gamevia.pages.dev   ya da   https://www.example.com{RST}\n")
    raw = prompt("Site URL")
    while not raw:
        warn("URL bos birakilamaz!")
        raw = prompt("Site URL")
    base_url = normalize_url(raw)

    # ── ADIM 2: Erisim testi ──────────────────────────────────────────────────
    step(2, "Site erisim kontrolu yapiliyor")
    sp = Spinner(f"{base_url} adresine baglaniliyor").start()
    try:
        resp = requests.get(base_url, timeout=12, verify=False,
                            allow_redirects=True,
                            headers={"User-Agent": UA})
        final_url = clean_url(resp.url).rstrip("/")
        sp.stop(f"Baglanti OK   HTTP {resp.status_code}")
        info(f"Son URL  : {Y}{final_url}{RST}")
        info(f"Sunucu   : {Y}{resp.headers.get('Server','?')}{RST}")
        info(f"Icerik   : {Y}{resp.headers.get('Content-Type','?').split(';')[0]}{RST}")
        cl = int(resp.headers.get("Content-Length",0))
        if cl: info(f"Boyut    : {Y}{fmtb(cl)}{RST}")
        base_url = final_url
    except Exception as e:
        sp.stop()
        err(f"Baglanti hatasi: {e}")
        if not ask_yn("Yine de devam etmek istiyor musunuz?"):
            sys.exit(1)

    # ── ADIM 3: Mod ───────────────────────────────────────────────────────────
    step(3, "Klonlama modunu secin")
    print(f"""
  {C}[1]{RST}  {W}Hizli Mod{RST}     {DIM}— Anasayfa + tum varliklar (derinlik 0){RST}
  {C}[2]{RST}  {W}Standart{RST}      {DIM}— Derinlik 3, maks. 500 sayfa  {G}(Onerilen){RST}
  {C}[3]{RST}  {W}Derin Tarama{RST}  {DIM}— Derinlik 5, maks. 2000 sayfa{RST}
  {C}[4]{RST}  {W}Ozel{RST}          {DIM}— Kendi parametrelerinizi girin{RST}
""")
    mod = prompt("Mod (1-4)", "2").strip()
    if mod in MODLAR:
        m   = MODLAR[mod]
        cfg = {k:v for k,v in m.items() if k != "label"}
        ok(f"{m['label']} secildi.")
    else:
        cfg = ozel_menu()
        ok("Ozel ayarlar uygulandı.")

    # ── ADIM 4: Klasor ────────────────────────────────────────────────────────
    step(4, "Temp klasoru hazirlaniyor")
    domain   = re.sub(r"[^\w\-]","_", urlparse(base_url).netloc.lstrip("www."))[:40]
    tarih    = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest     = Path(tempfile.gettempdir()) / "SiteKlonlayici" / f"{domain}__{tarih}"
    dest.mkdir(parents=True, exist_ok=True)
    ok(f"Konum: {Y}{dest}{RST}")

    # ── ADIM 5: Klonla ────────────────────────────────────────────────────────
    step(5, "Klonlama baslıyor")
    warn("Bu islem sitenin buyuklugune gore zaman alabilir. Ctrl+C ile durdurabilirsiniz.")
    print()

    t0   = time.time()
    klon = Klonlayici(
        base_url  = base_url,
        dest      = dest,
        max_depth = cfg["depth"],
        max_pages = cfg["pages"],
        workers   = cfg["workers"],
        timeout   = cfg["timeout"],
    )
    try:
        stats = klon.calistir()
    except KeyboardInterrupt:
        print()
        warn("Kullanici tarafindan durduruldu.")
        stats = {
            "pages" : klon.c_pages.value,
            "assets": klon.c_assets.value,
            "bytes" : klon.c_bytes.value,
            "failed": klon.c_failed.value,
        }

    elapsed = time.time() - t0
    nf, sz  = dir_stats(dest)

    # ── Rapor ─────────────────────────────────────────────────────────────────
    print()
    sep("=", color=G)
    print(f"  {G}{BRT}  KLONLAMA TAMAMLANDI!{RST}")
    sep("=", color=G)
    print(f"""
  {W}Indirilen Sayfa  {RST}:  {G}{BRT}{stats['pages']}{RST}
  {W}Indirilen Varlik {RST}:  {G}{BRT}{stats['assets']}{RST}
  {W}Toplam Dosya     {RST}:  {G}{BRT}{nf}{RST}
  {W}Toplam Boyut     {RST}:  {G}{BRT}{fmtb(sz)}{RST}
  {W}Basarisiz URL    {RST}:  {(R+BRT) if stats['failed'] else (G+BRT)}{stats['failed']}{RST}
  {W}Gecen Sure       {RST}:  {Y}{BRT}{elapsed:.1f} sn{RST}
  {W}Konum            {RST}:  {C}{dest}{RST}
""")

    if stats["failed"] and klon.failed:
        warn(f"Basarisiz olan ilk {min(8,len(klon.failed))} URL:")
        for u, r_ in klon.failed[:8]:
            print(f"   {DIM}{R}-{RST} {u[:65]}  {DIM}({r_[:60]}){RST}")
        print()

    # ── Acilis secenekleri ────────────────────────────────────────────────────
    sep(color=C)
    if ask_yn("Klonlanan klasoru Explorer'da ac"):
        open_folder(dest)
        ok("Klasor acildi!")

    index = dest / "index.html"
    if index.exists():
        if ask_yn("index.html'yi tarayicida ac"):
            webbrowser.open(index.as_uri())
            ok("Tarayicida acildi!")

    # ── Tekrar ────────────────────────────────────────────────────────────────
    print()
    sep("-", 70, DIM+C)
    if ask_yn("Baska bir site klonlamak ister misiniz?", default="h"):
        main()
    else:
        print(f"\n  {C}{BRT}Kullandiginiz icin tesekkurler! — Site Klonlayici v{VER}{RST}\n")

# ── Giris noktasi ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Y}Program kapatildi.{RST}\n")
        sys.exit(0)
