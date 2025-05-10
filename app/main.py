# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import psycopg2


# Configuration de la base de données
DB_CONNECTION = {
    "dbname": "airflow",
    "user": "airflow",
    "password": "airflow",
    "host": "postgres_airflow",  # Nom du conteneur Docker
    "port": 5432,
}

# Fonction pour vérifier la connexion à la base de données
@st.cache_data
def test_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONNECTION)
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données : {e}")
        return False

# Fonction pour récupérer les données
@st.cache_data
def get_weather_data():
    try:
        conn = psycopg2.connect(**DB_CONNECTION)
        cur = conn.cursor()
        cur.execute("SELECT * FROM weather ORDER BY date DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        df = pd.DataFrame(rows, columns=["date", "min_temperature", "max_temperature", "precipitation", "weather_code"])
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date")
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()


# Interface utilisateur
st.set_page_config(page_title="Données météo", layout="wide")
st.title("📊 Données Météo")
st.markdown("Ce dashboard présente les données collectées automatiquement via Airflow depuis une API météo.")

if test_db_connection():
    df = get_weather_data()

    if not df.empty:
        st.subheader("📋 Données brutes")
        st.dataframe(df)

        st.subheader("📈 Visualisation des températures et précipitations")
        st.line_chart(df.set_index("date")[["min_temperature", "max_temperature", "precipitation"]])
    else:
        st.warning("Aucune donnée disponible.")
else:
    st.error("Impossible de se connecter à la base de données. Veuillez vérifier la configuration.")
