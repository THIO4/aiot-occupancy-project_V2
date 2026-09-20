import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime
import time
import os

# Tuodaan funktiot omasta mallitiedostosta
from train_model import load_data, get_24h_profile, get_weekly_heatmap_data

# dashboardin asetukset
st.set_page_config(page_title="AIoT & ROBO LAB - Tilannehuone", layout="wide")

# Päivitysväli sekunteina
REFRESH_RATE = 30 

st.title("AIoT & ROBO Laboratorion kävijämäärän seuranta")

try:
    # 1. Ladataan data
    df = load_data()

    if not df.empty:
        # 2. Valmistellaan analyysi
        profile_df = get_24h_profile(df)
        nyky_hetki = datetime.datetime.now()
        nyky_tunti = nyky_hetki.hour
        
        # Suodatetaan tämän päivän data
        df['date'] = df['timestamp'].dt.date
        tanaan_df = df[df['date'] == nyky_hetki.date()].copy()
        tanaan_df = tanaan_df.sort_values('timestamp')

        # Päivän kokonaiskävijät
        # Lasketaan vain positiiviset muutokset peräkkäisten rivien välillä
        saapumiset_tanaan = tanaan_df['occupancy'].diff().fillna(tanaan_df['occupancy'].iloc[0] if not tanaan_df.empty else 0)
        kokonaiskayvijat_tanaan = int(saapumiset_tanaan.clip(lower=0).sum())

        # Ylärivin mittarit
        m1, m2, m3 = st.columns(3)
        
        # Kävijöitä tänään yhteensä (kumulatiivinen luku)
        m1.metric("Kävijöitä tänään yhteensä", f"{kokonaiskayvijat_tanaan} hlöä")
        
        # Ennuste seuraavalle tunnille (kokonaisulukuna)
        seuraava_tunti_idx = (nyky_tunti + 1) % 24
        ennuste_seuraava = int(profile_df.loc[profile_df['hour'] == seuraava_tunti_idx, 'predicted_occupancy'].values[0])
        m2.metric("Ennuste seuraavalle tunnille", f"{ennuste_seuraava} hlöä")
        
        # Päivän ennustettu volyymi (Koko 24h ennusteiden summa)
        paivan_kokonaisennuste = int(profile_df['predicted_occupancy'].sum())
        m3.metric("Päivän ennustettu volyymi", f"{paivan_kokonaisennuste} henkilöä")

        # Keskirivi 24H vertailugraafi
        st.subheader(f"Päivittäinen seuranta (24h) - {nyky_hetki.strftime('%d.%m.%Y')}")
        
        tanaan_df['hour'] = tanaan_df['timestamp'].dt.hour
        
        tanaan_tunnit = tanaan_df.groupby('hour')['occupancy'].max().astype(int).reset_index()

        fig = go.Figure()

        # Ennustekäyrä 
        fig.add_trace(go.Scatter(
            x=profile_df['hour'], 
            y=profile_df['predicted_occupancy'],
            mode='lines',
            name='Ennustettu trendi',
            line=dict(color='rgba(255, 255, 255, 0.3)', dash='dash')
        ))

        # Tämän päivän toteuma 
        fig.add_trace(go.Scatter(
            x=tanaan_tunnit['hour'], 
            y=tanaan_tunnit['occupancy'],
            mode='lines+markers',
            name='Tämän päivän toteuma',
            line=dict(color='#00FFCC', width=4)
        ))

        fig.update_layout(
            xaxis_title="Kellonaika",
            yaxis_title="Kävijämäärä",
            xaxis=dict(tickmode='linear', range=[0, 23]),
            template="plotly_dark",
            hovermode="x", 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Lämpökartta, viikkotason historia
        st.markdown("---")
        st.subheader("Viikoittainen käyttöaste (Lämpökartta)")
        
        heatmap_df = get_weekly_heatmap_data(df)

        if not heatmap_df.empty:
            pivot_df = heatmap_df.pivot(index='day_name', columns='hour', values='predicted_occupancy')
            # Järjestetään päivät
            jarjestys = ['Ma', 'Ti', 'Ke', 'To', 'Pe', 'La', 'Su']
            pivot_df = pivot_df.reindex(jarjestys)

            fig_heat = px.imshow(
                pivot_df,
                labels=dict(x="Kellonaika", y="Viikonpäivä", color="Kävijämäärä"),
                x=pivot_df.columns,
                y=pivot_df.index,
                color_continuous_scale='Viridis',
                aspect="auto"
            )

            fig_heat.update_layout(
                xaxis=dict(tickmode='linear', dtick=1),
                template="plotly_dark"
            )

            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Lämpökarttaa varten tarvitaan dataa useammalta päivältä.")
            
# INFO 
        st.markdown("---")
        st.header("Ohjeet ja mallin toiminta")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.subheader("Miten seuranta toimii?")
            st.write("""
            * **Kävijöitä tänään:** Tämä luku laskee kaikki päivän aikana saapuneet henkilöt. Se tunnistaa nousut kävijämäärässä ja laskee ne yhteen (kumulatiivinen saapuminen).
            * **Tämän päivän toteuma:** Turkoosi viiva näyttää kunkin tunnin korkeimman havaitun kävijämäärän. Käytämme maksimiarvoa, jotta lyhyetkin vierailut näkyvät graafissa.
            * **Lämpökartta:** Seuraa labran käyttöastetta pitemmällä aikavälillä. Mitä kirkkaampi väri, sitä ruuhkaisempi ajankohta on historiallisesti ollut.
            """)

        with col_info2:
            st.subheader("Miten ennustetta tulkitaan?")
            st.write("""
            * **Ennustettu trendi:** Harmaa katkoviiva edustaa labran 'normaalia' päivää. Se on laskettu kaiken kertyneen historiastatistiikan keskiarvona.
            * **Ennuste vs. Toteuma:** Jos turkoosi viiva on katkoviivan yläpuolella, labrassa on tavallista enemmän ruuhkaa. 
            * **Päivän ennustettu volyymi:** Ennuste siitä, kuinka monta henkilöä päivän aikana yhteensä kertyy. Se auttaa arvioimaan päivän kokonaiskuormitusta.
            """)
            
        st.info("💡 **Vinkki:** Voit zoomata graafeja hiirellä ja nähdä tarkat arvot viemällä kursorin käyrän päälle.")
        

        
        time.sleep(REFRESH_RATE)
        st.rerun()

        # Automaattinen päivitys
        time.sleep(REFRESH_RATE)
        st.rerun()

    else:
        st.warning("Odotetaan dataa tietokantaan...")
        time.sleep(5)
        st.rerun()

except Exception as e:
    st.error(f"Virhe: {e}")