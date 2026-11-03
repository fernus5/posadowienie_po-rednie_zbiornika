import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# KONFIGURACJA STRONY I STYLE CSS
# ==========================================
st.set_page_config(page_title="Kalkulator Pali - Zbiorniki", layout="wide")

# Wstrzyknięcie stylów powiększających czcionkę zakładek
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab"] p {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# INICJALIZACJA PARAMETRÓW SESJI (URL ROUTING)
# ==========================================
# Przykład użycia linku wysyłanego do biura: mojkalkulator.streamlit.app/?client_id=biuro_szczecin
params = st.query_params
if "client_id" in params:
    session_client = params["client_id"]
    # Rejestracja unikalnej instancji sesji (zabezpieczenie przed podwójnym logowaniem)
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True
        init_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # TUTAJ MOŻNA PODPIĄĆ ZAPIS DO BAZY (np. Google Sheets za pomocą gspread)
        # Na ten moment wyświetlamy dyskretny log techniczny (możesz to usunąć w wersji publicznej)
        st.toast(f"Aktywowano dedykowaną instancję środowiska: {session_client} ({init_time})", icon="⚙️")
        
        # Przykład integracji z zewnętrznym webhookiem (np. Make/Zapier):
        # import requests
        # try:
        #     requests.post("https://twoj-webhook-url.com", json={"client": session_client, "time": init_time}, timeout=2)
        # except:
        #     pass

st.title("Analiza posadowienia pośredniego zbiornika retencyjnego")
st.markdown("Wypór (UPL), osiadanie (GEO/SGU), zbrojenie, przedmiar robót oraz **optymalizacja kosztowa**.")

# ==========================================
# PANEL BOCZNY: DANE WEJŚCIOWE
# ==========================================
st.sidebar.markdown("### 1. Parametry geometryczne zbiornika ")
L_z = st.sidebar.number_input("Długość zewnętrzna L [m]", value=10.0, step=1.0)
B_z = st.sidebar.number_input("Szerokość zewnętrzna B [m]", value=5.0, step=1.0)
H_z = st.sidebar.number_input("Wysokość całkowita H [m]", value=3.0, step=0.5)
grubosc = st.sidebar.number_input("Grubość ścian i dna [m]", value=0.3, step=0.05)
gamma_betonu = st.sidebar.number_input("Ciężar obj. betonu zbiornika [kN/m³]", value=24.0)

st.sidebar.markdown("### 2. Zagłębienie i Naziom")
h_naziomu = st.sidebar.number_input("Grubość gruntu nad stropem [m]", value=1.0, step=0.1)
gamma_naziomu = st.sidebar.number_input("Ciężar obj. gruntu naziomu [kN/m³]", value=18.0, step=0.5)
D_f = h_naziomu + H_z 

st.sidebar.markdown("### 3. Profil Geotechniczny")
tryb_gruntu = st.sidebar.radio(
    "Metoda definiowania parametrów gruntu", 
    ["Korelacja z parametrów wiodących (ID / IL)", 
     "Ręczne definiowanie oporów (pełna kontrola)"], 
    horizontal=False
)

st.sidebar.markdown("### 4. Warunki Hydrogeologiczne")
H_wody = st.sidebar.number_input("Poziom wody na zewnątrz (od dna) [m]", value=2.5, step=0.1)
gamma_wody = 10.0 

st.sidebar.markdown("### 5. Parametry Pali")
D_pala = st.sidebar.number_input("Średnica pala D [m]", value=0.4, step=0.1)
L_pala = st.sidebar.number_input("Całkowita długość pala [m]", value=6.0, step=0.5)
liczba_pali = st.sidebar.number_input("Liczba zaplanowanych pali [szt.]", value=12, step=1, min_value=1)

technologia = st.sidebar.selectbox(
    "Technologia wykonania pala", 
    ["Pale przemieszczeniowe (wbijane, FDP) - α_s = 1.0", 
     "Pale CFA (świder ciągły) - α_s = 0.8", 
     "Pale wiercone w obsadzie - α_s = 0.6"]
)
alfa_s = float(technologia.split("=")[-1].strip())

st.sidebar.markdown("### 6. Stany Graniczne Użytkowalności (SGU)")
s_max = st.sidebar.number_input("Dopuszczalne osiadanie s_max [mm]", value=50.0, step=5.0)

st.sidebar.markdown("### 7. Parametry Zbrojenia")
stal_fyk = st.sidebar.number_input("Granica plastyczności stali f_yk [MPa]", value=500, step=50)
phi_preta = st.sidebar.selectbox("Średnica pręta podłużnego [mm]", [12, 16, 20, 25, 32], index=1)

st.sidebar.markdown("### 8. Ograniczenia Wykonawcze i Koszty")
skrajnia = st.sidebar.number_input("Wymagana skrajnia robocza palownicy (odstęp od krawędzi) [m]", value=1.0, step=0.1, min_value=0.0)
margines_platformy = st.sidebar.number_input("Margines platformy roboczej (wokół zbiornika) [m]", value=2.0, step=0.5)
grubosc_platformy = st.sidebar.number_input("Grubość warstwy kruszywa [m]", value=0.4, step=0.1)
pow_dojazdu = st.sidebar.number_input("Powierzchnia drogi dojazdowej [m²]", value=100.0, step=10.0)
cena_betonu_pal = st.sidebar.number_input("Cena betonu palowego z pompą [PLN/m³]", value=450.0, step=10.0)
cena_stali = st.sidebar.number_input("Cena stali zbrojeniowej [PLN/t]", value=4500.0, step=100.0)
cena_kruszywa = st.sidebar.number_input("Kruszywo platformy z wbudowaniem [PLN/m³]", value=130.0, step=5.0)
cena_wiercenia = st.sidebar.number_input("Wykonanie 1 mb pala (sprzęt+robocizna) [PLN/mb]", value=150.0, step=10.0)
cena_skuwania = st.sidebar.number_input("Skuwanie 1 głowicy pala [PLN/szt.]", value=180.0, step=10.0)

# Współczynniki częściowe
gamma_G_dst_upl = 1.0; gamma_G_stb_upl = 0.9; gamma_s_t = 1.15       
gamma_G_geo = 1.35; gamma_Q_geo = 1.50; gamma_s_c = 1.10; gamma_b_c = 1.10       
gamma_s_stal = 1.15 

# ==========================================
# WSPÓLNE OBLICZENIA GEOMETRII I CIĘŻARÓW
# ==========================================
V_zewnetrzna = L_z * B_z * H_z
V_wewnetrzna = (L_z - 2*grubosc) * (B_z - 2*grubosc) * (H_z - grubosc)
V_betonu = V_zewnetrzna - V_wewnetrzna

G_k_zbiornika = V_betonu * gamma_betonu
G_k_naziomu = L_z * B_z * h_naziomu * gamma_naziomu 
G_k_calkowite = G_k_zbiornika + G_k_naziomu

