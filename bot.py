import yfinance as yf
import requests

# --- BURAYI DOLDUR (TIRNAK İÇİNDE KALSIN) ---
TOKEN = "8201264694:AAG_E7j_RvaCCX@WlMokf×gTQ
VpNvBmchYc"
ID = "1123565558"
# -------------------------------------------

def mesaj_gonder(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": ID, "text": text})

def calistir():
    try:
        # Hızlıca THYAO verisini çekip test edelim
        hisse = yf.Ticker("THYAO.IS")
        fiyat = hisse.info.get('currentPrice', 0)
        
        mesaj = f"🚀 Gökhan Hocam Sistem Çalıştı!\nTHYAO Fiyatı: {fiyat} TL"
        print(mesaj)
        mesaj_gonder(mesaj)
        
    except Exception as e:
        print(f"Hata: {e}")
        mesaj_gonder(f"Hata var: {e}")

if __name__ == "__main__":
    calistir()
