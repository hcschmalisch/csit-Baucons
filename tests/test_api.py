"""
Test-Skript für den API-Server mit Authentifizierung

Unterstützt drei Test-Modi:
1. "sync" - Synchroner Aufruf (mit 0-N Dateien)
2. "text_only" - Nur Text, keine Datei (synchron)
3. "async" - Asynchroner Aufruf (für lange Analysen / Power Automate)
"""
import requests
import base64
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Retry-Strategie für ngrok SSL-Probleme
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# ============================================
# KONFIGURATION - HIER ANPASSEN
# ============================================

# API-Key (aus customer_config.json)
## API_KEY = "Fameline-key-tAemhC35OgAJa-0IiOMo7w"  # Fameline
API_KEY = "Brandconsulting-key-CVvJ9bLuo0hLxV5LT-yzCQ"
# Aktion (muss für diesen Kunden erlaubt sein)
# ACTION = "analyze-quotation"
# ACTION = "analyze-rfqs"
# ACTION = "analyze-document"
ACTION = "get-bvv-rechnungsempfaenger"

# Test-Modus auswählen:
# "sync" = Synchroner Aufruf (mit Dateien aus FILES-Array)
# "text_only" = Nur Text, keine Datei (synchron)
# "async" = Asynchroner Aufruf (für Power Automate / lange Analysen)
TEST_MODE = "sync"  # Ändern Sie dies für verschiedene Tests

# Dateien zum Senden (0-N Dateien möglich):
# - Leer: [] = nur Text senden (dann USER_TEXT verwenden)
# - Eine Datei: ["datei.pdf"]
# - Mehrere Dateien: ["datei1.pdf", "datei2.docx", "datei3.xlsx"]
FILES = [
    "testdocs\\bvv_Uremovic.pdf"
]

# Optional: Zusätzlicher Text für den Agenten (kann plain-text oder HTML sein)
USER_TEXT = "Wer ist der Rechnungsempfaenger fuer diesen BVV?"
# USER_TEXT = "<h1>Analyse-Anfrage</h1><p>Bitte analysiere das Dokument und extrahiere alle Mengen.</p>"  # HTML-Beispiel
# USER_TEXT = "Erkläre mir den Pythagoras-Satz."  # Für text_only Modus

# Optional: Vector Store IDs (Wissensbasis)
# - Leer: [] = keine Wissensbasis
# - Eine ID: ["vs_..."]
# - Mehrere IDs: ["vs_...", "vs_..."]
VECTOR_STORE_IDS = []  # Leer für analyze-quotation (oder Vector Store ID eintragen)
# VECTOR_STORE_IDS = ["Index_silly_carnival_lpgs1qbv8"]  # Für analyze-rfqs

# API-URL (ändern Sie dies für localhost oder ngrok)
# API_URL = "http://localhost:5000/analyze"  # Für lokalen Test
# API_URL = "https://your-ngrok-url.ngrok-free.app/analyze"  # Für ngrok
# API_BASE_URL = "https://officemate.azurewebsites.net"  # Azure
API_BASE_URL = "http://localhost:5000"  # Für lokalen Test

# Abgeleitete URLs
API_URL = f"{API_BASE_URL}/analyze"
API_URL_ASYNC = f"{API_BASE_URL}/analyze-async"
API_URL_STATUS = f"{API_BASE_URL}/status"

# Timeout in Sekunden (Standard: 600 = 10 Minuten)
# Erhöhen Sie dies, wenn die Analyse sehr lange dauert (z.B. große Dateien oder komplexe Analysen)
REQUEST_TIMEOUT = 600  # 10 Minuten
# REQUEST_TIMEOUT = 900  # 15 Minuten für sehr große Dateien

# Polling-Intervall für async-Modus (in Sekunden)
ASYNC_POLL_INTERVAL = 5  # Sekunden zwischen Status-Abfragen
ASYNC_MAX_WAIT = 600  # Maximale Wartezeit (10 Minuten)

# ============================================


