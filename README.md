# 🚀 CRYPTO ANALYTICS SYSTEM (CAS)

Bu proje, Python ve Tkinter kullanılarak geliştirilmiş, **Binance** API'si üzerinden gerçek zamanlı kripto para verilerini çeken, analiz eden ve görselleştiren bir masaüstü uygulamasıdır. Veri kalıcılığı ve analiz için MongoDB Atlas kullanılmıştır.

***

## ✨ Temel Özellikler

* **OOP Mimarisi:** Gelişmiş nesne yönelimli programlama (OOP) yapıları (Inheritance, Abstract Base Classes, Protocols) kullanılmıştır.
* **Gerçek Zamanlı Veri Çekme:** Binance API'si üzerinden 24 saatlik fiyat değişimleri ve işlem hacimleri dahil olmak üzere Top N (limit ayarlanabilir) kripto paranın anlık verilerini çeker.
* **Veri Kalıcılığı (MongoDB):** Çekilen tüm anlık ve tarihsel veriler MongoDB Atlas veritabanına kaydedilir (MongoEngine ODM kullanılmıştır).
* **Canlı Tablo ve Seans Takibi:** Tkinter tablosu üzerinde fiyat, 24 saatlik değişim ve oturum (session) başlangıcından itibaren toplam değişimi renk kodlarıyla takip eder.
* **Piyasa Analizi:** En çok kazananlar (Top Gainers) ve en çok kaybedenler (Top Losers) listelerini çıkaran bir analiz motoru içerir.
* **Gelişmiş Görselleştirme:** Seçilen herhangi bir tokenin geçmiş fiyat performansını gösteren dinamik bir grafik (Matplotlib) penceresi sunar.
* **Scrapy Entegrasyonu:** Tek bir butonla dinamik olarak bir Scrapy örümceği (spider) oluşturup çalıştırabilir ve veriyi yerel JSON dosyasına kaydeder.
* **Pydantic Veri Modelleri:** Veri tutarlılığını sağlamak için tüm veri transfer objeleri (DTO) Pydantic ile doğrulanmıştır.

***

## 🛠️ Kurulum ve Çalıştırma

### 1. Ön Koşullar

Projenin çalışması için aşağıdaki yazılımların ve kütüphanelerin yüklü olması gerekir:

* **Python 3.10+**
* **Git**
* **MongoDB Atlas** hesabı (Veritabanı bağlantı linki **`core.py`** içerisinde tanımlıdır.)

### 2. Kütüphane Kurulumu

Projenin ana bağımlılıkları aşağıdaki gibidir. Projeyi klonladığınız dizinde aşağıdaki komutu çalıştırın:

```bash
# Gerekli tüm Python kütüphanelerini kurar
pip install pymongo pydantic mongoengine requests scrapy dnspython matplotlib# COE203_2