Q_k_wody_wewnatrz = V_wewnetrzna * gamma_wody
U_k_wypor = (L_z * B_z * H_wody) * gamma_wody
ciezar_1_pala_k = (np.pi * (D_pala**2) / 4) * L_pala * gamma_betonu

# Platforma (koszty stałe)
pow_platformy = (L_z + 2 * margines_platformy) * (B_z + 2 * margines_platformy)
obj_kruszywa = (pow_platformy + pow_dojazdu) * grubosc_platformy
koszt_kruszywo = obj_kruszywa * cena_kruszywa

# ==========================================
# FUNKCJE KORELACYJNE
# ==========================================
def koreluj_parametry(nazwa, parametr, organiczny):
    nazwa_lower = str(nazwa).lower()
    
    if organiczny or "torf" in nazwa_lower or "gytia" in nazwa_lower:
        return 5.0, 0.0, 2.0  
    
    if "piasek" in nazwa_lower or "żwir" in nazwa_lower or "pospółka" in nazwa_lower:
        id_val = max(0.1, min(parametr, 1.0))
        q_sk = 20.0 + (id_val - 0.2) * (100.0 - 20.0) / (0.8 - 0.2)
        q_bk = 500.0 + (id_val - 0.2) * (3500.0 - 500.0) / (0.8 - 0.2)
        m0 = 40.0 + (id_val - 0.2) * (150.0 - 40.0) / (0.8 - 0.2)
        return max(10.0, q_sk), max(100.0, q_bk), max(20.0, m0)
        
    elif "glin" in nazwa_lower or "ił" in nazwa_lower or "pył" in nazwa_lower:
        il_val = max(0.0, min(parametr, 0.7))
        q_sk = 60.0 - (il_val - 0.0) * (60.0 - 15.0) / (0.6 - 0.0)
        q_bk = 1200.0 - (il_val - 0.0) * (1200.0 - 200.0) / (0.6 - 0.0)
        m0 = 60.0 - (il_val - 0.0) * (60.0 - 10.0) / (0.6 - 0.0)
        return max(10.0, q_sk), max(100.0, q_bk), max(5.0, m0)
        
    else:
        return 15.0, 200.0, 20.0

# ==========================================
# TABELA WARSTW GRUNTOWYCH
# ==========================================
st.subheader("Profil Geotechniczny (od poziomu terenu 0.00 m)")
st.info(f"Dno wykopu (zbiornika) znajduje się na głębokości **{D_f:.2f} m**.")

if "Korelacja" in tryb_gruntu:
    domyslne_warstwy = pd.DataFrame({
        "Rodzaj gruntu": ["Nasyp", "Torf", "Piasek drobny", "Glina zwięzła"],
        "Miąższość [m]": [1.5, 2.5, 3.0, 5.0],
        "Stan (ID / IL)": [0.5, 0.0, 0.6, 0.2],
        "Organiczny?": [False, True, False, False]
    })
    df_wejscie = st.data_editor(domyslne_warstwy, num_rows="dynamic", width="stretch")
    
    # Generowanie df_grunt w tle
    df_grunt = df_wejscie.copy()
    q_sk_list, q_bk_list, m0_list = [], [], []
    for idx, row in df_wejscie.iterrows():
        q_sk, q_bk, m0 = koreluj_parametry(row["Rodzaj gruntu"], row["Stan (ID / IL)"], row["Organiczny?"])
        q_sk_list.append(q_sk)
        q_bk_list.append(q_bk)
        m0_list.append(m0)
        
    df_grunt["q_sk (pobocznica) [kPa]"] = q_sk_list
    df_grunt["q_bk (podstawa) [kPa]"] = q_bk_list
    df_grunt["M0 (ściśliwość) [MPa]"] = m0_list
    
    with st.expander("Podgląd wyznaczonych parametrów obliczeniowych (z korelacji)", expanded=True):
        st.dataframe(df_grunt[["Rodzaj gruntu", "Miąższość [m]", "q_sk (pobocznica) [kPa]", "q_bk (podstawa) [kPa]", "M0 (ściśliwość) [MPa]"]].style.format(precision=1), width="stretch", hide_index=True)

else:
    domyslne_warstwy = pd.DataFrame({
        "Rodzaj gruntu": ["Nasyp", "Torf", "Piasek drobny", "Glina zwięzła"],
        "Miąższość [m]": [1.5, 2.5, 3.0, 5.0],
        "q_sk (pobocznica) [kPa]": [15.0, 5.0, 73.3, 45.0],
        "q_bk (podstawa) [kPa]": [200.0, 0.0, 2500.0, 866.7],
        "M0 (ściśliwość) [MPa]": [20.0, 2.0, 113.3, 43.3],
        "Organiczny?": [False, True, False, False]
    })
    df_grunt = st.data_editor(domyslne_warstwy, num_rows="dynamic", width="stretch")

# ==========================================
# PĘTLA OBLICZENIOWA (GEO / UPL) - BIEŻĄCY WARIANT
# ==========================================
z_curr = 0.0
obwod_pala = np.pi * D_pala
pole_podstawy = np.pi * (D_pala**2) / 4

R_sk_wyciaganie = 0.0; R_sk_wciskanie = 0.0; F_nk_tarcie_neg = 0.0; R_bk_podstawa = 0.0    
nazwa_gruntu_podstawa = ""
raport_warstw = [] 

for idx, row in df_grunt.iterrows():
    miazszosc = row["Miąższość [m]"]
    start_pala_w_warstwie = max(z_curr, D_f)
    koniec_pala_w_warstwie = min(z_curr + miazszosc, D_f + L_pala)
    dl_w_warstwie = max(0.0, koniec_pala_w_warstwie - start_pala_w_warstwie)
    q_sk = row["q_sk (pobocznica) [kPa]"]
    organiczny = row["Organiczny?"]
    
    if dl_w_warstwie > 0:
        powierzchnia_segmentu = obwod_pala * dl_w_warstwie
        if organiczny: F_nk_tarcie_neg += powierzchnia_segmentu * q_sk
        else:
            R_sk_wyciaganie += powierzchnia_segmentu * q_sk * alfa_s
            R_sk_wciskanie += powierzchnia_segmentu * q_sk * alfa_s
            
        raport_warstw.append({"nazwa": row["Rodzaj gruntu"], "dlugosc": dl_w_warstwie, "q_sk": q_sk, "organiczny": organiczny})
        
    z_curr += miazszosc
    if z_curr >= D_f + L_pala and nazwa_gruntu_podstawa == "":
        R_bk_podstawa = pole_podstawy * row["q_bk (podstawa) [kPa]"]
        nazwa_gruntu_podstawa = row["Rodzaj gruntu"]

