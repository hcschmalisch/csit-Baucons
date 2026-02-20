import json
import secrets
import os

def generate_api_key(customer_id):
    """Generiert einen sicheren API-Key"""
    random_part = secrets.token_urlsafe(16)
    return f"{customer_id}-key-{random_part}"

def add_customer():
    """Interaktives Hinzufügen eines neuen Kunden"""
    print("=" * 60)
    print("Neuen Kunden hinzufügen")
    print("=" * 60)
    
    # Lade existierende Konfiguration
    config_path = os.path.join(os.path.dirname(__file__), 'customer_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"customers": {}}
    
    # Sammle Kundeninformationen
    customer_id = input("\nKunden-ID (z.B. customer-003): ").strip()
    customer_name = input("Kundenname (z.B. Firma GmbH): ").strip()
    
    # Generiere API-Key
    api_key = generate_api_key(customer_id)
    print(f"\n✓ Generierter API-Key: {api_key}")
    
    # Definiere Aktionen
    print("\n--- Erlaubte Aktionen definieren ---")
    allowed_actions = {}
    
    while True:
        action_name = input("\nAktionsname (z.B. analyze-document, leer für fertig): ").strip()
        if not action_name:
            break
        
        endpoint = input("  Endpoint URL: ").strip()
        agent = input("  Agent Name: ").strip()
        description = input("  Beschreibung (optional): ").strip()
        
        allowed_actions[action_name] = {
            "endpoint": endpoint,
            "agent": agent,
            "description": description if description else f"Aktion: {action_name}"
        }
        print(f"  ✓ Aktion '{action_name}' hinzugefügt")
    
    if not allowed_actions:
        print("\n⚠ Mindestens eine Aktion muss definiert werden!")
        return
    
    # Erstelle Kundeneintrag
    customer_entry = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "active": True,
        "allowed_actions": allowed_actions
    }
    
    # Füge zur Konfiguration hinzu
    config["customers"][api_key] = customer_entry
    
    # Speichere Konfiguration
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("✓ Kunde erfolgreich hinzugefügt!")
    print("=" * 60)
    print(f"\nAPI-Key für {customer_name}:")
    print(f"  {api_key}")
    print(f"\nErlaubte Aktionen: {', '.join(allowed_actions.keys())}")
    print("\n⚠ Wichtig: Geben Sie den API-Key sicher an den Kunden weiter!")
    print("=" * 60)

def list_customers():
    """Listet alle Kunden auf"""
    config_path = os.path.join(os.path.dirname(__file__), 'customer_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("⚠ Keine Kundenkonfiguration gefunden!")
        return
    
    customers = config.get("customers", {})
    
    print("\n" + "=" * 60)
    print(f"Registrierte Kunden ({len(customers)})")
    print("=" * 60)
    
    for api_key, customer in customers.items():
        status = "✓ Aktiv" if customer.get("active") else "✗ Deaktiviert"
        print(f"\n{customer['customer_name']} ({customer['customer_id']})")
        print(f"  Status: {status}")
        print(f"  API-Key: {api_key}")
        print(f"  Aktionen: {', '.join(customer.get('allowed_actions', {}).keys())}")
    
    print("\n" + "=" * 60)

def toggle_customer_status():
    """Aktiviert/Deaktiviert einen Kunden"""
    config_path = os.path.join(os.path.dirname(__file__), 'customer_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("⚠ Keine Kundenkonfiguration gefunden!")
        return
    
    customers = config.get("customers", {})
    
    print("\n" + "=" * 60)
    print("Kunden-Status ändern")
    print("=" * 60)
    
    # Zeige Kunden
    print("\nVerfügbare Kunden:")
    for i, (api_key, customer) in enumerate(customers.items(), 1):
        status = "Aktiv" if customer.get("active") else "Deaktiviert"
        print(f"{i}. {customer['customer_name']} ({customer['customer_id']}) - {status}")
    
    # Wähle Kunde
    try:
        choice = int(input("\nKunde auswählen (Nummer): ")) - 1
        api_key = list(customers.keys())[choice]
        customer = customers[api_key]
    except (ValueError, IndexError):
        print("⚠ Ungültige Auswahl!")
        return
    
    # Toggle Status
    current_status = customer.get("active", True)
    new_status = not current_status
    customer["active"] = new_status
    
    # Speichere
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    status_text = "aktiviert" if new_status else "deaktiviert"
    print(f"\n✓ Kunde '{customer['customer_name']}' wurde {status_text}!")

def main():
    while True:
        print("\n" + "=" * 60)
        print("Kunden-Verwaltung")
        print("=" * 60)
        print("1. Neuen Kunden hinzufügen")
        print("2. Alle Kunden auflisten")
        print("3. Kunden aktivieren/deaktivieren")
        print("4. Beenden")
        print("=" * 60)
        
        choice = input("\nWählen Sie eine Option: ").strip()
        
        if choice == "1":
            add_customer()
        elif choice == "2":
            list_customers()
        elif choice == "3":
            toggle_customer_status()
        elif choice == "4":
            print("\nAuf Wiedersehen!")
            break
        else:
            print("⚠ Ungültige Option!")

if __name__ == "__main__":
    main()
