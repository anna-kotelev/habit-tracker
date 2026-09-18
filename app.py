import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
from backend import (
    aggiungi_abitudine, 
    get_tutte_abitudini, 
    registra_log, 
    get_log_abitudini
)

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Habit Tracker Personale", page_icon="🎯", layout="wide")

st.title("🎯 Il mio Habit Tracker")
st.markdown("Monitora le tue abitudini con percentuali ponderate e traguardi giornalieri.")

# ----------------------------------------------------
# SIDEBAR: Aggiungi Nuova Abitudine
# ----------------------------------------------------
st.sidebar.header("➕ Nuova Abitudine")
with st.sidebar.form("form_nuova_abitudine"):
        nome_abitudine = st.text_input("Nome dell'abitudine (es. Bere 2L d'acqua)")
        descrizione_abitudine = st.text_area("Descrizione o obiettivo (facoltativo)")
        importanza_abitudine = st.slider("Grado di importanza (1-5)", min_value=1, max_value=5, value=3)
        submit_abitudine = st.form_submit_button(label="Salva Nuova Abitudine")
        
        if submit_abitudine:
            if not nome_abitudine.strip():
                st.error("Il nome dell'abitudine non può essere vuoto!")
            else:
                # [MODIFICA 1] Passiamo l'importanza alla funzione del backend
                aggiungi_abitudine(nome_abitudine, descrizione_abitudine, importanza_abitudine)
                st.success(f"Abitudine '{nome_abitudine}' creata!")
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
        
        # Verifichiamo se l'abitudine è già spuntata oggi
        gia_completata = False
        if not log_oggi.empty:
            match = log_oggi[(log_oggi['abitudine_id'] == ab_id) & (log_oggi['completato'] == 1)]
            if not match.empty:
                gia_completata = True
                
        # Mostriamo il checkbox interattivo
        stato_attuale = st.checkbox(f"**{ab_nome}** ({abitudine['descrizione']})" if abitudine['descrizione'] else f"**{ab_nome}**", value=gia_completata, key=f"ab_{ab_id}")
        
        # Se lo stato cambia, aggiorniamo il database in tempo reale
        valore_salvato = 1 if stato_attuale else 0
        registra_log(ab_id, oggi_str, valore_salvato)

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