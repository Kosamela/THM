# TryHackMe: 

**Difficulty:** Hard
**Operating System:** Linux
**Machine IP:** 10.114.131.93
**Room Link:** https://tryhackme.com/room/sequence

---

## 1. Reconnaissance

Initial machine scanning to identify open ports and running services.

```bash
# Nmap Scan
nmap --privileged -p- -sV -sC -T4 -v -oN nmap_pelen_skan.txt 10.114.131.93
```

**Full Nmap scan log:** [nmap_pelen_skan.txt](./nmap_pelen_skan.txt)

**Key Findings:**
* **Port 22 (SSH):** OpenSSH 8.2p1 Ubuntu 4ubuntu0.3
* **Port 80 (HTTP):** Apache httpd 2.4.41

## 2. Enumeration

Detailed analysis of open services. For the web server, I ran a hidden directory scan:

```bash
# Directory Brute-forcing
gobuster dir -u 10.114.131.93 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 40 -x php,txt,bak,tar.gz -o gobuster_wyniki.txt -b 404,400
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
Seems like a very useful thing when we get into internal. Maybe thats a docker?
```python
# Example script used
python3 exploit.py -u 10.114.131.93
```

## 4. Privilege Escalation

### User Flag
How did you stabilize the shell and get the `user.txt` file?

### Root Flag (System / Administrator)
After getting on the machine, I started gathering system information using `sudo -l` (or looking for SUID binaries).

## 5. Summary and Lessons Learned

* **What went well:** 
* **What I learned:** 
* **Where I got stuck (Rabbit holes):** 