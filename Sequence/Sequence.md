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
logout.php           (Status: 302) [Size: 0] [--> index.php]
settings.php         (Status: 302) [Size: 0] [--> login.php]
dashboard.php        (Status: 302) [Size: 1400] [--> login.php]
phpmyadmin           (Status: 301) [Size: 321] [--> http://10.114.179.101/phpmyadmin/]
server-status        (Status: 403) [Size: 279]
```
## 3. Initial Access

Describe step-by-step how you gained the initial foothold on the machine.

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