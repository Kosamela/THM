#!/usr/bin/env python3
import sys
import subprocess

# 1. Sprawdzenie, czy użytkownik podał adres IP
if len(sys.argv) != 2:
    print(f"Użycie: python3 {sys.argv[0]} <adres_IP>")
    sys.exit(1)

ip_address = sys.argv[1]
print(f"[*] Rozpoczynam wyliczanie RID dla IP: {ip_address} (od 500 do 2000)...\n")

# 2. Główna pętla
for rid in range(500, 2001):
    # Konstruowanie komendy (flaga -c pozwala przekazać komendę bezpośrednio)
    command = ["rpcclient", "-U", "", "-N", ip_address, "-c", f"queryuser {rid}"]
    
    try:
        # 3. Wykonanie komendy w tle i przechwycenie wyniku (stdout)
        result = subprocess.run(command, capture_output=True, text=True)
        
        # 4. Przeszukiwanie wyniku linijka po linijce
        for line in result.stdout.splitlines():
            if "User Name" in line:
                # Wypisanie sformatowanego wyniku na ekran
                print(f"[RID: {rid}] {line.strip()}")
                
    except KeyboardInterrupt:
        print("\n[-] Przerwano przez użytkownika (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Błąd podczas sprawdzania RID {rid}: {e}")

print("\n[*] Zakończono skanowanie.")
