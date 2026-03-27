import requests

# Create a session object
session = requests.Session()

# Log in and maintain the session automatically
login_url = "http://python.thm/labs/lab4/login.php"
credentials = {"username": "admin", "password": "password123"}

response = session.post(login_url, data=credentials)

if response.status_code==200:
    print("[+] Login successful. Session cookies are stored automatically!")
    print(response)
# Po udanym logowaniu:
    print("[+] Aktualne ciasteczka w sesji:")
    cookies_dict = session.cookies.get_dict()
    print(cookies_dict)

# Jeśli chcesz konkretne ciasteczko:
    php_sid = cookies_dict.get('PHPSESSID')
    print(f"Twoje ID sesji to: {php_sid}")
else:
    print("[-] Login failed.")
