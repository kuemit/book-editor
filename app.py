# app.py
import os
import subprocess
import base64
import tempfile
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Initialisiere die Flask-Anwendung.
# 'static_folder' legt fest, wo Flask nach statischen Dateien (Frontend) suchen soll.
# 'static_url_path' stellt sicher, dass statische Dateien direkt von der Root-URL ausgeliefert werden.
app = Flask(__name__, static_folder='static', static_url_path='')

# CORS ist hier hauptsächlich für die Entwicklung, wenn Frontend und Backend
# potenziell auf verschiedenen Ursprüngen laufen würden.
# Da das Backend jetzt das Frontend hostet, ist es technisch nicht mehr streng notwendig,
# aber es schadet nicht, es für Flexibilität beizubehalten.
CORS(app)

@app.route('/')
def serve_index():
    """Dient die index.html-Datei für die Root-URL."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Dient andere statische Dateien (CSS, JS, Bilder usw.) aus dem statischen Ordner."""
    # Verhindert, dass Pfade wie '..' verwendet werden, um auf Dateien außerhalb des static_folder zuzugreifen
    if ".." in path:
        return "Forbidden", 403
    return send_from_directory(app.static_folder, path)

@app.route('/convert', methods=['POST'])
def convert_markdown_to_pdf():
    """
    Konvertiert Markdown-Text in ein PDF-Buchformat mithilfe von Pandoc.
    Pandoc wird direkt im Container aufgerufen, da es sich im selben Image befindet.
    """
    data = request.json
    markdown_text = data.get('markdown_text')

    if not markdown_text:
        return jsonify({"error": "Kein Markdown-Text bereitgestellt"}), 400

    # Erstelle temporäre Dateien für Markdown-Eingabe und PDF-Ausgabe.
    # tempfile.NamedTemporaryFile erstellt eine Datei, die automatisch gelöscht wird,
    # wenn sie geschlossen wird oder das Programm beendet wird.
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.md', encoding='utf-8') as md_file:
        md_file.write(markdown_text)
        md_file_path = md_file.name

    pdf_output_path = md_file_path.replace('.md', '.pdf')

    try:
        # Führe den Pandoc-Befehl direkt aus.
        # Pandoc ist im PATH des pandoc/latex-Basis-Images verfügbar.
        pandoc_command = [
            'pandoc',
            md_file_path,  # Eingabedatei im Container
            '-o', pdf_output_path,  # Ausgabedatei im Container
            '--template=book',  # Verwendet das Standard-LaTeX-Buch-Template von Pandoc
            '--pdf-engine=xelatex',  # PDF-Engine für bessere Font- und Unicode-Unterstützung
            '-M', 'title=Mein Buch',  # Beispiel-Metadaten für Pandoc (können angepasst werden)
            '-M', 'author=Ein begeisterter Autor'
        ]

        # Führe den Pandoc-Befehl aus und fange die Ausgabe ab.
        result = subprocess.run(pandoc_command, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            app.logger.error(f"Pandoc Fehler: {result.stderr}")
            return jsonify({"error": "Fehler bei der Konvertierung des Buches", "details": result.stderr}), 500

        # Lese die generierte PDF-Datei im Binärmodus.
        with open(pdf_output_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()

        # Kodieren Sie die PDF-Daten in Base64, um sie über JSON an das Frontend zu senden.
        encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')

        return jsonify({"pdf_data": encoded_pdf}), 200

    except FileNotFoundError:
        # Dieser Fehler sollte nicht auftreten, wenn Pandoc korrekt im Image installiert ist.
        return jsonify({"error": "Pandoc-Befehl nicht gefunden. Ist Pandoc im Image korrekt installiert?"}), 500
    except Exception as e:
        # Fängt alle anderen unerwarteten Fehler ab.
        app.logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        return jsonify({"error": f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"}), 500
    finally:
        # Bereinige temporäre Dateien, unabhängig davon, ob ein Fehler aufgetreten ist.
        if os.path.exists(md_file_path):
            os.remove(md_file_path)
        if os.path.exists(pdf_output_path):
            os.remove(pdf_output_path)

if __name__ == '__main__':
    # Starten Sie die Flask-Anwendung.
    # 'host='0.0.0.0'' macht die Anwendung von außen im Container zugänglich.
    # 'debug=True' ist gut für die Entwicklung, sollte aber in der Produktion deaktiviert werden.
    app.run(debug=True, host='0.0.0.0', port=5000)
