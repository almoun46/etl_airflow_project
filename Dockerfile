# Image officielle python 3.13-slim
FROM python:3.13-slim

# Définition du répertoire de travail
WORKDIR /app

# Copie des fichiers nécessaires
COPY requirements.txt requirements.txt
COPY app/main.py main.py

# Installation des dépendances système
RUN apt-get update && apt-get install -y libpq-dev

# Installation des dépendances Python
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