# ==========================================
# PĘTLA OBLICZENIOWA SGU ORAZ K_Z (MES)
# ==========================================
z_eq = D_f + (2/3) * L_pala  
B_eq = B_z + (L_pala / 3)    
L_eq = L_z + (L_pala / 3)    
N_k_sgu = G_k_calkowite + Q_k_wody_wewnatrz 

s_calkowite_mm = 0.0
z_curr_sgu = 0.0
raport_sgu = []

for idx, row in df_grunt.iterrows():
    miazszosc = row["Miąższość [m]"]
    M0_kPa = row["M0 (ściśliwość) [MPa]"] * 1000
    z_bottom = z_curr_sgu + miazszosc
    
    if z_bottom > z_eq:
        z_start = max(z_curr_sgu, z_eq)
        h_warstwy = z_bottom - z_start
        z_prim = (z_start + h_warstwy / 2) - z_eq 
        
        A_z = (B_eq + z_prim) * (L_eq + z_prim)
        sigma_z = N_k_sgu / A_z 
        s_i_mm = (sigma_z / M0_kPa) * h_warstwy * 1000
        s_calkowite_mm += s_i_mm
        raport_sgu.append({"nazwa": row["Rodzaj gruntu"], "h": h_warstwy, "z_prim": z_prim, "sigma": sigma_z, "M0": row["M0 (ściśliwość) [MPa]"], "s_i": s_i_mm})
        
    z_curr_sgu += miazszosc

N_k_1pal = N_k_sgu / liczba_pali if liczba_pali > 0 else 0
if s_calkowite_mm > 0:
    K_z_kN_m = N_k_1pal / (s_calkowite_mm / 1000.0)
    K_z_MN_m = K_z_kN_m / 1000.0
else:
    K_z_kN_m = 0.0; K_z_MN_m = 0.0

# ==========================================
# ZBROJENIE PALA I SIŁY UPL/GEO (GLOBALNE)
# ==========================================
# UPL
V_dst_d = U_k_wypor * gamma_G_dst_upl
G_stb_d = G_k_calkowite * gamma_G_stb_upl
R_td_1_pal = (R_sk_wyciaganie / gamma_s_t) + (ciezar_1_pala_k * gamma_G_stb_upl)
R_td_calkowite = R_td_1_pal * liczba_pali
suma_oporow = G_stb_d + R_td_calkowite
wykorzystanie_upl = (V_dst_d / suma_oporow) * 100 if suma_oporow > 0 else 999

# GEO
N_Ed_1_pal = ((G_k_calkowite + Q_k_wody_wewnatrz) * gamma_G_geo / liczba_pali) + (ciezar_1_pala_k * gamma_G_geo) + (F_nk_tarcie_neg * gamma_G_geo)
R_cd_1_pal = (R_sk_wciskanie / gamma_s_c) + (R_bk_podstawa / gamma_b_c)
wykorzystanie_geo = (N_Ed_1_pal / R_cd_1_pal) * 100 if R_cd_1_pal > 0 else 999

# Zbrojenie
N_Ed_t_1pal = max(0.0, (V_dst_d - G_stb_d) / liczba_pali)
f_yd = stal_fyk / gamma_s_stal
As_req = (N_Ed_t_1pal * 1000) / f_yd 
As_1_preta = np.pi * (phi_preta**2) / 4
n_pretow = max(6, int(np.ceil(As_req / As_1_preta))) 
As_prov = n_pretow * As_1_preta

# SGU
wykorzystanie_sgu = (s_calkowite_mm / s_max) * 100 if s_max > 0 else 999

# Koszty zmienne pali
mb_pali = liczba_pali * L_pala
obj_betonu_pali = mb_pali * pole_podstawy * 1.05 
masa_stali_pali_t = ((As_prov / 1e6) * L_pala * 7850 * liczba_pali) / 1000

koszt_beton = obj_betonu_pali * cena_betonu_pal
koszt_stal = masa_stali_pali_t * cena_stali
koszt_wiercenie = mb_pali * cena_wiercenia
koszt_skuwanie = liczba_pali * cena_skuwania
koszt_calkowity = koszt_kruszywo + koszt_beton + koszt_stal + koszt_wiercenie + koszt_skuwanie


# ==========================================
# FUNKCJE RYSUJĄCE CAD Z WYMIAROWANIEM
# ==========================================
def dobierz_kolor_gruntu(nazwa, organiczny):
    nazwa_lower = str(nazwa).lower()
    if organiczny or "torf" in nazwa_lower or "gytia" in nazwa_lower: return "#5C4033"  
    elif "piasek" in nazwa_lower or "żwir" in nazwa_lower or "pospółka" in nazwa_lower: return "#F4D03F" 
    elif "glin" in nazwa_lower or "ił" in nazwa_lower or "pył" in nazwa_lower: return "#D35400"  
    elif "nasyp" in nazwa_lower: return "#95A5A6" 
    else: return "#E3C29E" 

