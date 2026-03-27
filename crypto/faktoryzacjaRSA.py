from Crypto.Util.number import inverse, long_to_bytes
#from sympy import factorint
# Given values
n = 43941819371451617899582143885098799360907134939870946637129466519309346255747
# kurwa pierdolone gowno kwantowe zakomentowane gowno to faktoryzacja liczby pierwszej
#faktor = factorint(n)
#p, q = faktor.keys()
p = 205237461320000835821812139013267110933
q = 214102333408513040694153189550512987959
e = 65537
phi_n = (p-1)*(q-1)
d = inverse(e, phi_n)
print('klucz prywatny: ', d)

zaszyfrowany = 9002431156311360251224219512084136121048022631163334079215596223698721862766
plaintext = pow(zaszyfrowany, d, n)
odszyfrowany = long_to_bytes(plaintext)
print('zdekodowany: ', odszyfrowany.decode())
print('odszyfrowany: ', odszyfrowany)
