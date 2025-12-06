🚀 Crypto Analytics System – Real-Time Binance Tracker

Bu proje, Binance üzerindeki kripto varlıklarını gerçek zamanlı izleyen, analiz eden, grafiksel olarak gösteren ve verileri MongoDB üzerinde saklayan bir masaüstü uygulamasıdır.

Uygulama Python, Tkinter, Matplotlib, MongoEngine teknolojileri ile bir araya getirilmiştir.
Proje aynı zamanda EXE formatına dönüştürülmüş olup tüm Windows cihazlarda çalışabilir.

📂 Proje Yapısı

Proje şu anda GitHub’da aşağıdaki gibi sade bir yapıya sahiptir:

.
├── .gitignore        # Gereksiz dosyaların Git'e dahil edilmemesi için
├── core.py           # API işlemleri, MongoDB bağlantısı ve veri modelleri
├── main.exe          # Derlenmiş çalıştırılabilir uygulama
├── main.py           # Projenin giriş dosyası (GUI başlatılır)
├── test.py           # Test amaçlı denemeler
└── ui.py             # Tkinter arayüzü, grafikler, analiz ekranı


Bu yapıda her dosya direkt proje kök dizininde bulunur ve çalıştırılabilir.

📌 Uygulama Özellikleri
🔴 Gerçek Zamanlı Veri İzleme

Binance API üzerinden 50 kripto parayı anlık olarak çekeriz
Fiyat, 24 saatlik değişim, hacim ve session yüzdesi takip edilir

Veri akışı başlatıp durdurulabilir

📊 Grafiksel Coin Analizi

Her coin için 30 günlük fiyat grafiği çizilir

Seçili coin hakkında detaylı bilgiler gösterilir

Matplotlib kullanılarak profesyonel grafik elde edilir

🗄️ MongoDB Atlas Entegrasyonu

Token bilgileri TokenDocument modelleriyle kaydedilir

Geçmiş fiyatlar HistoricalDocument ile tutulur

Uygulama açıldığında son kayıtlar yüklenir

Database içinde kategori, fiyat, hacim gibi bilgiler saklanır

📈 Piyasa Analiz Modülü

Arayüz üzerindeki ANALYZE butonuna basıldığında:

En çok artan 5 token

En çok düşen 5 token

Toplam taranan varlık sayısı

Zaman damgalı analiz raporu

üretilir.

🕷️ Scrapy Entegrasyonu

GUI üzerinden Scrapy spider oluşturulur

Binance USDT pariteleri scrape edilir

Çıktı binance_data.json dosyasına kaydedilir