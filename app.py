import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
from backend import (
    aggiungi_abitudine, 
    get_tutte_abitudini, 
    registra_log, 
    get_log_abitudini,
    elimina_abitudine
)
import time

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Habit Tracker Personale", page_icon="🎯", layout="wide")

st.title("🎯 Il mio Habit Tracker")
st.markdown("Monitora le tue abitudini con percentuali ponderate e traguardi giornalieri.")

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
st.subheader("🏆 Tabella dei Traguardi Giornalieri")
                
traguardi_dict = {}
for _, row in daily_sum.iterrows():
    d = row['data']
    perc = row['Percentuale (%)']
    
    master_emoji = ""
    ottimo_emoji = ""
    strada_emoji = ""

    if perc > 85:
        master_emoji = "⭐"
    elif perc > 60:
        ottimo_emoji = "🔥"
    elif perc > 50:
        strada_emoji = "💪​"

    traguardi_dict[d] = {
        "Master": master_emoji,
        "Ottimo": ottimo_emoji,
        "Sei sulla giusta strada": strada_emoji
    }

if traguardi_dict:
    df_traguardi = pd.DataFrame(traguardi_dict)
    st.dataframe(df_traguardi, use_container_width=True)
else:
    st.warning("Nessun traguardo registrato nel periodo.")

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
                # Passiamo l'importanza alla funzione del backend
                aggiungi_abitudine(nome_abitudine, descrizione_abitudine, importanza_abitudine, scadenza_abitudine)
                st.success(f"Abitudine '{nome_abitudine}' creata!")
                
                # 3. Mettiamo in pausa per 1 secondo esatto per mostrare il colore
                time.sleep(1)
            
                # 4. Spegniamo lo stato e ricarichiamo la pagina
                st.session_state['success_flash'] = False
                st.rerun()


# ----------------------------------------------------
# AREA PRINCIPALE: Check-in Giornaliero
# ----------------------------------------------------
df_abitudini = get_tutte_abitudini()

st.subheader("📅 Check-in di Oggi")

if df_abitudini.empty:
    st.info("Non hai ancora creato nessuna abitudine. Usare la barra laterale a sinistra per iniziare!")
else:
    oggi_str = date.today().strftime("%Y-%m-%d")
    st.write(f"Data odierna: **{oggi_str}** - Spunta le abitudini che hai completato oggi:")

    # Recuperiamo i log esistenti per la data odierna
    df_log = get_log_abitudini()
    log_oggi = df_log[df_log['data'] == oggi_str] if not df_log.empty else pd.DataFrame()
    
    # Creiamo un form o dei checkbox interattivi per ogni abitudine
    for _, abitudine in df_abitudini.iterrows():
        ab_id = abitudine['id']
        ab_nome = abitudine['nome']
        descrizione = abitudine.get('descrizione', None)
        scadenza = abitudine.get('scadenza', None)
       
        # 1. Calcolo del countdown
        badge_scadenza = ""        
        if pd.notna(scadenza) and scadenza:
            # Assicuriamoci che la data sia in formato corretto
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
                
        # Formattazione dell'etichetta del checkbox
        label_testo = f"**{ab_nome}**"
        if pd.notna(descrizione) and str(descrizione).strip():
            label_testo += f" ({descrizione})"
        label_testo += badge_scadenza
        
        # Layout a colonne per separare Checkbox e Tasto Elimina
        col_check, col_delete = st.columns([0.9, 0.1])
        
        with col_check:
            stato_attuale = st.checkbox(label_testo, value=gia_completata, key=f"ab_{ab_id}")
            
            # Ottimizzazione: registra nel DB solo se c'è un cambiamento reale per evitare scritture inutili al refresh
            if stato_attuale != gia_completata:
                valore_salvato = 1 if stato_attuale else 0
                registra_log(ab_id, oggi_str, valore_salvato)
                st.rerun() # Forza un refresh per aggiornare statistiche in tempo reale

        with col_delete:
            # Pulsante per eliminare (usiamo un pop-up nativo se necessario, qui un tasto diretto)
            if st.button("🗑️", key=f"del_{ab_id}", help="Elimina questa abitudine"):
                elimina_abitudine(ab_id)
                st.rerun()

    # ----------------------------------------------------
    # SEZIONE STATISTICHE E GRAFICI
    # ----------------------------------------------------
    st.markdown("---")
    st.subheader("📊 Analisi e Storico Progressi")
    
    if not df_log.empty:
        # Filtro temporale richiesto
        periodo = st.radio("Seleziona il periodo da visualizzare:", ["Ultimi 7 giorni", "Ultimi 30 giorni", "Tutto lo storico"], horizontal=True)
        
        # Convertiamo la colonna data in formato datetime per filtrare correttamente
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
                
                # [CORREZIONE] Controlliamo se ci sono abitudini completate nel periodo
                if df_comp.empty:
                    st.warning("Nessuna abitudine completata nel periodo selezionato. Spunta qualche abitudine per vedere il grafico!")
                else:
                    daily_sum = df_comp.groupby('data')['importanza'].sum().reset_index()
                    daily_sum.columns = ['data', 'importanza_completata']
                    
                    daily_sum['Percentuale (%)'] = (daily_sum['importanza_completata'] / totale_importanza_sistema) * 100
                    
                    # Grafico a barre statico con Matplotlib
                    st.markdown("### Trend percentuale giornaliero")
                    
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.bar(daily_sum['data'].astype(str), daily_sum['Percentuale (%)'], color='#4CAF50', width=0.6)
                    ax.set_xlabel("Giorni")
                    ax.set_ylabel("Percentuale (%)")
                    ax.set_ylim(0, 105)
                    plt.xticks(rotation=45)
                    ax.grid(axis='y', linestyle='--', alpha=0.7)
                    
                    st.pyplot(fig)
                    
                    # Tabella dei Traguardi (Gamification)
                    st.markdown("---")

                    
