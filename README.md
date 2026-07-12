#  Web Cloner Engine

<div align="center">

> **Gelişmiş, güvenli ve yüksek uyumlulukla çalışan yeni nesil açık kaynaklı web arşivleme sistemi.**



---

###  Proje Hakkında

Bu araç, web sitelerinin arayüz tasarımlarını ve kaynak kodlarını  yerel bilgisayarınıza kusursuz bir şekilde indirmek için geliştirilmiş **açık kaynaklı bir klonlama motorudur**. Terminal ve sistem bazlı karakter kararsızlıklarını tamamen ortadan kaldıran akıllı bir mimariye sahiptir.

### 🛡️ Neden Güvenilir ve Şeffaf?

Piyasadaki kapalı kaynaklı araçların aksine, sistemimiz tamamen şeffaftır. Kod tabanında hiçbir gizli ağ isteği, telemetri veya veri toplama aracı bulunmaz. 

İşletim sistemleri (Windows, Linux, macOS) arasındaki enkod farklarından doğan **Türkçe/özel karakter bozulmalarını ve çökmeleri** engellemek için doğrudan standart giriş/çıkış akışlarını I/O streams optimize eder:

```python
import io
import os
import sys

# Tamamen Optimize Sistemimizi kullanır
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stdin, "buffer"):
    sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding="utf-8", errors="replace")
```

---

###  Temel Avantajlar

```text
┌────────────────────────────────────────────────────────┐
│  %100 Açık Kaynak - Her satırı denetlenebilir kod      │
├────────────────────────────────────────────────────────┤
│  Kusursuz UTF-8 Desteği - Karakter kaybına son         │
├────────────────────────────────────────────────────────┤
│  Hafif ve Hızlı - Sıfır gereksiz bağımlılık            │
└────────────────────────────────────────────────────────┘
```
