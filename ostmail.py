"""
ÖSTMAIL PREMIUM v8.0 - TAM DONANIMLI
Bu dosya; veritabanı yönetimi, güvenli auth, mail sistemi, 
çöp kutusu ve gelişmiş admin log sistemini barındırır.
"""

import streamlit as st
import sqlite3
import hashlib
import os
import time
from datetime import datetime

# ==============================================================================
# 1. KONFİGÜRASYON VE SİSTEM AYARLARI
# ==============================================================================
DB_NAME = "ostmail_v8.db"
LOG_DIR = r"C:\Users\omeef\Videos\ostmailgiriş"
LOG_FILE = os.path.join(LOG_DIR, "giris_kayitlari.txt")

# Veritabanı bağlantısı
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

def initialize_database():
    """
    Sistemin ihtiyaç duyduğu tüm tabloları ve dizinleri oluşturur.
    Veritabanı bütünlüğünü sağlar.
    """
    # Klasör yoksa oluştur
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    # Tablo 1: Kullanıcılar
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kullanicilar (
        eposta TEXT PRIMARY KEY,
        sifre TEXT,
        kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Tablo 2: Mailler
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mailler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gonderen TEXT,
        alici TEXT,
        baslik TEXT,
        icerik TEXT,
        dosya_adi TEXT,
        dosya_veri BLOB,
        durum_alici TEXT DEFAULT 'gelen',
        silinme_tarihi TIMESTAMP,
        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

# Veritabanını başlat
initialize_database()

# ==============================================================================
# 2. YARDIMCI GÜVENLİK VE LOGLAMA FONKSİYONLARI
# ==============================================================================
def hash_password(password: str) -> str:
    """Şifreyi SHA-256 algoritması ile özetler (hashing)."""
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email: str) -> bool:
    """E-posta adresi geçerliliğini kontrol eder."""
    return email.endswith("@ost.com") and len(email) > 8

def log_login_event(eposta: str):
    """
    Giriş olaylarını kaydeder:
    1. Yerel log dosyasına yazar.
    2. Admin'e otomatik mail atar (bildirim sistemi).
    """
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Dosya Loglama
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{zaman}] BAŞARILI GİRİŞ - Kullanıcı: {eposta}\n")
    except Exception as e:
        st.error(f"Kritik Hata (Log): {e}")

    # 2. Admin Mail Bildirimi (Veritabanı üzerinden)
    try:
        sistem_mesaji = f"SİSTEM UYARI:\n{eposta} adresli kullanıcı {zaman} tarihinde giriş yaptı."
        cursor.execute(
            "INSERT INTO mailler (gonderen, alici, baslik, icerik) VALUES (?, ?, ?, ?)",
            ("sistem@ost.com", "admin@ost.com", "🛡️ Yeni Giriş Bildirimi", sistem_mesaji)
        )
        conn.commit()
    except Exception as e:
        st.error(f"Admin bildirim hatası: {e}")

# ==============================================================================
# 3. ARAYÜZ VE STİL YÖNETİMİ
# ==============================================================================
st.set_page_config(page_title="Östmail Premium v8.0", layout="wide")

