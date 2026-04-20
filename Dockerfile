# Utiliser l'image Python officielle
FROM python:3.12-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=project.settings

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier des dépendances
COPY requirements.txt .

# Installer les dépendances Python (SANS PyTorch séparé)
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copier tout le projet
COPY . .

# Exposer le port
EXPOSE 8000

# Commande pour démarrer le serveur
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]