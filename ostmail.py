import streamlit as st
import sqlite3
import hashlib

# 1. VERİBATANI AYARLARI
conn = sqlite3.connect("ostmail_v4.db", check_same_thread=False)
cursor = conn.cursor()

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
    resim_url TEXT,
    tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# 2. YARDIMCI FONKSİYONLAR
def sifre_sifrele(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

# Sayfa Ayarları
st.set_page_config(page_title="Östmail Premium", layout="wide")

# Şık Karanlık Tema Tasarımı
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .mail-card { background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #38bdf8; margin-bottom: 10px; cursor: pointer; transition: 0.3s; }
    .mail-card:hover { background-color: #334155; }
    .mail-title { font-weight: bold; color: #38bdf8; font-size: 16px; }
    .mail-meta { color: #94a3b8; font-size: 12px; }
    .mail-open-box { background-color: #1e293b; padding: 25px; border-radius: 12px; border: 1px solid #475569; margin-top: 15px; }
    .stButton>button { background-color: #0284c7 !important; color: white !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: #38bdf8; text-align: center;'>📧 ÖSTMAIL PREMIUM</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>Gelişmiş @ost.com E-Posta Servisi</p>", unsafe_allow_html=True)
st.write("---")

# 3. BENİ HATIRLA ÖZELLİĞİ
if "giris_yapan_kullanici" not in st.query_params:
    current_user = None
else:
    current_user = st.query_params["giris_yapan_kullanici"]

# --- GİRİŞ / KAYIT EKRANI ---
if current_user is None:
    sekme1, sekme2 = st.tabs(["🔐 Giriş Yap", "📝 Hesap Oluştur"])
    
    with sekme1:
        st.subheader("Hesabınla Giriş Yap")
        # Örnek yazısı kaldırıldı
        giris_ad = st.text_input("E-Posta Adresiniz", key="g_ad").lower().strip()
        giris_sifre = st.text_input("Şifre", type="password", key="g_sifre")
        
        if st.button("Giriş Yap", use_container_width=True):
            if giris_ad and giris_sifre:
                if not giris_ad.endswith("@ost.com"):
                    st.error("❌ Hata: Giriş yaparken e-posta adresinizin sonuna '@ost.com' yazmak zorunludur!")
                else:
                    sifreli_sifre = sifre_sifrele(giris_sifre)
                    cursor.execute("SELECT * FROM kullanicilar WHERE eposta=? AND sifre=?", (giris_ad, sifreli_sifre))
                    if cursor.fetchone():
                        st.query_params["giris_yapan_kullanici"] = giris_ad
                        st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                        st.rerun()
                    else:
                        st.error("Kullanıcı adı veya şifre hatalı!")
            else:
                st.error("Lütfen tüm alanları doldurun!")
                
    with sekme2:
        st.subheader("Yeni @ost.com Adresi Al")
        # Örnek yazısı kaldırıldı
        yeni_ad = st.text_input("İstediğin Kullanıcı Adı", key="y_ad").lower().strip()
        yeni_sifre = st.text_input("Şifre Belirle (En az 6 haneli)", type="password", key="y_sifre")
        
        if st.button("Hesabımı Oluştur", use_container_width=True):
            if not yeni_ad or not yeni_sifre:
                st.error("Lütfen tüm alanları doldurun!")
            elif len(yeni_sifre) < 6:
                st.error("❌ Şifreniz çok kısa! Güvenliğiniz için şifre en az 6 haneli olmalıdır.")
            else:
                temiz_ad = yeni_ad.replace("@ost.com", "")
                tam_eposta = f"{temiz_ad}@ost.com"
                sifreli_sifre = sifre_sifrele(yeni_sifre)
                
                try:
                    cursor.execute("INSERT INTO kullanicilar (eposta, sifre) VALUES (?, ?)", (tam_eposta, sifreli_sifre))
                    conn.commit()
                    st.success(f"🎉 Tebrikler! {tam_eposta} başarıyla açıldı. Giriş sekmesinden bağlanabilirsiniz.")
                except sqlite3.IntegrityError:
                    st.error("Bu kullanıcı adı kapılmış! Başka bir tane dene.")

# --- ANA UYGULAMA ARAYÜZÜ ---
else:
    st.sidebar.markdown(f"👤 **Aktif Hesap:** \n`{current_user}`")
    menu = st.sidebar.radio("Menü Menüsü", ["📥 Gelen Kutusu", "✏️ Yeni Mail Yaz", "📤 Giden Kutusu"])
    
    if st.sidebar.button("🚪 Oturumu Kapat"):
        st.query_params.clear()
        st.rerun()
        
    # --- YENİ MAİL YAZMA (RESİM DESTEKLİ) ---
    if menu == "✏️ Yeni Mail Yaz":
        st.header("✏️ Yeni E-Posta Oluştur")
        # Örnek yazısı kaldırıldı
        alici = st.text_input("Alıcı Adresi").lower().strip()
        baslik = st.text_input("Konu")
        resim_url = st.text_input("Resim URL'si (İsteğe bağlı)")
        icerik = st.text_area("Mesaj içeriği", height=150)
        
        if st.button("Zarfa Koy ve Gönder"):
            if alici and baslik and icerik:
                if not alici.endswith("@ost.com"):
                    st.error("❌ Hata: Alıcı adresi mutlaka '@ost.com' ile bitmelidir!")
                else:
                    cursor.execute("SELECT * FROM kullanicilar WHERE eposta=?", (alici,))
                    if cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO mailler (gonderen, alici, baslik, icerik, resim_url) VALUES (?, ?, ?, ?, ?)",
                            (current_user, alici, baslik, icerik, resim_url)
                        )
                        conn.commit()
                        st.success(f"📬 Mail başarıyla gönderildi!")
                    else:
                        st.error("Böyle bir Östmail kullanıcısı sistemde kayıtlı değil!")
            else:
                st.error("Lütfen Alıcı, Başlık ve İçerik alanlarını boş bırakmayın!")

    # --- GELEN KUTUSU ---
    elif menu == "📥 Gelen Kutusu":
        st.header("📥 Gelen Kutusu")
        cursor.execute("SELECT id, gonderen, baslik, icerik, resim_url, tarih FROM mailler WHERE alici=? ORDER BY tarih DESC", (current_user,))
        gelenler = cursor.fetchall()
        
        if not gelenler:
            st.info("Gelen kutunuzda henüz bir mesaj yok.")
        else:
            mail_sozlugu = {}
            secenekler = []
            
            for m_id, gonderen, baslik, icerik, r_url, tarih in gelenler:
                gorunum_metni = f"✉️ {gonderen} - {baslik} ({tarih[:16]})"
                secenekler.append(gorunum_metni)
                mail_sozlugu[gorunum_metni] = {"gonderen": gonderen, "baslik": baslik, "icerik": icerik, "resim": r_url, "tarih": tarih}
            
            st.markdown("👇 **Açmak ve okumak istediğiniz mesajı seçin:**")
            secilen_mail = st.selectbox("Mesaj Seçici", secenekler, label_visibility="collapsed")
            
            if secilen_mail:
                m = mail_sozlugu[secilen_mail]
                st.markdown(f"""
                <div class='mail-open-box'>
                    <div style='font-size: 20px; font-weight: bold; color: #38bdf8;'>{m['baslik']}</div>
                    <div class='mail-meta'><b>Kimden:</b> {m['gonderen']} | <b>Tarih:</b> {m['tarih']}</div>
                    <hr style='border-color: #475569;'>
                    <div style='font-size: 16px; line-height: 1.6; white-space: pre-wrap;'>{m['icerik']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if m['resim'] and m['resim'].strip() != "":
                    st.markdown("<br>🖼️ **Gelen Ekli Resim:**", unsafe_allow_html=True)
                    try:
                        st.image(m['resim'], use_container_width=True)
                    except:
                        st.warning("Gönderilen resim linki kırık veya geçersiz olduğundan yüklenemedi.")

    # --- GİDEN KUTUSU ---
    elif menu == "📤 Giden Kutusu":
        st.header("📤 Gönderilen Mailler")
        cursor.execute("SELECT alici, baslik, icerik, resim_url, tarih FROM mailler WHERE gonderen=? ORDER BY tarih DESC", (current_user,))
        gidenler = cursor.fetchall()
        
        if not gidenler:
            st.info("Henüz kimseye mail göndermediniz.")
        else:
            for alici, baslik, icerik, r_url, tarih in gidenler:
                st.markdown(f"""
                <div class='mail-card' style='border-left: 5px solid #a855f7;'>
                    <div class='mail-title' style='color: #a855f7;'>Kime: {alici}</div>
                    <div style='font-weight: bold;'>Konu: {baslik}</div>
                    <div class='mail-meta'>Tarih: {tarih}</div>
                    <div style='margin-top: 10px;'>{icerik}</div>
                </div>
                """, unsafe_allow_html=True)
                if r_url:
                    st.caption("🖼️ Resim eki gönderildi.")
