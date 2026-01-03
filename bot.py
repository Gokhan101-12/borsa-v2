import requests
import pandas as pd
import yfinance as yf
import concurrent.futures
import time

# --- AYARLAR ---
TOKEN = "8201264694:AAG_E7j_RvaCCX0WlMokfxgTQvpNvBmchYc"
ID = "1123565558"

def mesaj_gonder(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # Telegram mesaj limiti 4096 karakterdir, uzunsa parça parça atalım
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            sub_text = text[i:i+4000]
            requests.post(url, json={"chat_id": ID, "text": sub_text, "parse_mode": "Markdown"})
    else:
        requests.post(url, json={"chat_id": ID, "text": text, "parse_mode": "Markdown"})

def tum_hisseleri_getir():
    # TradingView altyapısından BIST'teki tüm hisseleri çeker (600+)
    url = "https://scanner.tradingview.com/turkey/scan"
    payload = {
        "filter": [{"left": "type", "operation": "equal", "right": "stock"}],
        "options": {"lang": "tr"},
        "symbols": {"query": {"types": []}},
        "columns": ["name", "close", "volume", "type"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [0, 600] # İlk 600 hisse (Hacme göre sıralı)
    }
    try:
        response = requests.post(url, json=payload).json()
        hisseler = [f"{row['d'][0]}.IS" for row in response['data']]
        return hisseler
    except Exception as e:
        print(f"Hisse listesi çekilemedi: {e}")
        # Yedek liste (Eğer API çalışmazsa BIST 30'a döner)
        return ["THYAO.IS", "EREGL.IS", "GARAN.IS", "AKBNK.IS", "SISE.IS"]

def williams_r_hesapla(df, period=14):
    # Williams %R Formülü: (Highest High - Close) / (Highest High - Lowest Low) * -100
    highest_high = df['High'].rolling(window=period).max()
    lowest_low = df['Low'].rolling(window=period).min()
    wr = -100 * ((highest_high - df['Close']) / (highest_high - lowest_low))
    return wr.iloc[-1]

def hisse_analiz_et(symbol):
    try:
        stock = yf.Ticker(symbol)
        
        # 1. TEMEL ANALİZ (Graham Değerlemesi)
        # Verileri hızlı çekmek için 'fast_info' kullanalım (Daha hızlıdır)
        info = stock.info
        
        fiyat = info.get('currentPrice', 0)
        eps = info.get('trailingEps', 0)
        
        # Eğer kar etmiyorsa (EPS negatifse) veya fiyat yoksa geç
        if eps is None or eps <= 0 or fiyat is None or fiyat == 0:
            return None

        # Graham Formülü: V = EPS * (8.5 + 2g) -> g=15 aldık
        adil_deger = eps * (8.5 + 2 * 15)
        
        # Potansiyel hesabı (Ne kadar iskontolu?)
        potansiyel = ((adil_deger - fiyat) / fiyat) * 100
        
        # KRİTER 1: En az %30 potansiyel (Ucuzluk) olsun
        if potansiyel < 30:
            return None

        # 2. TEKNİK ANALİZ (Williams %R)
        # Son 1 aylık veriyi çekelim (Günlük)
        hist = stock.history(period="1mo")
        if len(hist) < 15:
            return None
            
        w_r = williams_r_hesapla(hist)
        
        # KRİTER 2: Williams %R < -80 (Aşırı Satım / Dip Bölgesi)
        # -80 ile -100 arası "DİP" demektir.
        if w_r > -80: 
            return None

        # Tüm filtreleri geçtiyse raporla
        return {
            "symbol": symbol.replace(".IS", ""),
            "fiyat": fiyat,
            "adil_deger": adil_deger,
            "potansiyel": potansiyel,
            "williams": w_r
        }

    except Exception as e:
        return None

def main():
    print("Hisseler çekiliyor...")
    hisse_listesi = tum_hisseleri_getir()
    print(f"Toplam {len(hisse_listesi)} hisse taramaya başlıyor...")
    
    rapor = "💎 **KELEPİR & DİPTEKİ HİSSELER** 💎\n"
    rapor += "_Kriterler: Graham'a göre ucuz VE Williams %R < -80 (Dip)_ \n"
    rapor += "-----------------------------------\n"
    
    bulunanlar = []

    # MULTITHREADING (Hızlandırma)
    # 20 işçi (thread) aynı anda çalışacak.
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(hisse_analiz_et, hisse_listesi)
        
        for result in results:
            if result:
                bulunanlar.append(result)

    # Sonuçları Potansiyele göre sırala (En ucuz en üstte)
    bulunanlar.sort(key=lambda x: x['potansiyel'], reverse=True)

    if not bulunanlar:
        rapor += "Bu kriterlere uyan hisse bulunamadı."
    else:
        # Telegram mesajı çok şişmesin diye ilk 20 tanesini yazalım
        count = 0
        for h in bulunanlar:
            if count >= 20: break
            
            ikon = "🟢"
            # Williams değeri -90 altındaysa "Çok Dip" demektir
            w_durum = "Dipte" if h['williams'] > -90 else "AŞIRI DİPTE 🔥"
            
            rapor += f"🎯 *{h['symbol']}* ({h['fiyat']} TL)\n"
            rapor += f"📊 Adil Değer: {h['adil_deger']:.1f} TL (Primi: %{h['potansiyel']:.0f})\n"
            rapor += f"📉 Williams %R: {h['williams']:.1f} ({w_durum})\n"
            rapor += "------------------\n"
            count += 1
            
        rapor += f"\n_Toplam {len(hisse_listesi)} hisseden {len(bulunanlar)} tanesi filtreye takıldı._"

    print("Analiz bitti, mesaj gönderiliyor...")
    mesaj_gonder(rapor)

if __name__ == "__main__":
    main()
