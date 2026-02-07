import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
# rectpack kütüphanesi: pip install rectpack
from rectpack import newPacker, PackingMode, PackingBin
# Tüm güçlü algoritmaları çağırıyoruz
from rectpack import (
    MaxRectsBl, MaxRectsBaf, MaxRectsBssf, MaxRectsBlsf, 
    GuillotineBssfSas, GuillotineBlsfSas
)

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="OptiCut Pro+", page_icon="📐", layout="wide")

# ==============================================================================
# 🎨 ÖZEL TASARIM (CSS)
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #fffdf9; color: #000; font-family: 'Courier New', monospace; }
    
    /* Etiketleri Görünür Yap */
    div[data-testid="stWidgetLabel"] p {
        font-weight: 900 !important; color: #000 !important; font-size: 16px !important;
        text-transform: uppercase; margin-bottom: 5px !important;
    }
    label[data-testid="stWidgetLabel"] { color: #000 !important; font-weight: bold !important; }

    /* Inputlar */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
        border: 2px solid #000 !important; border-radius: 0px !important;
        background-color: #fff !important; color: #000 !important; font-weight: bold;
        box-shadow: 4px 4px 0px #ccc;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #FF5722 !important; box-shadow: 4px 4px 0px #FF5722 !important;
    }

    /* Buton */
    div.stButton > button {
        background-color: #000; color: #fff; border: 2px solid #000;
        border-radius: 0px !important; padding: 15px; font-weight: bold;
        text-transform: uppercase; letter-spacing: 2px;
        box-shadow: 6px 6px 0px #FF5722; width: 100%; transition: all 0.1s;
    }
    div.stButton > button:hover { color: #FF5722; border-color: #FF5722; }
    div.stButton > button:active { transform: translate(4px, 4px); box-shadow: 2px 2px 0px #FF5722; }

    /* Tablo */
    div[data-testid="stDataEditor"] { border: 2px solid #000; box-shadow: 8px 8px 0px rgba(0,0,0,0.1); border-radius: 0px !important; }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
st.markdown("<h1 style='text-align:center; border-bottom: 4px solid black; padding-bottom:10px;'>📐 OPTICUT <span style='background-color:#FF5722; color:white; padding:0 10px;'>PLUS</span></h1>", unsafe_allow_html=True)

# --- GİRİŞ PANELİ ---
st.markdown("### 1. HAMMADDE PANELİ")
c1, c2, c3, c4 = st.columns(4)
with c1: plaka_w = st.number_input("GENİŞLİK (cm)", value=210, step=10)
with c2: plaka_h = st.number_input("YÜKSEKLİK (cm)", value=280, step=10)
with c3: plaka_fiyat = st.number_input("BİRİM FİYAT (TL)", value=1500, step=50)
with c4: bicak_payi = st.number_input("BIÇAK PAYI (cm)", value=1, help="Parçalar arası boşluk. Sığmıyorsa 0 yapıp deneyin.")

st.markdown("---")

# --- LİSTE VE İŞLEM ---
col_liste, col_islem = st.columns([3, 1])

with col_liste:
    st.markdown("### 2. KESİM LİSTESİ")
    varsayilan_veri = pd.DataFrame({
        'Parça Kodu': ['P-01', 'P-02', 'P-03', 'P-04'],
        'En': [50.0, 80.0, 40.0, 40.0],
        'Boy': [60.0, 30.0, 200.0, 20.0],
        'Adet': [12, 15, 6, 10]
    })
    df = st.data_editor(varsayilan_veri, num_rows="dynamic", use_container_width=True, key="editor",
        column_config={
            "Adet": st.column_config.NumberColumn("Adet", min_value=1, step=1),
            "En": st.column_config.NumberColumn("En", min_value=1.0),
            "Boy": st.column_config.NumberColumn("Boy", min_value=1.0),
        })

with col_islem:
    st.markdown("### İŞLEM")
    st.write("6 farklı algoritma dikey/yatay tüm boşlukları tarar.")
    st.markdown("<br>", unsafe_allow_html=True)
    hesapla_btn = st.button("HESAPLAMAYI BAŞLAT ➤")

# --- HESAPLAMA MOTORU ---
if hesapla_btn:
    st.markdown("---")
    st.markdown("### 3. ANALİZ RAPORU")
    
    df_temiz = df.dropna().copy()
    if df_temiz.empty:
        st.error("❌ LİSTE BOŞ! Lütfen parça giriniz.")
        st.stop()
        
    try:
        df_temiz['En'] = df_temiz['En'].astype(float)
        df_temiz['Boy'] = df_temiz['Boy'].astype(float)
        df_temiz['Adet'] = df_temiz['Adet'].astype(int)
    except ValueError:
        st.error("❌ HATA: Sayısal değer giriniz.")
        st.stop()
    
    # Sıralama: Büyük parçaları öne al (Tetris mantığı)
    df_temiz['Alan'] = df_temiz['En'] * df_temiz['Boy']
    df_temiz = df_temiz.sort_values(by='Alan', ascending=False)

    # Renkler
    teknik_renkler = ['#FF5722', '#2196F3', '#FFC107', '#9C27B0', '#00BCD4', '#8BC34A', '#3F51B5']
    ozel_parcalar = df_temiz['Parça Kodu'].unique()
    renk_sozlugu = {isim: teknik_renkler[i % len(teknik_renkler)] for i, isim in enumerate(ozel_parcalar)}

    # -----------------------------------------------------------------------
    # 🧠 SUPER-SMART OPTİMİZASYON DÖNGÜSÜ
    # 6 Farklı Algoritma Yarışıyor
    # -----------------------------------------------------------------------
    algoritmalar = [
        MaxRectsBssf,       # Best Short Side Fit (Kısa kenara en iyi uyan)
        MaxRectsBl,         # Bottom Left (Klasik Sol Alt)
        MaxRectsBaf,        # Best Area Fit (En iyi alan)
        MaxRectsBlsf,       # Best Long Side Fit (Uzun kenarı doldurur - Dikey boşluklar için iyidir)
        GuillotineBssfSas,  # Guillotine Kesim (Şeritler halinde)
        GuillotineBlsfSas   # Guillotine Long Side
    ]
    
    best_bins = None
    min_bin_count = float('inf')
    max_efficiency = 0
    best_algo_name = ""

    # İlerleme çubuğu
    bar = st.progress(0)
    
    for i, algo in enumerate(algoritmalar):
        # rotation=True: Parçayı döndürme izni verir (Dikey/Yatay dener)
        packer = newPacker(mode=PackingMode.Offline, pack_algo=algo, rotation=True)
        
        for index, row in df_temiz.iterrows():
            if row['Adet'] > 0:
                for _ in range(int(row['Adet'])):
                    packer.add_rect(row['En'] + bicak_payi, row['Boy'] + bicak_payi, rid=row['Parça Kodu'])
        
        for _ in range(300):
            packer.add_bin(plaka_w, plaka_h)
            
        packer.pack()
        
        current_bins = [b for b in packer]
        if not current_bins: continue

        bin_count = len(current_bins)
        
        # Verimlilik hesabı
        total_used_area = sum([r.width * r.height for b in current_bins for r in b])
        total_bin_area = bin_count * (plaka_w * plaka_h)
        efficiency = total_used_area / total_bin_area if total_bin_area > 0 else 0

        # En iyiyi seç
        if bin_count < min_bin_count or (bin_count == min_bin_count and efficiency > max_efficiency):
            min_bin_count = bin_count
            max_efficiency = efficiency
            best_bins = current_bins
            best_algo_name = str(algo)
            
        bar.progress(int((i + 1) / len(algoritmalar) * 100))
    
    bar.empty()

    if not best_bins:
        st.error("❌ Parçalar sığmadı! Ölçüleri kontrol edin.")
    else:
        toplam_plaka = len(best_bins)
        toplam_maliyet = toplam_plaka * plaka_fiyat
        
        st.markdown(f"""
        <div style="display:flex; gap:20px; margin-bottom:20px;">
            <div style="border:2px solid black; padding:15px; background:white; flex:1; box-shadow:5px 5px 0px #000;">
                <div style="font-size:14px; color:#666; font-weight:bold;">TOPLAM PLAKA</div>
                <div style="font-size:28px; font-weight:900;">{toplam_plaka} <span style="font-size:16px;">ADET</span></div>
            </div>
            <div style="border:2px solid black; padding:15px; background:white; flex:1; box-shadow:5px 5px 0px #000;">
                <div style="font-size:14px; color:#666; font-weight:bold;">MALİYET</div>
                <div style="font-size:28px; font-weight:900; color:#FF5722;">{toplam_maliyet} <span style="font-size:16px;">TL</span></div>
            </div>
            <div style="border:2px solid black; padding:15px; background:white; flex:1; box-shadow:5px 5px 0px #000;">
                <div style="font-size:14px; color:#666; font-weight:bold;">DOLULUK</div>
                <div style="font-size:28px; font-weight:900; color:#2196F3;">%{max_efficiency*100:.1f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if bicak_payi > 0:
            st.warning(f"⚠️ **Dikkat:** Bıçak Payı ({bicak_payi} cm) açık. Gözle görülen boşluk 30 cm ise, makine oraya 30 cm parça koymaz (30+1=31 gerektiği için). Sığdırmak için Bıçak Payı'nı 0 yapıp deneyebilirsiniz.")

        st.write("### 🔥 OPTİMİZE EDİLMİŞ KESİM PLANI")
        
        for i, bin in enumerate(best_bins):
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor('#fffdf9') 
            ax.set_facecolor('white')
            
            # Plaka
            ax.add_patch(patches.Rectangle((0, 0), plaka_w, plaka_h, ec='black', fc='none', lw=3))
            
            bin_dolu_alan = 0
            for rect in bin:
                # Bıçak payını çizimden düş
                w = rect.width - bicak_payi
                h = rect.height - bicak_payi
                x, y = rect.x, rect.y
                rid = str(rect.rid)
                color = renk_sozlugu.get(rid, '#999')
                
                # Parça Çizimi
                ax.add_patch(patches.Rectangle((x, y), w, h, ec='black', fc=color, lw=2, alpha=1.0))
                
                # Etiket
                if w > 5 and h > 5:
                    font_sz = 9 if (w>20 and h>20) else 6
                    ax.text(x+w/2, y+h/2, f"{rid}\n{w:.0f}x{h:.0f}", 
                            ha='center', va='center', fontsize=font_sz, color='white', fontweight='bold',
                            bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', boxstyle='square,pad=0.1'))
                bin_dolu_alan += (w*h)
            
            doluluk = (bin_dolu_alan / (plaka_w*plaka_h)) * 100
            ax.set_xlim(-5, plaka_w + 5)
            ax.set_ylim(-5, plaka_h + 5)
            ax.set_title(f"PLAKA #{i+1} (DOLULUK: %{doluluk:.1f})", fontsize=12, fontweight='bold', fontname='monospace')
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
            
            st.pyplot(fig)