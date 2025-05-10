import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python_operator import PythonOperator
import requests
import psycopg2
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)

# Confifuration
API_URL = "https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&daily=temperature_2m_min,temperature_2m_max,weather_code,precipitation_sum&timezone=Europe/Paris"
DB_CONNECTION = {
    "dbname": "airflow",
    "user": "airflow",
    "password": "airflow",
    "host": "postgres",
    "port": 5432,
}

# Fonction pour extraire les données
def extract_data():
    response = requests.get(API_URL)
    data = response.json()
    logging.info(f"Données extraites : {data['daily']}")
    return data["daily"]

# Fonction pour transformer les données
def transform_data(ti):
    raw_data = ti.xcom_pull(task_ids="extract_task")
    logging.info(f"Données brutes : {raw_data}")
    transformed_data = [
        (raw_data["time"][i], raw_data["temperature_2m_min"][i],
         raw_data["temperature_2m_max"][i], raw_data["precipitation_sum"][i],
         raw_data["weather_code"][i])
        for i in range(len(raw_data["time"]))
    ]
    logging.info(f"Données transformées : {transformed_data}")
    return transformed_data

# Fonction pour charger les données dans la base de données
def load_data(ti):
    transformed_data = ti.xcom_pull(task_ids="transform_task")
    logging.info(f"Données à charger : {transformed_data}")
    connection = psycopg2.connect(**DB_CONNECTION)
    cursor = connection.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS weather (
        date DATE PRIMARY KEY,
        min_temperature FLOAT,
        max_temperature FLOAT,
        precipitation FLOAT,
        weather_code INT
        )"""
    )
    insert_query = "INSERT INTO weather (date, min_temperature, max_temperature, precipitation, weather_code) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (date) DO NOTHING"
    cursor.executemany(insert_query, transformed_data)
    connection.commit()
    cursor.close()
    connection.close()


# Définition du DAG
# Paramètres par défaut pour les tâches du DAG
default_args = {
    # propriétaire du DAG
    "owner": "airflow",
    # le DAG dépend-il de la réussite de la tâche précédente ?
    "depends_on_past": False,
    # date de début de l'exécution du DAG
    "start_date": datetime.datetime(2025, 1, 18),
    # nombre de fois que le DAG doit être relancé en cas d'échec
    "retries": 3,
    # délai avant de relancer le DAG en cas d'échec
    "retry_delay": datetime.timedelta(minutes=1),
}

with DAG(
    dag_id="etl_pipeline",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
) as dag:
    extract_task = PythonOperator(
        task_id="extract_task",
        python_callable=extract_data,
    )
    transform_task = PythonOperator(
        task_id="transform_task",
        python_callable=transform_data,
    )
    load_task = PythonOperator(
        task_id="load_task",
        python_callable=load_data,
    )
    extract_task >> transform_task >> load_task  # spécification du workflow
