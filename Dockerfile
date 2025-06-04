# Dockerfile
# Verwende das pandoc/latex Image als Basis
FROM pandoc/latex:latest-ubuntu

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Installiere Python, pip und Flask über apt-get
# pandoc/latex basiert auf Debian, daher apt-get
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-flask \
    # Optional: Fügen Sie hier build-essentials hinzu, falls Flask oder andere apt-Pakete sie benötigen
    # build-essential \
    # libffi-dev \
    # libssl-dev \
    # python3-dev \
    # gcc \
    # g++ \
    # make \
    # pkg-config \
    # cmake \
    && rm -rf /var/lib/apt/lists/*

# Stelle sicher, dass 'python' auf 'python3' verweist, für pandoc-interne Skripte oder andere Tools.
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Kopiere die requirements.txt und installiere die Python-Abhängigkeiten (jetzt nur gunicorn)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere die Flask-Anwendung
COPY app.py .

# Kopiere den 'static' Ordner mit den Frontend-Dateien
# Der gesamte Inhalt des Host-static-Ordners wird in den Container-static-Ordner kopiert
COPY static/ static/

# Exponiere den Port, auf dem die Flask-Anwendung lauschen wird
EXPOSE 5000

# Setze den ENTRYPOINT auf Gunicorn, damit es als Hauptprozess gestartet wird
ENTRYPOINT ["gunicorn"]

# Übergebe die Argumente an Gunicorn
CMD ["--bind", "0.0.0.0:5000", "app:app"]
