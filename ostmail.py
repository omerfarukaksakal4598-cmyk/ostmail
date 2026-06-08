import streamlit as st
import sqlite3
import hashlib

# 1. VERİTABANI AYARLARI (Hesapları ve Mailleri Saklamak İçin)
conn = sqlite3.connect("ostmail.db", check_same_thread=False)
cursor = conn.cursor()

# Tabloları oluşturma
cursor.execute("""
CREATE TABLE IF NOT EXISTS kullanicilar (
    eposta TEXT PRIMARY KEY,
    sifre TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS mailler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gonderen TEXT,
    alici TEXT,
    baslik TEXT,
    icerik TEXT,
    tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# 2. YARDIMCI FONKSİYONLAR
def sifre_sifrele(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

# 3. SAYFA TASARIMI
st.set_page_config(page_title="Östmail - Yeni Nesil E-Posta", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #111827; color: #f3f4f6; }
    .sidebar .sidebar-content { background-color: #1f2937; }
    .mail-box { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #ef4444; margin-bottom: 15px; }
    .mail-header { font-weight: bold; color: #ef4444; font-size: 16px; }
    .mail-meta { color: #9ca3af; font-size: 12px; }
    .mail-body { margin-top: 10px; color: #e5e7eb; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: #ef4444; text-align: center;'>📧 ÖSTMAIL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9ca3af;'>@ost.com Uzantılı Güvenli E-Posta Platformu</p>", unsafe_allow_html=True)
st.write("---")

# Giriş Kontrolü
if "giris_yapan_kullanici" not in st.session_state:
    st.session_state.giris_yapan_kullanici = None

# --- GİRİŞ / KAYIT EKRANI ---
if st.session_state.giris_yapan_kullanici is None:
    sekme1, sekme2 = st.tabs(["🔐 Giriş Yap", "📝 Hesap Oluştur"])
    
    with sekme1:
        st.subheader("Östmail Hesabınla Giriş Yap")
        giris_ad = st.text_input("Kullanıcı Adı (Örn: omer)", key="g_ad")
        giris_sifre = st.text_input("Şifre", type="password", key="g_sifre")
        
        if st.button("Giriş Yap", use_container_width=True):
            tam_eposta = f"{giris_ad.lower().strip()}@ost.com"
            sifreli_sifre = sifre_sifrele(giris_sifre)
            
            cursor.execute("SELECT * FROM kullanicilar WHERE eposta=? AND sifre=?", (tam_eposta, sifreli_sifre))
            kullanici = cursor.fetchone()
            
            if kullanici:
                st.session_state.giris_yapan_kullanici = tam_eposta
                st.success(f"Başarıyla giriş yapıldı! Hoş geldin, {tam_eposta}")
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")
                
    with sekme2:
        st.subheader("Yeni @ost.com Adresi Al")
        yeni_ad = st.text_input("İstediğin Kullanıcı Adı (Örn: ahmet)", key="y_ad")
        yeni_sifre = st.text_input("Şifre Belirle", type="password", key="y_sifre")
        
        if st.button("Hesabımı Oluştur", use_container_width=True):
            if yeni_ad and yeni_sifre:
                tam_eposta = f"{yeni_ad.lower().strip()}@ost.com"
                sifreli_sifre = sifre_sifrele(yeni_sifre)
                
                try:
                    cursor.execute("INSERT INTO kullanicilar (eposta, sifre) VALUES (?, ?)", (tam_eposta, sifreli_sifre))
                    conn.commit()
                    st.success(f"Hesabın başarıyla açıldı! Artık adresin: {tam_eposta}. Giriş yapabilirsin.")
                except sqlite3.IntegrityError:
                    st.error("Bu kullanıcı adı daha önce alınmış! Başka bir tane dene.")
            else:
                st.error("Lütfen tüm alanları doldur!")

# --- ANA MAİL ARAYÜZÜ ---
else:
    mevcut_kullanici = st.session_state.giris_yapan_kullanici
    
    # Sol Menü (Sidebar)
    st.sidebar.markdown(f"👤 **Hesap:** {mevcut_kullanici}")
    menu = st.sidebar.radio("Menü", ["📥 Gelen Kutusu", "📤 Giden Kutusu", "✏️ Yeni Mail Yaz"])
    
    if st.sidebar.button("🚪 Çıkış Yap"):
        st.session_state.giris_yapan_kullanici = None
        st.rerun()
        
    # --- YENİ MAİL YAZMA ---
    if menu == "✏️ Yeni Mail Yaz":
        st.header("✏️ Yeni E-Posta Gönder")
        alici_eposta = st.text_input("Alıcı E-Posta Adresi (Örn: ahmet@ost.com)")
        mail_baslik = st.text_input("Konu / Başlık")
        mail_icerik = st.text_area("Mesajınız", height=200)
        
        if st.button("Gönder", use_container_width=False):
            if alici_eposta and mail_baslik and mail_icerik:
                # Alıcı var mı kontrol et
                cursor.execute("SELECT * FROM kullanicilar WHERE eposta=?", (alici_eposta.lower().strip(),))
                if cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO mailler (gonderen, alici, baslik, icerik) VALUES (?, ?, ?, ?)",
                        (mevcut_kullanici, alici_eposta.lower().strip(), mail_baslik, mail_icerik)
                    )
                    conn.commit()
                    st.success(f"Mail başarıyla {alici_eposta} adresine gönderildi!")
                else:
                    st.error("Böyle bir Östmail kullanıcısı bulunamadı! Adresi doğru yazdığından emin ol.")
            else:
                st.error("Lütfen boş alan bırakma!")
                
    # --- GELEN KUTUSU ---
    elif menu == "📥 Gelen Kutusu":
        st.header("📥 Gelen Kutusu")
        cursor.execute("SELECT gonderen, baslik, icerik, tarih FROM mailler WHERE alici=? ORDER BY tarih DESC", (mevcut_kullanici,))
        gelen_mailler = cursor.fetchall()
        
        if not gelen_mailler:
            st.info("Gelen kutunuz boş.")
        else:
            for gonderen, baslik, icerik, tarih in gelen_mailler:
                st.markdown(f"""
                <div class='mail-box'>
                    <div class='mail-header'>Kimden: {gonderen}</div>
                    <div style='font-weight: bold; margin-top:5px;'>Konu: {baslik}</div>
                    <div class='mail-meta'>Tarih: {tarih}</div>
                    <div class='mail-body'>{icerik}</div>
                </div>
                """, unsafe_allow_html=True)
                
    # --- GİDEN KUTUSU ---
    elif menu == "📤 Giden Kutusu":
        st.header("📤 Gönderilen Mailler")
        cursor.execute("SELECT alici, baslik, icerik, tarih FROM mailler WHERE gonderen=? ORDER BY tarih DESC", (mevcut_kullanici,))
        giden_mailler = cursor.fetchall()
        
        if not giden_mailler:
            st.info("Henüz hiç mail göndermediniz.")
        else:
            for alici, baslik, icerik, tarih in giden_mailler:
                st.markdown(f"""
                <div class='mail-box' style='border-left: 5px solid #3b82f6;'>
                    <div class='mail-header' style='color: #3b82f6;'>Kime: {alici}</div>
                    <div style='font-weight: bold; margin-top:5px;'>Konu: {baslik}</div>
                    <div class='mail-meta'>Tarih: {tarih}</div>
                    <div class='mail-body'>{icerik}</div>
                </div>
                """, unsafe_allow_html=True)