# TryHackMe: 

**Difficulty:** Easy
**Operating System:** Linux
**Attacker IP:** 192.168.180.79
**Machine IP:** 10.10.X.X
**Domain:** review.thm
**Room Link:** 

---

## 1. Reconnaissance

Initial machine scanning to identify open ports and running services.

```bash
# Nmap Scan
nmap --privileged -p- -sV -sC -T4 -v -oN nmap_pelen_skan.txt 10.10.X.X
```

📄 **Full Nmap scan log:** [nmap_pelen_skan.txt](./nmap_pelen_skan.txt)

**Key Findings:**
* **Port 22 (SSH):** OpenSSH version X.X
* **Port 80 (HTTP):** Apache server, login page

## 2. Enumeration

Detailed analysis of open services. For the web server, I ran a hidden directory scan:

```bash
# Directory Brute-forcing
gobuster dir -u 10.10.X.X -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 40 -x php,txt,bak,tar.gz -o gobuster_wyniki.txt -b 404,400
```

📄 **Full Gobuster results:** [gobuster_wyniki.txt](./gobuster_wyniki.txt)

**Interesting Paths / Vulnerabilities Found:**

```bash
# VHOSTS Brute-forcing
gobuster vhosts -u 10.10.X.X -w /usr/share/wordlists/amass/subdomains-top1mil-5000.txt -o vhosts_found.txt
```

📄 **Full Gobuster results:** [vhosts.txt](./vhosts_found.txt)

**Interesting Paths / Vulnerabilities Found:**

## 3. Initial Access

## 4. Privilege Escalation

### User Flag

<details>
  <summary>🚩 Click to see Mod Flag</summary>

  `THM{M0dH@ck3dPawned007}`
</details>

### Root Flag (System / Administrator)
<details>
  <summary>🚩 Click to see Root Flag</summary>

  `THM{M0dH@ck3dPawned007}`
</details>

## 5. Summary and Lessons Learned

* **What went well:** 
* **What I learned:** 
* **Where I got stuck (Rabbit holes):** 