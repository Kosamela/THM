# SSTI
```
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}
```
self - to po prostu aktualny obiekt szablonu (nasz punkt startowy).  
__init__ - wbudowana metoda inicjalizująca. Odwołujemy się do niej tylko po to, żeby móc przejść wyżej w strukturze Pythona.  
__globals__ - to jest złota góra! Słownik zawierający wszystkie globalne zmienne i funkcje dostępne w danym środowisku.  
__builtins__ - słownik wewnątrz globals, który trzyma wbudowane funkcje Pythona (np. eval, print czy właśnie __import__).  
__import__('os') - importujemy bibliotekę systemową os, która pozwala gadać z systemem operacyjnym (Linux/Windows).  
popen('id') - funkcja z biblioteki os, która otwiera proces i wykonuje komendę id w terminalu.  
read() - odczytuje wynik (output) z terminala, żeby mógł się wyświetlić na stronie.  
Silnik Pythona pozwala na zapisywanie tekstów (stringów) w postaci kodów szesnastkowych, poprzedzając każdą literę znakiem \x.  
Litera o to w hex 6f. Więc w Pythonie '\x6f' to to samo co 'o'.  
Litera s to w hex 73. Więc w Pythonie '\x73' to to samo co 's'.  
Zatem słowo 'os' to '\x6f\x73'.  
URL-encoding: / => %2f  
Hex-encoding: _ => \x5f, 0x5f  
Unicode-encoding: % => \u0025  
Case Sensitivity (using mixed-cases to avoid detection)  
Obfuscation using White Space and Delimiters  
Zastępujemy każdy pojedynczy string w naszym ładunku jego szesnastkowym odpowiednikiem. Nawiasy, słowo self i wywołania () zostawiamy w spokoju, bo to one tworzą strukturę gramatyczną, która mówi serwerowi: "hej, wykonaj ten kod".