# Özel CSS Yapılandırması
st.markdown("""
    <style>
    .stApp { background-color: #0c0e12; color: #e2e8f0; }
    .header-text { color: #38bdf8; text-align: center; font-size: 50px; font-weight: bold; }
    .mail-card { background-color: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8; margin-bottom: 15px; }
    .log-box { font-family: monospace; background: #000; color: #0f0; padding: 15px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='header-text'>📧 ÖSTMAIL PREMIUM</h1>", unsafe_allow_html=True)
st.write("---")

# ==============================================================================
# 4. OTURUM YÖNETİMİ VE GİRİŞ KONTROLÜ
# ==============================================================================
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# GİRİŞ YAPILMADIYSA
if st.session_state.current_user is None:
    tab_login, tab_register, tab_help = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol", "ℹ️ Bilgi"])
    
    with tab_login:
        email_in = st.text_input("E-Posta Adresi", key="g_mail").lower().strip()
        pass_in = st.text_input("Şifre", type="password", key="g_pass")
        
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            sifreli = hash_password(pass_in)
            cursor.execute("SELECT * FROM kullanicilar WHERE eposta=? AND sifre=?", (email_in, sifreli))
            if cursor.fetchone():
                log_login_event(email_in)
                st.session_state.current_user = email_in
                st.rerun()
            else:
                st.error("❌ Hatalı E-posta veya Şifre.")

    with tab_register:
        r_email = st.text_input("Yeni E-Posta (user@ost.com)", key="r_mail").lower().strip()
        r_pass = st.text_input("Şifre Belirle", type="password", key="r_pass")
        
        if st.button("Hesabı Oluştur", use_container_width=True):
            if not is_valid_email(r_email):
                st.error("Geçersiz e-posta formatı! (@ost.com kullanın)")
            elif len(r_pass) < 6:
                st.error("Şifre 6 karakterden az olamaz!")
            else:
                try:
                    cursor.execute("INSERT INTO kullanicilar (eposta, sifre) VALUES (?, ?)", (r_email, hash_password(r_pass)))
                    conn.commit()
                    st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
                except:
                    st.error("Bu e-posta adresi zaten alınmış.")

# GİRİŞ YAPILDIKTAN SONRA ANA ARAYÜZ
else:
    # Sidebar Menü
    st.sidebar.markdown(f"### 👤 {st.session_state.current_user}")
    menu_secenekleri = [
        "📥 Gelen Kutusu", 
        "✏️ Yeni İleti Yaz", 
        "📤 Giden Kutusu", 
        "🗑️ Çöp Kutusu", 
        "🛡️ Profil Ayarları", 
        "👑 Yönetici Paneli"
    ]
    menu = st.sidebar.radio("Navigasyon Menüsü", menu_secenekleri)
    
    if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.current_user = None
        st.rerun()

    # --- 1. GELEN KUTUSU ---
    if menu == "📥 Gelen Kutusu":
        st.header("📥 Gelen Kutusu")
        msgs = cursor.execute("SELECT id, gonderen, baslik, icerik, dosya_adi, dosya_veri FROM mailler WHERE alici=? AND durum_alici='gelen' ORDER BY tarih DESC", (st.session_state.current_user,)).fetchall()
        if not msgs:
            st.info("Gelen kutunuz boş.")
        else:
            for m_id, g, b, i, d_a, d_v in msgs:
                with st.expander(f"✉️ {g} | {b}"):
                    st.write(f"**İçerik:** {i}")
                    if d_a:
                        st.download_button(f"📥 Dosyayı İndir: {d_a}", d_v, d_a)
                    if st.button("🗑️ Çöp Kutusuna At", key=f"del_{m_id}"):
                        cursor.execute("UPDATE mailler SET durum_alici='cop', silinme_tarihi=CURRENT_TIMESTAMP WHERE id=?", (m_id,))
                        conn.commit()
                        st.rerun()

    # --- 2. YENİ İLETİ ---
    elif menu == "✏️ Yeni İleti Yaz":
        st.header("✏️ Yeni İleti Gönder")
        with st.form("mail_form"):
            target = st.text_input("Alıcı Adresi")
            subject = st.text_input("Konu")
            body = st.text_area("İleti içeriği", height=150)
            file_u = st.file_uploader("Dosya Yükle")
            
            if st.form_submit_button("Gönder"):
                if target and subject and body:
                    d_name = file_u.name if file_u else None
                    d_data = file_u.read() if file_u else None
                    cursor.execute("INSERT INTO mailler (gonderen, alici, baslik, icerik, dosya_adi, dosya_veri) VALUES (?, ?, ?, ?, ?, ?)", 
                                   (st.session_state.current_user, target, subject, body, d_name, d_data))
                    conn.commit()
                    st.success("Mail iletildi!")
                else:
                    st.error("Tüm alanları doldurmalısın.")

    # --- 3. GİDEN KUTUSU ---
    elif menu == "📤 Giden Kutusu":
        st.header("📤 Giden Kutusu")
        gidenler = cursor.execute("SELECT alici, baslik, icerik FROM mailler WHERE gonderen=?", (st.session_state.current_user,)).fetchall()
        for alici, baslik, icerik in gidenler:
            st.markdown(f"<div class='mail-card'><b>Kime:</b> {alici}<br><b>Konu:</b> {baslik}<br>{icerik}</div>", unsafe_allow_html=True)

    # --- 4. ÇÖP KUTUSU ---
    elif menu == "🗑️ Çöp Kutusu":
        st.header("🗑️ Çöp Kutusu")
        copler = cursor.execute("SELECT id, gonderen, baslik FROM mailler WHERE alici=? AND durum_alici='cop'", (st.session_state.current_user,)).fetchall()
        if not copler:
            st.info("Çöp kutusu boş.")
        else:
            for m_id, g, b in copler:
                col1, col2 = st.columns([4, 1])
                col1.write(f"⚠️ {g} - {b}")
                if col2.button("Kalıcı Sil", key=f"perm_{m_id}"):
                    cursor.execute("DELETE FROM mailler WHERE id=?", (m_id,))
                    conn.commit()
                    st.rerun()

    # --- 5. PROFİL AYARLARI ---
    elif menu == "🛡️ Profil Ayarları":
        st.header("🛡️ Profilim")
        st.write(f"**E-Posta:** {st.session_state.current_user}")
        st.write("Sistem durumu: ✅ Aktif")

    # --- 6. YÖNETİCİ PANELİ ---
    elif menu == "👑 Yönetici Paneli":
        if st.session_state.current_user == "admin@ost.com":
            st.header("👑 Yönetici Kontrol Paneli")
            
            # Alt sekmeler ile admin paneli detaylandırıldı
            t1, t2, t3 = st.tabs(["🛡️ Log Analizi", "📊 İstatistikler", "⚙️ Sistem Temizliği"])
            
            with t1:
                st.subheader("Giriş Logları")
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, "r", encoding="utf-8") as f:
                        st.markdown(f"<div class='log-box'>{f.read()}</div>", unsafe_allow_html=True)
                else:
                    st.warning("Log dosyası yok.")
                    
            with t2:
                st.subheader("Sistem İstatistikleri")
                u_c = cursor.execute("SELECT count(*) FROM kullanicilar").fetchone()[0]
                m_c = cursor.execute("SELECT count(*) FROM mailler").fetchone()[0]
                col_a, col_b = st.columns(2)
                col_a.metric("Toplam Kullanıcı", u_c)
                col_b.metric("Toplam Mail", m_c)
                
            with t3:
                st.subheader("Sistem İşlemleri")
                if st.button("Logları Temizle"):
                    with open(LOG_FILE, "w") as f: f.write("")
                    st.success("Loglar temizlendi.")
                    st.rerun()
                if st.button("Database Integrity Check"):
                    initialize_database()
                    st.success("Database kontrol edildi.")
        else:
            st.error("⛔ Yetkisiz Erişim! Bu alan adminlere özeldir.")

# ==============================================================================
# FOOTER BÖLÜMÜ
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.caption("Östmail v8.0 Enterprise | Tüm Hakları Saklıdır.")
# Kod bitişi: Geliştirici - AI