def test_async():
    """Testet den asynchronen API-Aufruf"""
    print(f"\n{'='*60}")
    print(f"ASYNCHRONER API-Test")
    print(f"{'='*60}")
    print(f"API-Key: {API_KEY}")
    print(f"Aktion: {ACTION}")
    print(f"Dateien: {FILES if FILES else '(keine)'}")
    print(f"URL (async): {API_URL_ASYNC}")
    print(f"URL (status): {API_URL_STATUS}")
    print(f"Polling-Intervall: {ASYNC_POLL_INTERVAL} Sekunden")
    print(f"{'='*60}\n")
    
    # Basis-Payload
    payload = {
        "api_key": API_KEY,
        "action": ACTION
    }

    # Optional: Vector Store IDs
    if VECTOR_STORE_IDS:
        payload["vector_store_ids"] = VECTOR_STORE_IDS
    
    # Dateien einlesen (0-N Dateien)
    if FILES:
        print(f"Lese {len(FILES)} Datei(en) ein...")
        files_array = []
        for test_file in FILES:
            print(f"  - {test_file}")
            with open(test_file, "rb") as f:
                file_content = f.read()
                file_content_base64 = base64.b64encode(file_content).decode('utf-8')
                files_array.append({
                    "file_content": file_content_base64,
                    "file_name": test_file
                })
            print(f"    {len(file_content)} Bytes")
        payload["files"] = files_array
    else:
        print("Keine Dateien, nur Text-Modus")
    
    # Optional: user_text
    if USER_TEXT:
        payload["user_text"] = USER_TEXT
    
    # Schritt 1: Async-Request starten
    print(f"\n[1/3] Starte asynchrone Analyse...")
    start_time = time.time()
    
    try:
        response = session.post(
            API_URL_ASYNC,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30  # Kurzer Timeout für den Start
        )
        
        if response.status_code != 202:
            print(f"❌ Fehler beim Starten: Status {response.status_code}")
            print(response.text)
            return
        
        result = response.json()
        task_id = result.get("task_id")
        status_url = result.get("status_url")
        
        print(f"✓ Task gestartet!")
        print(f"  Task-ID: {task_id}")
        print(f"  Status-URL: {status_url}")
        
    except Exception as e:
        print(f"❌ Fehler beim Starten: {e}")
        return
    
    # Schritt 2: Status abfragen (Polling)
    print(f"\n[2/3] Warte auf Ergebnis (Polling alle {ASYNC_POLL_INTERVAL}s)...")
    
    poll_count = 0
    max_polls = ASYNC_MAX_WAIT // ASYNC_POLL_INTERVAL
    last_status = None
    
    while poll_count < max_polls:
        poll_count += 1
        elapsed = time.time() - start_time
        
        try:
            status_response = session.get(
                f"{API_URL_STATUS}/{task_id}",
                timeout=10
            )
            
            if status_response.status_code == 404:
                print(f"❌ Task nicht gefunden!")
                return
            
            status_data = status_response.json()
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            
            # Nur ausgeben wenn sich Status ändert oder alle 5 Polls
            if status != last_status or poll_count % 5 == 0:
                print(f"  [{elapsed:5.1f}s] Status: {status} ({progress}%)")
                last_status = status
            
            if status == "completed":
                print(f"\n[3/3] ✓ Analyse abgeschlossen!")
                total_time = time.time() - start_time
                print(f"  Gesamtdauer: {total_time:.1f} Sekunden")
                
                # Ergebnis anzeigen
                result = status_data.get("result", {})
                print(f"\n{'='*60}")
                print("ERGEBNIS:")
                print(f"{'='*60}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # Zusammenfassung
                if result.get("success"):
                    response_data = result.get("response", {})
                    items_count = response_data.get("ItemsCount", 0)
                    print(f"\n✓ Erfolgreich! {items_count} Items gefunden.")
                return
            
            elif status == "failed":
                print(f"\n❌ Analyse fehlgeschlagen!")
                error = status_data.get("error", "Unbekannter Fehler")
                print(f"  Fehler: {error}")
                return
            
            # Warten vor nächstem Poll
            time.sleep(ASYNC_POLL_INTERVAL)
            
        except Exception as e:
            print(f"  ⚠ Polling-Fehler: {e}")
            time.sleep(ASYNC_POLL_INTERVAL)
    
    print(f"\n❌ Timeout: Maximale Wartezeit ({ASYNC_MAX_WAIT}s) erreicht")
    print(f"  Der Task läuft möglicherweise noch. Task-ID: {task_id}")


def test_sync():
    """Testet den synchronen API-Aufruf"""
    # Basis-Payload
    payload = {
        "api_key": API_KEY,
        "action": ACTION
    }

    # Optional: Vector Store IDs
    if VECTOR_STORE_IDS:
        payload["vector_store_ids"] = VECTOR_STORE_IDS

    # Füge user_text hinzu, falls vorhanden
    if USER_TEXT:
        payload["user_text"] = USER_TEXT

    # Test-Modus verarbeiten
    if TEST_MODE == "sync":
        # Dateien aus FILES-Array einlesen (0-N Dateien)
        if FILES:
            print(f"Modus: {len(FILES)} Datei(en)")
            print(f"Lese {len(FILES)} Datei(en) ein...")
            files_array = []
            for test_file in FILES:
                print(f"  - {test_file}")
                with open(test_file, "rb") as f:
                    file_content = f.read()
                    file_content_base64 = base64.b64encode(file_content).decode('utf-8')
                    files_array.append({
                        "file_content": file_content_base64,
                        "file_name": test_file
                    })
                print(f"    {len(file_content)} Bytes")
            payload["files"] = files_array
        else:
            print("Modus: Sync ohne Dateien (nur user_text)")
            if not USER_TEXT:
                print("⚠️  WARNUNG: FILES ist leer und USER_TEXT ist leer!")
                print("   Mindestens eines von beiden muss angegeben werden.")
                return

    elif TEST_MODE == "text_only":
        # Nur Text, keine Datei
        print(f"Modus: Nur Text (keine Datei)")
        if not USER_TEXT:
            print("FEHLER: USER_TEXT muss für text_only Modus gesetzt sein!")
            return

    print(f"\n{'='*60}")
    print(f"API-Test mit Authentifizierung (SYNCHRON)")
    print(f"{'='*60}")
    print(f"Modus: {TEST_MODE}")
    print(f"API-Key: {API_KEY}")
    print(f"Aktion: {ACTION}")
    print(f"Dateien: {FILES if FILES else '(keine)'}")
    if USER_TEXT:
        print(f"Benutzertext: {USER_TEXT[:100]}..." if len(USER_TEXT) > 100 else f"Benutzertext: {USER_TEXT}")
    print(f"URL: {API_URL}")
    print(f"Timeout: {REQUEST_TIMEOUT} Sekunden ({REQUEST_TIMEOUT/60:.1f} Minuten)")
    print(f"{'='*60}\n")

    print("Sende Request...")
    print(f"Bitte warten (kann 1-3 Minuten dauern, max. {REQUEST_TIMEOUT/60:.0f} Min.)...\n")

    try:
        # API-Aufruf mit Timeout
        start_time = time.time()
        response = session.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT
        )
        elapsed_time = time.time() - start_time
        
        # Ergebnis ausgeben
        print(f"{'='*60}")
        print(f"Response erhalten")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        print(f"Dauer: {elapsed_time:.2f} Sekunden")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"\nResponse-Body:")
        
        # Versuche JSON zu parsen, zeige aber Rohinhalt bei Fehler
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print("⚠ Response ist kein JSON! Rohinhalt:")
            print(response.text[:1000])  # Erste 1000 Zeichen
            if len(response.text) > 1000:
                print(f"\n... ({len(response.text)} Zeichen insgesamt)")
        
        print(f"{'='*60}")
        
        # Status-basierte Hinweise
        if response.status_code == 401:
            print("\n⚠ Authentifizierung fehlgeschlagen:")
            print("   - Prüfen Sie, ob der API-Key korrekt ist")
            print("   - Der Key muss in customer_config.json vorhanden sein")
        elif response.status_code == 403:
            print("\n⚠ Zugriff verweigert:")
            print("   - Prüfen Sie, ob die Aktion für diesen Kunden erlaubt ist")
            print("   - Prüfen Sie, ob der Kunde aktiviert ist (active: true)")
        elif response.status_code == 200:
            print("\n✓ Anfrage erfolgreich!")
        
    except requests.exceptions.SSLError as e:
        print(f"\n❌ SSL-Fehler (häufig bei ngrok):")
        print(f"   {str(e)}")
        print("\n💡 Lösungen:")
        print("   1. Warten Sie 10 Sekunden und versuchen Sie es erneut")
        print("   2. Starten Sie ngrok neu (python start_with_ngrok.py)")
        print("   3. Testen Sie lokal: http://localhost:5000/analyze")
        
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout - Die Anfrage hat zu lange gedauert (>{REQUEST_TIMEOUT} Sekunden)")
        print(f"\n💡 Lösungsvorschläge:")
        print(f"   1. Erhöhen Sie REQUEST_TIMEOUT im Skript (aktuell: {REQUEST_TIMEOUT}s)")
        print(f"   2. Die Datei könnte zu groß oder komplex sein")
        print(f"   3. Azure OpenAI könnte ausgelastet sein - versuchen Sie es später")
        print(f"   4. Prüfen Sie die Server-Logs für weitere Details")
        print(f"\n💡 Alternativ: Nutzen Sie TEST_MODE = 'async' für asynchrone Verarbeitung")
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Verbindungsfehler:")
        print(f"   {str(e)}")
        print("\n💡 Prüfen Sie:")
        print("   1. Läuft der Server? (python api_server.py)")
        print("   2. Ist ngrok aktiv? (python start_with_ngrok.py)")
        
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler:")
        print(f"   {type(e).__name__}: {str(e)}")


# ============================================
# HAUPTPROGRAMM
# ============================================

if __name__ == "__main__":
    if TEST_MODE == "async":
        test_async()
    else:
        test_sync()