def generuj_przekroj(B, H, h_naz, D_f_rys, H_w, D_p, L_p, grunty):
    fig, ax = plt.subplots(figsize=(9, 10), dpi=300)
    szer_rys = B + 8  
    x_min, x_max = -szer_rys/2, szer_rys/2
    y_top = 0.0
    
    for idx, row in grunty.iterrows():
        miazsz = row["Miąższość [m]"]
        org = row["Organiczny?"]
        kolor = dobierz_kolor_gruntu(row["Rodzaj gruntu"], org)
        
        ax.add_patch(patches.Rectangle((x_min, y_top - miazsz), x_max - x_min, miazsz, linewidth=1, edgecolor='black', facecolor=kolor, hatch="///" if org else "", alpha=0.6))
        ax.text(x_max - 0.5, y_top - miazsz/2, f"{row['Rodzaj gruntu']}\n({miazsz} m)", va='center', ha='right', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
        y_top -= miazsz
        if y_top < -D_f_rys - L_p - 2.0: break 
        
    ax.add_patch(patches.Rectangle((-B/2, -D_f_rys), B, H, linewidth=2, edgecolor='black', facecolor='#D3D3D3', zorder=3))
    ax.add_patch(patches.Rectangle((-B/2 + grubosc, -D_f_rys + grubosc), B - 2*grubosc, H - grubosc, linewidth=2, edgecolor='black', facecolor='white', zorder=4))
    
    poziom_wody_y = -D_f_rys + H_w
    if H_w > 0:
        ax.add_patch(patches.Rectangle((x_min, y_top), x_max - x_min, poziom_wody_y - y_top, color='#1E90FF', alpha=0.3, zorder=2))
        ax.plot([-B/2 - 1.2, -B/2 - 0.8], [poziom_wody_y, poziom_wody_y], color='blue', zorder=5) 
        ax.plot([-B/2 - 1.2, -B/2 - 1.0, -B/2 - 0.8], [poziom_wody_y, poziom_wody_y - 0.2, poziom_wody_y], color='blue', zorder=5) 
        ax.text(-B/2 - 1.0, poziom_wody_y + 0.1, "WGW", color='blue', ha='center', fontsize=8, fontweight='bold', zorder=5)
        
    rozstaw = max(0.1, B - 2*skrajnia)
    for x_p in [-rozstaw/2, rozstaw/2]:
        ax.add_patch(patches.Rectangle((x_p - D_p/2, -D_f_rys - L_p), D_p, L_p, linewidth=1.5, edgecolor='black', facecolor='#696969', zorder=3))
        
    ax.axvline(0, color='red', linestyle='-.', linewidth=1, alpha=0.7, zorder=6)
    ax.axhline(0, color='green', linewidth=2, linestyle='--', zorder=5)
    ax.text(x_min + 0.5, 0.2, "Poziom terenu (0.00)", color='green', fontweight='bold')

    def wymiar_pion(x, y1, y2, text):
        ax.annotate('', xy=(x, y1), xytext=(x, y2), arrowprops=dict(arrowstyle='<->', color='black', lw=1.2))
        ax.text(x - 0.2, (y1+y2)/2, text, rotation=90, ha='right', va='center', fontsize=8, fontweight='bold', bbox=dict(fc='white', ec='none', pad=1))
        
    wymiar_pion(-B/2 - 2.0, -D_f_rys, -D_f_rys + H, f"H_z = {H:.2f} m")
    wymiar_pion(-B/2 - 3.0, -D_f_rys, 0, f"D_f = {D_f_rys:.2f} m")
    wymiar_pion(-rozstaw/2 - D_p/2 - 1.0, -D_f_rys - L_p, -D_f_rys, f"L_p = {L_p:.2f} m")
    if H_w > 0: wymiar_pion(B/2 + 1.0, -D_f_rys, poziom_wody_y, f"H_wody = {H_w:.2f} m")
    
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(min(y_top, -D_f_rys - L_p - 2.0), 1.5)
    ax.set_aspect('equal') 
    ax.axis('off')
    return fig

def generuj_rzut(L, B, grub, D_p, n, akt_skrajnia):
    fig_w, fig_h = 10, max(5, min(12, 10 * (B/L)))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=300)
    ax.axhline(0, color='red', linestyle='-.', linewidth=1.2, alpha=0.6, zorder=1)
    ax.axvline(0, color='red', linestyle='-.', linewidth=1.2, alpha=0.6, zorder=1)
    
    # Obrys zbiornika
    ax.add_patch(patches.Rectangle((-L/2, -B/2), L, B, lw=2, ec='black', fc='none', zorder=3))
    ax.add_patch(patches.Rectangle((-L/2 + grub, -B/2 + grub), L - 2*grub, B - 2*grub, lw=2, ec='black', fc='none', zorder=3))
    ax.add_patch(patches.Rectangle((-L/2, -B/2), L, B, lw=0, fc='#D3D3D3', hatch='//', alpha=0.6, zorder=2))
    ax.add_patch(patches.Rectangle((-L/2 + grub, -B/2 + grub), L - 2*grub, B - 2*grub, lw=0, fc='white', zorder=3))
    
    # Rysowanie skrajni roboczej głowicy
    L_eff = max(0.0, L - 2*akt_skrajnia)
    B_eff = max(0.0, B - 2*akt_skrajnia)
    if L_eff > 0 and B_eff > 0:
        ax.add_patch(patches.Rectangle((-L_eff/2, -B_eff/2), L_eff, B_eff, lw=1.5, ec='blue', ls=':', fc='none', zorder=4))
        ax.text(0, -B_eff/2 + 0.15, f"Granica robocza palownicy (skrajnia {akt_skrajnia} m)", color='blue', fontsize=8, ha='center', va='bottom', alpha=0.8, zorder=5)

    ny = max(1, int(np.round(np.sqrt(n * B/L))))
    if ny > n: ny = n
    counts = [n // ny] * ny
    for i in range(n % ny): counts[i // 2 if i % 2 == 0 else -(i // 2 + 1)] += 1
    
    y_coords = np.linspace(-B_eff/2, B_eff/2, ny) if ny > 1 else [0]
    
    for i, y in enumerate(y_coords):
        count = counts[i]
        x_coords = np.linspace(-L_eff/2, L_eff/2, count) if count > 1 else [0]
        for x in x_coords:
            ax.add_patch(patches.Circle((x, y), radius=D_p/2, lw=1.5, ec='black', fc='#696969', zorder=6))
            ax.plot([x - D_p/1.2, x + D_p/1.2], [y, y], color='black', lw=0.6, zorder=7)
            ax.plot([x, x], [y - D_p/1.2, y + D_p/1.2], color='black', lw=0.6, zorder=7)
            
    def wymiar(x1, y1, x2, y2, text, offset_x=0.0, offset_y=0.0, rot=0):
        ax.annotate('', xy=(x1, y1), xytext=(x2, y2), arrowprops=dict(arrowstyle='<->', color='black', lw=1.2))
        mx, my = (x1+x2)/2 + offset_x, (y1+y2)/2 + offset_y
        ax.text(mx, my, text, ha='center', va='center', rotation=rot, fontsize=8, fontweight='bold', bbox=dict(fc='white', ec='none', pad=1))

    ax.plot([-L/2, -L/2], [B/2, B/2 + 1.5], color='gray', lw=1, ls='--')
    ax.plot([L/2, L/2], [B/2, B/2 + 1.5], color='gray', lw=1, ls='--')
    wymiar(-L/2, B/2 + 1.2, L/2, B/2 + 1.2, f"L = {L:.2f} m")
    ax.plot([-L/2, -L/2 - 1.5], [-B/2, -B/2], color='gray', lw=1, ls='--')
    ax.plot([-L/2, -L/2 - 1.5], [B/2, B/2], color='gray', lw=1, ls='--')
    wymiar(-L/2 - 1.2, -B/2, -L/2 - 1.2, B/2, f"B = {B:.2f} m", rot=90)

    ax.set_xlim(-L/2 - 2.5, L/2 + 2.5)
    ax.set_ylim(-B/2 - 2.5, B/2 + 2.5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

fig_przekroj = generuj_przekroj(B_z, H_z, h_naziomu, D_f, H_wody, D_pala, L_pala, df_grunt)
fig_rzut = generuj_rzut(L_z, B_z, grubosc, D_pala, liczba_pali, skrajnia)

# ==========================================
# WYNIKI - ZAKŁADKI (9 ZAKŁADEK)
# ==========================================
tab_upl, tab_geo, tab_sgu, tab_zbrojenie, tab_koszty, tab_przekroj, tab_rzut, tab_raport, tab_optymalizator = st.tabs([
    "△ Stan UPL", "▽ Stan GEO", "◯ Stan SGU", "▤ Zbrojenie", "◇ Kosztorys", "◧ Przekrój A-A", "◻ Rzut Płyty", "☰ Raport", "◈ Moduł Optymalizacji"
])

with tab_upl:
    st.subheader("Analiza Wyporu (Stan Graniczny UPL)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Wypór Wody (V_dst)", f"{V_dst_d:.0f} kN")
    col2.metric("Ciężar (Zbiornik + Naziom)", f"{G_stb_d:.0f} kN")
    col3.metric(f"Nośność Pali ({liczba_pali} szt.)", f"{R_td_calkowite:.0f} kN")
    
    if V_dst_d <= suma_oporow: 
        st.success("WARUNEK UPL SPEŁNIONY. Konstrukcja wykazuje wymaganą stabilność.")
    else: 
        st.error(f"NIESPEŁNIONY WARUNEK UPL. Deficyt nośności: {V_dst_d - suma_oporow:.0f} kN.")
        
    st.progress(min(wykorzystanie_upl / 100, 1.0))
    st.caption(f"**Wykorzystanie stanu granicznego UPL:** {wykorzystanie_upl:.1f}%")

with tab_geo:
    st.subheader("Analiza Nośności Gruntu na Wciskanie (Stan Graniczny GEO)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Masa Całkowita Obiektu", f"{(G_k_calkowite + Q_k_wody_wewnatrz):.0f} kN")
    col2.metric("Obciążenie 1 pala (N_Ed)", f"{N_Ed_1_pal:.0f} kN")
    col3.metric("Nośność 1 pala (R_cd)", f"{R_cd_1_pal:.0f} kN")
    
    if N_Ed_1_pal <= R_cd_1_pal: 
        st.success("WARUNEK GEO SPEŁNIONY. Zapewniono nośność gruntu.")
    else: 
        st.error(f"NIESPEŁNIONY WARUNEK GEO. Przekroczenie nośności o {N_Ed_1_pal - R_cd_1_pal:.0f} kN.")
        
    st.progress(min(wykorzystanie_geo / 100, 1.0))
    st.caption(f"**Wykorzystanie stanu granicznego GEO:** {wykorzystanie_geo:.1f}%")

with tab_sgu:
    st.subheader("Osiadanie Grupy Pali (Metoda Fundamentu Zastępczego)")
    st.write("W obliczeniach SGU przyjmuje się obciążenia charakterystyczne (bez współczynników).")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Osiadanie całkowite (s)", f"{s_calkowite_mm:.1f} mm")
    col2.metric("Dopuszczalne (s_max)", f"{s_max:.1f} mm")
    col3.metric("Obciążenie blokowe (N_k)", f"{N_k_sgu:.0f} kN")
    
    if s_calkowite_mm <= s_max: 
        st.success("WARUNEK SGU SPEŁNIONY. Osiadania w granicach dopuszczalnych.")
    else: 
        st.error(f"NIESPEŁNIONY WARUNEK SGU. Przekroczenie wartości osiadań dopuszczalnych.")
        
    st.progress(min(wykorzystanie_sgu / 100, 1.0))
    st.caption(f"**Wykorzystanie stanu granicznego SGU:** {wykorzystanie_sgu:.1f}%")
    
    st.write("---")
    st.markdown("### Parametry dla środowiska MES (np. Robot Structural Analysis)")
    if K_z_kN_m > 0:
        st.info(f"Wyliczona sztywność sprężysta podpory punktowej (pala) z prawa Hooke'a: **$K_z$ = {K_z_kN_m:,.0f} kN/m** ({K_z_MN_m:.1f} MN/m)")
    else:
        st.info("Sztywność sprężysta: Brak osiadania (można przyjąć podporę idealnie sztywną).")

with tab_zbrojenie:
    st.subheader("Dobór zbrojenia podłużnego pala na rozciąganie")
    col1, col2, col3 = st.columns(3)
    col1.metric("Siła wyrywająca 1 pala", f"{N_Ed_t_1pal:.1f} kN")
    col2.metric("Wymagane zbrojenie", f"{As_req:.1f} mm²")
    col3.metric(f"Przyjęto pręty", f"{n_pretow} szt. ∅ {phi_preta}")
    
    if N_Ed_t_1pal > 0: 
        st.success(f"Dobrane zbrojenie: {n_pretow} prętów $\\phi$ {phi_preta} mm. Wyznaczone pole przekroju ($A_{{s,prov}}$ = {As_prov:.1f} mm²) spełnia warunek $A_{{s,prov}} \\ge A_{{s,req}}$ ({As_req:.1f} mm²).")
    else: 
        st.success(f"Zbrojenie ze względu na siły wyciągające niewymagane. Przyjęto zbrojenie konstrukcyjne: {n_pretow} prętów $\\phi$ {phi_preta} mm.")

with tab_koszty:
    st.subheader("Szacunkowy Przedmiar i Kosztorys Robót Palowych")
    dane_kosztorys = {
        "Pozycja kosztorysowa": [
            "Platforma robocza i dojazd (Kruszywo)", 
            "Betonowanie pali (uwzgl. 5% nadbetonu)",
            "Zbrojenie pali (Stal podłużna)", 
            "Wiercenie pali (Sprzęt i Robocizna)", 
            "Skuwanie głowic pali"
        ],
        "Ilość": [
            f"{obj_kruszywa:.1f} m³", f"{obj_betonu_pali:.1f} m³", f"{masa_stali_pali_t:.2f} t",
            f"{mb_pali:.1f} mb", f"{liczba_pali} szt."
        ],
        "Cena Jednostkowa": [
            f"{cena_kruszywa:.2f} PLN/m³", f"{cena_betonu_pal:.2f} PLN/m³", f"{cena_stali:.2f} PLN/t",
            f"{cena_wiercenia:.2f} PLN/mb", f"{cena_skuwania:.2f} PLN/szt."
        ],
        "Wartość Netto [PLN]": [koszt_kruszywo, koszt_beton, koszt_stal, koszt_wiercenie, koszt_skuwanie]
    }
    st.dataframe(pd.DataFrame(dane_kosztorys).style.format({"Wartość Netto [PLN]": "{:,.2f}"}), width="stretch", hide_index=True)
    st.markdown(f"### Całkowity Szacunkowy Koszt Robót: {koszt_calkowity:,.2f} PLN netto")

with tab_przekroj: st.pyplot(fig_przekroj, use_container_width=False)
with tab_rzut: st.pyplot(fig_rzut, use_container_width=False)

with tab_raport:
    st.header("📄 Szczegółowy Raport Obliczeniowy")
    st.markdown(f"**Data wygenerowania:** {datetime.datetime.now().strftime('%Y-%m-%d')} | **Projektant:** Damian Kubiak, student ZUT")
    st.divider()

    st.subheader("Część 1: Sprawdzenie stanu granicznego UPL (Zbiornik pusty)")
    st.write("Analiza przeprowadzona dla schematu pustego zbiornika, poddanego maksymalnemu ciśnieniu hydrostatycznemu. Sprawdzamy, czy siła wyporu jest równoważona przez ciężar własny oraz nośność pobocznicy pali na wyciąganie.")
    
    st.markdown("**1.1 Obliczeniowa siła destabilizująca (wypór):**")
    st.latex(r"V_{dst,d} = L \cdot B \cdot H_{wody} \cdot \gamma_{wody} \cdot \gamma_{G,dst}")
    st.latex(rf"V_{{dst,d}} = {L_z:.2f} \cdot {B_z:.2f} \cdot {H_wody:.2f} \cdot {gamma_wody:.1f} \cdot {gamma_G_dst_upl:.2f} = \mathbf{{{V_dst_d:.2f} \text{{ kN}}}}")
    
    st.markdown("**1.2 Obliczeniowy ciężar stabilizujący (konstrukcja + naziom):**")
    st.latex(r"G_{stb,d} = (V_{betonu} \cdot \gamma_{betonu} + V_{naziomu} \cdot \gamma_{naziomu}) \cdot \gamma_{G,stb}")
    st.latex(rf"G_{{stb,d}} = ({V_betonu:.2f} \cdot {gamma_betonu:.1f} + {(L_z * B_z * h_naziomu):.2f} \cdot {gamma_naziomu:.1f}) \cdot {gamma_G_stb_upl:.2f} = \mathbf{{{G_stb_d:.2f} \text{{ kN}}}}")
    
    st.markdown("**1.3 Sumaryczny opór pali na wyciąganie:**")
    st.latex(r"R_{td,calk} = n \cdot \left( \frac{\sum (\pi \cdot D \cdot h_i \cdot q_{ski} \cdot \alpha_s)}{\gamma_{s,t}} + G_{pala} \cdot \gamma_{G,stb} \right)")
    st.latex(rf"R_{{td,calk}} = {liczba_pali} \cdot \left( \frac{{{R_sk_wyciaganie:.2f}}}{{{gamma_s_t:.2f}}} + {ciezar_1_pala_k:.2f} \cdot {gamma_G_stb_upl:.2f} \right) = \mathbf{{{R_td_calkowite:.2f} \text{{ kN}}}}")
    
    st.markdown("**1.4 Warunek nośności UPL:**")
    st.latex(r"V_{dst,d} \le G_{stb,d} + R_{td,calk}")
    if V_dst_d <= suma_oporow:
        st.latex(rf"{V_dst_d:.2f} \text{{ kN}} \le {suma_oporow:.2f} \text{{ kN}} \quad \Rightarrow \quad \textbf{{WARUNEK SPEŁNIONY}}")
    else:
        st.latex(rf"{V_dst_d:.2f} \text{{ kN}} > {suma_oporow:.2f} \text{{ kN}} \quad \Rightarrow \quad \textbf{{WARUNEK NIE SPEŁNIONY}}")

    st.divider()

    st.subheader("Część 2: Sprawdzenie stanu granicznego GEO (Zbiornik pełny)")
    st.write("Analiza nośności pionowej wciskanego pala dla pełnego zbiornika. Dodatkowo uwzględniono tarcie negatywne od osiadających warstw organicznych (jeśli występują).")
    
    st.markdown("**2.1 Maksymalna siła wciskająca na 1 pal:**")
    st.latex(r"N_{Ed} = \frac{(G_{k} \cdot \gamma_G + Q_{wody} \cdot \gamma_Q)}{n} + G_{pal} \cdot \gamma_G + F_{neg} \cdot \gamma_G")
    st.latex(rf"N_{{Ed}} = \frac{{({G_k_calkowite:.2f} \cdot {gamma_G_geo:.2f} + {Q_k_wody_wewnatrz:.2f} \cdot {gamma_Q_geo:.2f})}}{{{liczba_pali}}} + {ciezar_1_pala_k:.2f} \cdot {gamma_G_geo:.2f} + {F_nk_tarcie_neg:.2f} \cdot {gamma_G_geo:.2f} = \mathbf{{{N_Ed_1_pal:.2f} \text{{ kN}}}}")
    
    st.markdown("**2.2 Obliczeniowa nośność pala na wciskanie (pobocznica + podstawa):**")
    st.latex(r"R_{cd} = \frac{R_{sk,wciskanie}}{\gamma_{s,c}} + \frac{R_{bk,podstawa}}{\gamma_{b,c}}")
    st.latex(rf"R_{{cd}} = \frac{{{R_sk_wciskanie:.2f}}}{{{gamma_s_c:.2f}}} + \frac{{{R_bk_podstawa:.2f}}}{{{gamma_b_c:.2f}}} = \mathbf{{{R_cd_1_pal:.2f} \text{{ kN}}}}")
    
    st.markdown("**2.3 Warunek nośności GEO:**")
    st.latex(r"N_{Ed} \le R_{cd}")
    if N_Ed_1_pal <= R_cd_1_pal:
        st.latex(rf"{N_Ed_1_pal:.2f} \text{{ kN}} \le {R_cd_1_pal:.2f} \text{{ kN}} \quad \Rightarrow \quad \textbf{{WARUNEK SPEŁNIONY}}")
    else:
        st.latex(rf"{N_Ed_1_pal:.2f} \text{{ kN}} > {R_cd_1_pal:.2f} \text{{ kN}} \quad \Rightarrow \quad \textbf{{WARUNEK NIE SPEŁNIONY}}")

    st.divider()

    st.subheader("Część 3: Osiadanie i Sztywność MES (SGU)")
    if raport_sgu:
        df_raport_sgu = pd.DataFrame(raport_sgu)
        df_raport_sgu.columns = ["Warstwa Gruntu", "Miąższość h [m]", "Głębokość z' [m]", "Naprężenie σ_z [kPa]", "Moduł M0 [MPa]", "Osiadanie s_i [mm]"]
        st.dataframe(df_raport_sgu.style.format(precision=2), width="stretch", hide_index=True)
        st.latex(rf"s = \sum s_i = \mathbf{{{s_calkowite_mm:.2f} \text{{ mm}}}}")
    else:
        st.write("*Brak zdefiniowanych warstw ściśliwych poniżej fundamentu zastępczego.*")
        
    st.divider()

    st.subheader("Część 4: Dobór zbrojenia podłużnego na rozciąganie (SGN - Eurokod 2)")
    if N_Ed_t_1pal > 0:
        st.latex(r"N_{Ed,t} = \frac{V_{dst,d} - G_{stb,d}}{n}")
        st.latex(rf"N_{{Ed,t}} = \frac{{{V_dst_d:.2f} - {G_stb_d:.2f}}}{{{liczba_pali}}} = \mathbf{{{N_Ed_t_1pal:.2f} \text{{ kN}}}}")
        
        st.latex(r"A_{s,req} = \frac{N_{Ed,t}}{f_{yd}}")
        st.latex(rf"A_{{s,req}} = \frac{{{N_Ed_t_1pal:.2f} \cdot 10^3}}{{{f_yd:.2f}}} = \mathbf{{{As_req:.2f} \text{{ mm}}^2}}")
        
        st.write(rf"Zaprojektowano zbrojenie z prętów o średnicy $\phi = {phi_preta} \text{{ mm}}$:")
        st.latex(rf"n_{{prętów}} = \lceil \frac{{A_{{s,req}}}}{{A_{{s,1}}}} \rceil = {n_pretow} \text{{ sztuk}} \quad \Rightarrow \quad A_{{s,prov}} = {As_prov:.1f} \text{{ mm}}^2")
    else:
        st.write("Obliczeniowa siła wyporu jest mniejsza od obliczeniowego ciężaru zbiornika z naziomem. Pale nie są rozciągane, przyjmuje się zbrojenie konstrukcyjne.")

# ==========================================
# ZAKŁADKA 9: OPTYMALIZATOR Z INŻYNIERSKIMI WNIOSKAMI
# ==========================================
with tab_optymalizator:
    st.header("Moduł Optymalizacji Rozkładu Posadowienia")
    st.markdown("Algorytm generuje kombinacje siatek, odrzucając te naruszające rozstaw normowy **3D** oraz wprowadzoną z paska bocznego **skrajnię palownicy** (odległość osi narzędzia od brzegu wykopu).")
    
    col_opt1, col_opt2, col_opt3 = st.columns(3)
    with col_opt1: opt_d_list = st.multiselect("Testowane średnice D [m]", [0.3, 0.4, 0.5, 0.6, 0.8], default=[0.4, 0.5, 0.6])
    with col_opt2: 
        opt_l_min = st.number_input("Minimalna długość L [m]", value=4.0, step=0.5)
        opt_l_max = st.number_input("Maksymalna długość L [m]", value=12.0, step=0.5)
    with col_opt3:
        opt_n_min = st.number_input("Min. liczba pali [szt.]", value=4, step=2)
        opt_n_max = st.number_input("Max. liczba pali [szt.]", value=30, step=2)

    if st.button("Uruchom Procedurę Optymalizacji", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def evaluate_scenario(d_p, l_p, n_p):
            obwod = np.pi * d_p
            pole = np.pi * (d_p**2) / 4
            ciezar_1_p = pole * l_p * gamma_betonu
            
            l_eff_opt = max(0.0, L_z - 2 * skrajnia)
            b_eff_opt = max(0.0, B_z - 2 * skrajnia)
            if l_eff_opt > 0 and b_eff_opt > 0:
                max_x = int(l_eff_opt / (3 * d_p)) + 1
                max_y = int(b_eff_opt / (3 * d_p)) + 1
                max_pali = max_x * max_y
            else:
                max_pali = 0
                
            if n_p > max_pali: return False, "ZBYT GĘSTO", None
            
            r_sk_wyc = 0.0; r_sk_wci = 0.0; f_nk_neg = 0.0; r_bk = 0.0
            z_c = 0.0; nazwa_podst = ""
            for i, r in df_grunt.iterrows():
                miaz = r["Miąższość [m]"]
                start = max(z_c, D_f)
                koniec = min(z_c + miaz, D_f + l_p)
                dl = max(0.0, koniec - start)
                if dl > 0:
                    pow_s = obwod * dl
                    if r["Organiczny?"]: f_nk_neg += pow_s * r["q_sk (pobocznica) [kPa]"]
                    else: 
                        r_sk_wyc += pow_s * r["q_sk (pobocznica) [kPa]"] * alfa_s
                        r_sk_wci += pow_s * r["q_sk (pobocznica) [kPa]"] * alfa_s
                z_c += miaz
                if z_c >= D_f + l_p and nazwa_podst == "": r_bk = pole * r["q_bk (podstawa) [kPa]"]

            r_td_1 = (r_sk_wyc / gamma_s_t) + (ciezar_1_p * gamma_G_stb_upl)
            suma_op = G_stb_d + (r_td_1 * n_p)
            if V_dst_d > suma_op: return False, "AWARIA UPL", None
            
            n_ed_1 = ((G_k_calkowite + Q_k_wody_wewnatrz) * gamma_G_geo / n_p) + (ciezar_1_p * gamma_G_geo) + (f_nk_neg * gamma_G_geo)
            r_cd_1 = (r_sk_wci / gamma_s_c) + (r_bk / gamma_b_c)
            if n_ed_1 > r_cd_1: return False, "AWARIA GEO", None
            
            z_eq_opt = D_f + (2/3) * l_p
            b_eq_opt = B_z + (l_p / 3)
            l_eq_opt = L_z + (l_p / 3)
            s_calk = 0.0
            z_c_sgu = 0.0
            for i, r in df_grunt.iterrows():
                miaz = r["Miąższość [m]"]
                z_b = z_c_sgu + miaz
                if z_b > z_eq_opt:
                    z_start = max(z_c_sgu, z_eq_opt)
                    h_w = z_b - z_start
                    z_prim = (z_start + h_w / 2) - z_eq_opt
                    a_z = (b_eq_opt + z_prim) * (l_eq_opt + z_prim)
                    s_calk += ((N_k_sgu / a_z) / (r["M0 (ściśliwość) [MPa]"] * 1000)) * h_w * 1000
                z_c_sgu += miaz
            if s_calk > s_max: return False, "AWARIA SGU", None
            
            n_ed_t_1 = max(0.0, (V_dst_d - G_stb_d) / n_p)
            n_pret_opt = max(6, int(np.ceil(((n_ed_t_1 * 1000) / f_yd) / (np.pi * (phi_preta**2) / 4))))
            as_prov_opt = n_pret_opt * (np.pi * (phi_preta**2) / 4)
            obj_b = n_p * l_p * pole * 1.05
            masa_s = ((as_prov_opt / 1e6) * l_p * 7850 * n_p) / 1000
            
            k = koszt_kruszywo + (obj_b * cena_betonu_pal) + (masa_s * cena_stali) + (n_p * l_p * cena_wiercenia) + (n_p * cena_skuwania)

            return True, "OK", {
                "Koszt Całkowity [PLN]": k, "Liczba pali [szt.]": n_p, "Średnica D [m]": d_p, "Długość L [m]": l_p,
                "Wypór UPL [%]": (V_dst_d / suma_op) * 100, "Nośność GEO [%]": (n_ed_1 / r_cd_1) * 100, "Osiadanie [mm]": s_calk
            }

        wyniki = []
        statystyki = {"suma": 0, "upl": 0, "geo": 0, "sgu": 0, "gesto": 0, "ok": 0}
        dlugosci = np.arange(opt_l_min, opt_l_max + 0.1, 0.5)
        ilosci = range(int(opt_n_min), int(opt_n_max) + 1, 2) 
        
        total_steps = len(opt_d_list) * len(dlugosci) * len(ilosci)
        current_step = 0
        
        for d in opt_d_list:
            for l in dlugosci:
                for n in ilosci:
                    statystyki["suma"] += 1
                    sukces, powod, dane = evaluate_scenario(d, l, n)
                    if sukces:
                        statystyki["ok"] += 1
                        wyniki.append(dane)
                    else:
                        if powod == "AWARIA UPL": statystyki["upl"] += 1
                        elif powod == "AWARIA GEO": statystyki["geo"] += 1
                        elif powod == "AWARIA SGU": statystyki["sgu"] += 1
                        elif powod == "ZBYT GĘSTO": statystyki["gesto"] += 1
                    
                    current_step += 1
                    if current_step % 10 == 0:
                        progress_bar.progress(current_step / total_steps)
                        status_text.text(f"Analizuję wariant {current_step} z {total_steps}...")

        progress_bar.progress(1.0)
        status_text.empty()
        
        st.success(f"Procedura zakończona. Przeprowadzono analizę dla {statystyki['suma']} wariantów uwzględniających rygor przestrzenny.")
        st.write(f"Warianty odrzucone - Kryteria: UPL ({statystyki['upl']}), GEO ({statystyki['geo']}), SGU ({statystyki['sgu']}), Ograniczenia przestrzenne ({statystyki['gesto']}).")
        
        if statystyki["ok"] > 0:
            df_wyniki = pd.DataFrame(wyniki)
            df_wyniki = df_wyniki.sort_values(by="Koszt Całkowity [PLN]").reset_index(drop=True)
            
            st.markdown("### Zestawienie 10 najbardziej uzasadnionych ekonomicznie wariantów spełniających warunki projektowe:")
            st.dataframe(df_wyniki.head(10).style.format({
                "Koszt Całkowity [PLN]": "{:,.2f}", "Wypór UPL [%]": "{:.1f}%", "Nośność GEO [%]": "{:.1f}%", "Osiadanie [mm]": "{:.1f}"
            }), width="stretch")
            
            # --- MODUŁ AUTOMATYCZNYCH WNIOSKÓW ---
            najlepszy = df_wyniki.iloc[0]
            
            delta_koszt = koszt_calkowity - najlepszy['Koszt Całkowity [PLN]']
            delta_n = najlepszy['Liczba pali [szt.]'] - liczba_pali
            delta_l = najlepszy['Długość L [m]'] - L_pala
            delta_d = najlepszy['Średnica D [m]'] - D_pala

            rez_geo_baza = 100 - min(wykorzystanie_geo, 100)
            rez_geo_opt = 100 - najlepszy['Nośność GEO [%]']
            delta_rez_geo = rez_geo_opt - rez_geo_baza
            
            st.markdown("---")
            st.markdown("### Moduł Syntezy Wniosków Projektowych")
            st.write("Skopiuj poniższy wygenerowany wniosek do swojego podsumowania projektu:")
            
            wnioski = []
            
            # Wniosek o kosztach
            if delta_koszt > 0:
                wnioski.append(f"Zastosowanie iteracyjnego algorytmu optymalizacyjnego z uwzględnieniem ograniczeń kinematycznych palownicy pozwoliło na redukcję szacunkowych kosztów posadowienia o **{delta_koszt:,.2f} PLN netto** w stosunku do wariantu wyjściowego.")
            elif delta_koszt < 0:
                wnioski.append(f"Wyjściowy wariant posadowienia nie spełniał kryteriów normowych lub rygoru przestrzennego. Do zapewnienia pełnego bezpieczeństwa konstrukcji niezbędna była korekta zwiększająca budżet o **{abs(delta_koszt):,.2f} PLN netto**.")
            else:
                wnioski.append("Ręcznie zaprojektowany wariant wyjściowy okazał się tożsamy z najlepszym wynikiem algorytmu pod względem kosztów, co dowodzi optymalnego doboru parametrów początkowych.")
                
            # Wniosek o geometrii
            zmiany_geom = []
            if delta_n != 0:
                kier = "zwiększono" if delta_n > 0 else "zredukowano"
                zmiany_geom.append(f"{kier} liczbę pali z {int(liczba_pali)} do {int(najlepszy['Liczba pali [szt.]'])} szt.")
            if delta_l != 0:
                kier = "wydłużono" if delta_l > 0 else "skrócono"
                zmiany_geom.append(f"{kier} ich długość czynną z {L_pala:.1f} m do {najlepszy['Długość L [m]']:.1f} m")
            if delta_d != 0:
                kier = "zwiększono" if delta_d > 0 else "zmniejszono"
                zmiany_geom.append(f"{kier} projektowaną średnicę świdra na {najlepszy['Średnica D [m]']:.2f} m")

            if zmiany_geom:
                wnioski.append(f"Efekt ten osiągnięto poprzez modyfikację geometrii fundamentu w przestrzeni 3D: " + ", ".join(zmiany_geom) + ".")
                
            # Wniosek o mechanice gruntów
            if wykorzystanie_geo > 100 or wykorzystanie_upl > 100 or wykorzystanie_sgu > 100:
                wnioski.append(f"Najważniejszym osiągnięciem optymalizacji było wyprowadzenie układu ze stanu awaryjnego. Wariant docelowy charakteryzuje się bezpiecznym wykorzystaniem nośności GEO na poziomie **{najlepszy['Nośność GEO [%]']:.1f}%** oraz stabilnością na wypór (UPL na poziomie **{najlepszy['Wypór UPL [%]']:.1f}%**).")
            else:
                if delta_rez_geo > 0:
                    wnioski.append(f"Powyższe zabiegi pozwoliły nie tylko na optymalizację kosztów, ale również na wzrost zapasu nośności gruntu o **{delta_rez_geo:.1f} punktu procentowego**, zwiększając ogólny margines bezpieczeństwa posadowienia.")
                elif delta_rez_geo < 0:
                    wnioski.append(f"Jednocześnie zoptymalizowano wykorzystanie nośności podłoża (GEO), redukując przewymiarowanie inżynierskie o **{abs(delta_rez_geo):.1f} punktu procentowego**, co bezpośrednio przełożyło się na oszczędności materiałowe przy pełnym zachowaniu rygorów normowych.")

            for wniosek in wnioski:
                st.info(wniosek)

        else:
            st.warning("Uwaga: Parametry maszyny roboczej uniemożliwiają realizację układu przy zdefiniowanych obciążeniach. Wymagana redukcja skrajni narzędzia lub zwiększenie głębokości posadowienia pośredniego.")
