import subprocess
import json
import sys
import os

# --- Konfiguration ---
ZEN_SERVER_URL = "http://localhost:8000/v1/chat/completions"
TARGET_MODEL = "claude-code"

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
system_prompt_path = os.path.join(script_dir, "system_prompt.txt")

# --- 1. Lade System-Prompt ---
try:
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    print("✅ System-Prompt erfolgreich geladen.")
except FileNotFoundError:
    print("❌ FEHLER: 'system_prompt.txt' nicht gefunden.")
    sys.exit(1)

# --- 2. Definiere Benutzeranfrage ---
user_question = """
Okay, Claude, hier ist eine neue, komplexe Aufgabe für dich. Ticket-Nummer ist DS-4600.

Das Hauptproblem ist die Performance unseres `ReportGenerator`-Moduls. Es ist extrem langsam, weil es für jeden Report hunderte Datenbankabfragen macht. Gleichzeitig müssen wir für die Tests eine neue Version der Datenbank im CI/CD-Prozess bereitstellen.

Ich bin mir unsicher, ob wir das Modul nur refaktorisieren oder es komplett neu schreiben sollten, vielleicht mit einem asynchronen Ansatz, da es ein sehr altes Modul ist. Bitte analysiere das tiefgreifend und schlage einen Plan vor.

Und wo wir schon dabei sind, könntest du dem Report auch gleich ein neues Export-Format für 'Excel mit Makros' hinzufügen? Die Marketing-Abteilung hat danach gefragt.

Zusätzlich erstelle bitte eine kurze Zusammenfassung des neuen, schnelleren Report-Features für unsere Social-Media-Kanäle.

Wenn du den Plan hast, beginne bitte mit der Umsetzung.
"""

print(f"\n▶️ Sende Anfrage an Modell '{TARGET_MODEL}'...")
print("Dies kann einen Moment dauern, da die Aufgabe sehr komplex ist...")

# --- 3. Baue die Anfrage zusammen ---
payload = {
    "model": TARGET_MODEL,
    "system": system_prompt,
    "messages": [
        {
            "role": "user",
            "content": user_question
        }
    ],
    "stream": False
}

# Konvertiere das Payload-Dictionary in einen JSON-String
payload_json = json.dumps(payload)

# --- 4. Sende die Anfrage mit PowerShell's Invoke-WebRequest ---
# Wir verwenden diesen Workaround, da 'requests' Probleme zu haben scheint.
# Dieser Befehl ist robuster in dieser Umgebung.
command = [
    "powershell",
    "-Command",
    f"Invoke-WebRequest -Uri '{ZEN_SERVER_URL}' -Method 'POST' -ContentType 'application/json' -Body '{payload_json}' -UseBasicParsing | Select-Object -ExpandProperty Content"
]

try:
    # Führe den PowerShell-Befehl aus
    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=True, # Löst eine Ausnahme aus, wenn der Befehl fehlschlägt
        timeout=300
    )

    # Die Antwort ist der stdout des Prozesses
    response_text = process.stdout
    response_data = json.loads(response_text)

    # Extrahiere die eigentliche Text-Antwort
    model_reply = response_data['choices'][0]['message']['content']

    print("\n💡 Antwort von Claude erhalten:\n---")
    print(model_reply)
    print("---\n✅ Anfrage erfolgreich abgeschlossen.")

except subprocess.TimeoutExpired:
    print("❌ FEHLER: Die Anfrage hat zu lange gedauert (Timeout).")
except subprocess.CalledProcessError as e:
    print(f"❌ FEHLER bei der Ausführung des Web-Requests: {e}")
    print(f"    Stderr: {e.stderr}")
except (KeyError, IndexError, json.JSONDecodeError) as e:
    print(f"❌ FEHLER: Die Antwort vom Modell hatte ein unerwartetes Format. Antwort: {response_text}")