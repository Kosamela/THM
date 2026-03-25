# Reconnaissance
## Nmap
```
nmap -p- -sV -sC -T4 -v 10.114.185.137
```
```
Scanning 10.114.185.137 [65535 ports]
Discovered open port 80/tcp on 10.114.185.137
Discovered open port 22/tcp on 10.114.185.137
Discovered open port 2222/tcp on 10.114.185.137

PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.11 (Ubuntu Linux; protocol 2.0)
80/tcp   open  http    Apache httpd 2.4.58 ((Ubuntu))
|_http-favicon: Unknown favicon MD5: 1B6942E22443109DAEA739524AB74123
|_http-generator: Joomla! - Open Source Content Management
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
| http-robots.txt: 16 disallowed entries (15 shown)
| /joomla/administrator/ /administrator/ /api/ /bin/ 
| /cache/ /cli/ /components/ /includes/ /installation/ 
|_/language/ /layouts/ /libraries/ /logs/ /modules/ /plugins/
|_http-server-header: Apache/2.4.58 (Ubuntu)
|_http-title: Home
2222/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
## Gobuster
```
gobuster dir -u http://10.114.185.137 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 40 -x php,txt,bak,tar.gz -o gobuster_wyniki.txt -b 404,400
```
```
php                 (Status: 403) [Size: 279]
/media                (Status: 301) [Size: 316] [--> http://10.114.185.137/media/]
/templates            (Status: 301) [Size: 320] [--> http://10.114.185.137/templates/]
/modules              (Status: 301) [Size: 318] [--> http://10.114.185.137/modules/]
/images               (Status: 301) [Size: 317] [--> http://10.114.185.137/images/]
/index.php            (Status: 200) [Size: 8045]
/plugins              (Status: 301) [Size: 318] [--> http://10.114.185.137/plugins/]
/includes             (Status: 301) [Size: 319] [--> http://10.114.185.137/includes/]
/language             (Status: 301) [Size: 319] [--> http://10.114.185.137/language/]
/README.txt           (Status: 200) [Size: 4942]
/components           (Status: 301) [Size: 321] [--> http://10.114.185.137/components/]
/cache                (Status: 301) [Size: 316] [--> http://10.114.185.137/cache/]
/api                  (Status: 301) [Size: 314] [--> http://10.114.185.137/api/]
/libraries            (Status: 403) [Size: 279]
/robots.txt           (Status: 200) [Size: 764]
/tmp                  (Status: 301) [Size: 314] [--> http://10.114.185.137/tmp/]
/LICENSE.txt          (Status: 200) [Size: 18092]
/layouts              (Status: 301) [Size: 318] [--> http://10.114.185.137/layouts/]
/administrator        (Status: 301) [Size: 324] [--> http://10.114.185.137/administrator/]
/configuration.php    (Status: 200) [Size: 0]
/htaccess.txt         (Status: 200) [Size: 6858]
/cli                  (Status: 301) [Size: 314] [--> http://10.114.185.137/cli/]
/server-status        (Status: 403) [Size: 279]
```
### robots.txt
```
# If the Joomla site is installed within a folder
# eg www.example.com/joomla/ then the robots.txt file
# MUST be moved to the site root
# eg www.example.com/robots.txt
# AND the joomla folder name MUST be prefixed to all of the
# paths.
# eg the Disallow rule for the /administrator/ folder MUST
# be changed to read
# Disallow: /joomla/administrator/
#
# For more information about the robots.txt standard, see:
# https://www.robotstxt.org/orig.html

User-agent: *
Disallow: /administrator/
Disallow: /api/
Disallow: /bin/
Disallow: /cache/
Disallow: /cli/
Disallow: /components/
Disallow: /includes/
Disallow: /installation/
Disallow: /language/
Disallow: /layouts/
Disallow: /libraries/
Disallow: /logs/
Disallow: /modules/
Disallow: /plugins/
Disallow: /tmp/
```
