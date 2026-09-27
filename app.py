import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
import time
from backend import (
    aggiungi_abitudine, 
    get_tutte_abitudini, 
    registra_log, 
    get_log_abitudini,
    elimina_abitudine
)

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Habit Tracker Personale", page_icon="🎯", layout="wide")

st.title("🎯 Il mio Habit Tracker")
st.markdown("Monitora le tue abitudini con percentuali ponderate e traguardi giornalieri. Per aggiungere abitudini premi >> in alto a sinistra")

# Inizializzazione dello stato per il lampo di colore del pulsante
if 'success_flash' not in st.session_state:
    st.session_state['success_flash'] = False

# Se il flag è attivo, iniettiamo il CSS per colorare di verde il pulsante del form
if st.session_state['success_flash']:
    st.markdown("""
        <style>
        [data-testid="stFormSubmitButton"] button {
            background-color: #4CAF50 !important;
            color: white !important;
            border-color: #4CAF50 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 1. CARICAMENTO DATI E CALCOLO PREVENTIVO DEI TRAGUARDI
# ----------------------------------------------------
df_abitudini = get_tutte_abitudini()
df_log = get_log_abitudini()

count_master = 0
count_ottimo = 0
count_strada = 0

# Calcoliamo i dati dei traguardi prima di mostrare la tabella in alto
daily_sum = pd.DataFrame()

if not df_abitudini.empty and not df_log.empty:
    totale_importanza_sistema = df_abitudini['importanza'].sum()
    if totale_importanza_sistema > 0:
        df_comp = df_log[df_log['completato'] == 1]
        if not df_comp.empty:
            daily_sum = df_comp.groupby('data')['importanza'].sum().reset_index()
            daily_sum.columns = ['data', 'importanza_completata']
            daily_sum['Percentuale (%)'] = (daily_sum['importanza_completata'] / totale_importanza_sistema) * 100

            # Conteggio cumulativo dei trofei ottenuti
            for _, row in daily_sum.iterrows():
                perc = row['Percentuale (%)']
                if perc > 85:
                    count_master += 1
                elif perc > 60:
                    count_ottimo += 1
                elif perc > 50:
                    count_strada += 1
# ----------------------------------------------------
# 2. TABELLA DEI TRAGUARDI GIORNALIERI (IN ALTO)
# ----------------------------------------------------
st.subheader("🏆 Tabella dei Traguardi Giornalieri")

totale_trofei = count_master + count_ottimo + count_strada

if totale_trofei > 0:
    dati_traguardi = [
        {
            "Livello": "⭐ Master (>85%)",
            "Sbloccati": count_master,
            "Collezione Trofei": "⭐ " * count_master if count_master > 0 else "—"
        },
        {
            "Livello": "🔥 Ottimo (>60%)",
            "Sbloccati": count_ottimo,
            "Collezione Trofei": "🔥 " * count_ottimo if count_ottimo > 0 else "—"
        },
        {
            "Livello": "💪 Sei sulla giusta strada (>50%)",
            "Sbloccati": count_strada,
            "Collezione Trofei": "💪 " * count_strada if count_strada > 0 else "—"
        }
    ]
    df_traguardi = pd.DataFrame(dati_traguardi)
    st.dataframe(df_traguardi, use_container_width=True, hide_index=True)
else:
    st.info("Nessun traguardo ancora sbloccato. Completa le tue abitudini per iniziare ad accumulare trofei!")

st.markdown("---")

# ----------------------------------------------------
# SIDEBAR: Aggiungi Nuova Abitudine
# ----------------------------------------------------
st.sidebar.header("➕ Nuova Abitudine")
with st.sidebar.form("form_nuova_abitudine"):
    nome_abitudine = st.text_input("Nome dell'abitudine (es. Bere 2L d'acqua)")
    descrizione_abitudine = st.text_area("Descrizione o obiettivo (facoltativo)")
    importanza_abitudine = st.slider("Grado di importanza (1-5)", min_value=1, max_value=5, value=3)
    abilita_scadenza = st.checkbox("Imposta una data di scadenza")
    scadenza_abitudine = st.date_input("Seleziona la data", min_value=date.today()) if abilita_scadenza else None
    
    submit_abitudine = st.form_submit_button(label="Salva Nuova Abitudine")
    
    if submit_abitudine:
        if not nome_abitudine.strip():
            st.error("Il nome dell'abitudine non può essere vuoto!")
        else:
            st.session_state['success_flash'] = True
            aggiungi_abitudine(nome_abitudine, descrizione_abitudine, importanza_abitudine, scadenza_abitudine)
            st.success(f"Abitudine '{nome_abitudine}' creata!")
            time.sleep(1)
            st.session_state['success_flash'] = False
            st.rerun()

# ----------------------------------------------------
# AREA PRINCIPALE: Check-in Giornaliero
# ----------------------------------------------------
st.subheader("📅 Check-in di Oggi")

if df_abitudini.empty:
    st.info("Non hai ancora creato nessuna abitudine. Usare la barra laterale a sinistra per iniziare!")
else:
    oggi_str = date.today().strftime("%Y-%m-%d")
    st.write(f"Data odierna: **{oggi_str}** - Spunta le abitudini che hai completato oggi:")

    log_oggi = df_log[df_log['data'] == oggi_str] if not df_log.empty else pd.DataFrame()
    
    for _, abitudine in df_abitudini.iterrows():
        ab_id = abitudine['id']
        ab_nome = abitudine['nome']
        descrizione = abitudine.get('descrizione', None)
        scadenza = abitudine.get('scadenza', None)
        
        # Countdown scadenza
        badge_scadenza = ""        
        if pd.notna(scadenza) and scadenza:
            scadenza_date = pd.to_datetime(scadenza).date()
            giorni_rimanenti = (scadenza_date - date.today()).days
            
            if giorni_rimanenti > 0:
                badge_scadenza = f" ⏳ **-{giorni_rimanenti} giorni**"
            elif giorni_rimanenti == 0:
                badge_scadenza = " ⏳ **Scade oggi!**"
            else:
                badge_scadenza = " ⚠️ **Scaduta**"
        
        # Verifichiamo se l'abitudine è già spuntata oggi
        gia_completata = False
        if not log_oggi.empty:
            match = log_oggi[(log_oggi['abitudine_id'] == ab_id) & (log_oggi['completato'] == 1)]
            if not match.empty:
                gia_completata = True
                
        label_testo = f"**{ab_nome}**"
        if pd.notna(descrizione) and str(descrizione).strip():
            label_testo += f" ({descrizione})"
        label_testo += badge_scadenza
        
        col_check, col_delete = st.columns([0.9, 0.1])
        
        with col_check:
            stato_attuale = st.checkbox(label_testo, value=gia_completata, key=f"ab_{ab_id}")
            
            if stato_attuale != gia_completata:
                valore_salvato = 1 if stato_attuale else 0
                registra_log(ab_id, oggi_str, valore_salvato)
                st.rerun()

        with col_delete:
            if st.button("🗑️", key=f"del_{ab_id}", help="Elimina questa abitudine"):
                elimina_abitudine(ab_id)
                st.rerun()

    # ----------------------------------------------------
    # SEZIONE STATISTICHE E GRAFICI
    # ----------------------------------------------------
    st.markdown("---")
    st.subheader("📊 Analisi e Storico Progressi")
    
    if not df_log.empty:
        periodo = st.radio("Seleziona il periodo da visualizzare:", ["Ultimi 7 giorni", "Ultimi 30 giorni", "Tutto lo storico"], horizontal=True)
        
        df_log['data_dt'] = pd.to_datetime(df_log['data']).dt.date
        oggi = date.today()
        
        if periodo == "Ultimi 7 giorni":
            limite = oggi - timedelta(days=7)
            df_filtrato = df_log[df_log['data_dt'] >= limite]
        elif periodo == "Ultimi 30 giorni":
            limite = oggi - timedelta(days=30)
            df_filtrato = df_log[df_log['data_dt'] >= limite]
        else:
            df_filtrato = df_log
            
        if df_filtrato.empty:
            st.warning("Nessun dato disponibile per il periodo selezionato.")
        else:
            totale_importanza_sistema = df_abitudini['importanza'].sum()
            
            if totale_importanza_sistema > 0:
                df_comp = df_filtrato[df_filtrato['completato'] == 1]
                
                if df_comp.empty:
                    st.warning("Nessuna abitudine completata nel periodo selezionato. Spunta qualche abitudine per vedere il grafico!")
                else:
                    daily_sum_filtered = df_comp.groupby('data')['importanza'].sum().reset_index()
                    daily_sum_filtered.columns = ['data', 'importanza_completata']
                    daily_sum_filtered['Percentuale (%)'] = (daily_sum_filtered['importanza_completata'] / totale_importanza_sistema) * 100
                    
                    st.markdown("### Trend percentuale giornaliero")
                    
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.bar(daily_sum_filtered['data'].astype(str), daily_sum_filtered['Percentuale (%)'], color='#4CAF50', width=0.6)
                    ax.set_xlabel("Giorni")
                    ax.set_ylabel("Percentuale (%)")
                    ax.set_ylim(0, 105)
                    plt.xticks(rotation=45)
                    ax.grid(axis='y', linestyle='--', alpha=0.7)
                    
                    st.pyplot(fig)
