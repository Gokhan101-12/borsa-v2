import yfinance as yf
import requests
import time

# --- AYARLAR (Otomatik Dolduruldu) ---
TOKEN = "8201264694:AAG_E7j_RvaCCX0WlMokfxgTQvpNvBmchYc"
ID = "1123565558"

# BIST 30 ve Popüler Hisseler Listesi (Genişletilmiş)
PORTFOY = [
    "THYAO.IS", "EREGL.IS", "TUPRS.IS", "KCHOL.IS", "SISE.IS", 
    "ASELS.IS", "BIMAS.IS", "AKBNK.IS", "YKBNK.IS", "GARAN.IS",
    "SAHOL.IS", "FROTO.IS", "TOASO.IS", "PETKM.IS", "TCELL.IS",
    "TTKOM.IS", "HEKTS.IS", "SASA.IS", "KOZAL.IS", "KRDMD.IS",
    "ENKAI.IS", "ISCTR.IS", "MGROS.IS", "PGSUS.IS", "ALARK.IS",
    "ODAS.IS", "EKGYO.IS", "VESTL.IS", "ARCLK.IS", "SOKM.IS",
    "ASTOR.IS", "KONTR.IS", "GUBRF.IS", "OYAKC.IS", "DOHOL.IS"
]

def mesaj_gonder(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # Mesaj çok uzunsa parça parça gitmesi için try-except
    try:
        payload = {"chat_id": ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

def analyze_and_report():
    print("Analiz başlıyor, lütfen bekleyin...")
    
    # Rapor başlığı
    full_report = "📢 **GÜNLÜK GENİŞ BORSA TARAMASI** 📢\n\n"
    full_report += "Graham Formülü ile 'Ucuz' (AL) Sinyali Verenler:\n"
    full_report += "-----------------------------------\n"
    
    ucuz_hisse_bulundu = False

    for symbol in PORTFOY:
        try:
            # Yahoo Finance bazen çok hızlı istek atınca engeller, 1 sn uyutalım
            time.sleep(0.5) 
            
            stock = yf.Ticker(symbol)
            info = stock.info
            
            fiyat = info.get('currentPrice', 0)
            eps = info.get('trailingEps', 0)
            
            # Değerleme (Graham Mantığı: V = EPS * (8.5 + 2g))
            # Büyüme (g) beklentisini %15 standart alıyoruz.
            if eps > 0 and fiyat > 0:
                fair_value = eps * (8.5 + 2 * 15)
                potansiyel = ((fair_value - fiyat) / fiyat) * 100
                
                # Sadece POTANSİYELİ YÜKSEK (%30 üzeri) olanları rapora ekle
                # Böylece yüzlerce satır çöp veri gelmez, sadece fırsatlar gelir.
                if potansiyel > 30:
                    ucuz_hisse_bulundu = True
                    full_report += f"✅ *{symbol.replace('.IS', '')}*\n"
                    full_report += f"Fiyat: {fiyat} TL | Adil Değer: {fair_value:.1f} TL\n"
                    full_report += f"🚀 Potansiyel: %{potansiyel:.0f} (UCUZ)\n"
                    full_report += "------------------\n"
                    
        except Exception as e:
            print(f"{symbol} hatası: {e}")
            continue

    if not ucuz_hisse_bulundu:
        full_report += "Bu listede şu an aşırı ucuz kalmış hisse bulunamadı.\n"

    full_report += "\n⚠️ _Yatırım tavsiyesi değildir. Robotik hesaplamadır._"
    
    # Telegram'a at
    mesaj_gonder(full_report)
    print("Rapor gönderildi.")

if __name__ == "__main__":
    analyze_and_report()
