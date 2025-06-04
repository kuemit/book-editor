# Dockerfile
# Verwende das pandoc/latex Image als Basis
FROM pandoc/latex:latest-ubuntu

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Installiere Python und pip (falls nicht bereits im pandoc/latex Image enthalten)
# pandoc/latex basiert auf Debian, daher apt-get
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    # Optional: Installiere weitere Build-Tools, falls für Python-Pakete benötigt
    # build-essential \
    && rm -rf /var/lib/apt/lists/*

# Stelle sicher, dass 'python' auf 'python3' verweist, für pandoc-interne Skripte oder andere Tools.
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Kopiere die requirements.txt und installiere die Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere die Flask-Anwendung
COPY app.py .

# Kopiere den 'static' Ordner mit den Frontend-Dateien
# Der gesamte Inhalt des Host-static-Ordners wird in den Container-static-Ordner kopiert
COPY static/ static/

# Exponiere den Port, auf dem die Flask-Anwendung lauschen wird
EXPOSE 5000

# Starte die Anwendung mit Gunicorn
# "app:app" bedeutet, dass Gunicorn die Flask-Instanz namens "app" aus der Datei "app.py" laden soll
# Gunicorn wird auf allen verfügbaren Netzwerkschnittstellen (0.0.0.0) auf Port 5000 lauschen.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
