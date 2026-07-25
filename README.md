# THM

## Playbook (moja ściąga pentesterska)

Główny plik to `Playbook.md` — ściąga ułożona wg **faz kill chain** (recon → access → privesc → creds → AD → lateral → pivot → exfil → cloud → reporting), a nie wg narzędzi. Z niego generuję `Playbook.html` — przeszukiwalny, samowystarczalny, kolorowany wg fazy. Płaską wersję trzymam w `Commands.md`.

### Przebudowa HTML po edycji
```bash
python3 Scripts/playbook_html.py     # Playbook.md -> Playbook.html
```

### Jak dodaję nową treść
- **Podsekcja istniejącej fazy** — wrzucam `## N.N Tytuł` w odpowiednie miejsce w `Playbook.md` (np. `## 2.15 ...`). Nic więcej nie trzeba.
- **Nowa faza top-level** (`# N. Tytuł`) — dopisuję kolor w `Scripts/playbook_html.py` w słowniku `PHASE_META`, czyli `"N": ("#hex", "Skrót")`, i dorzucam wiersz do ręcznego TOC na górze `Playbook.md` (nawigacja w HTML robi się sama, ale tabelka w md jest ręczna).
- **Kontrola przed buildem** — bloki kodu muszą być domknięte: liczba linii z potrójnym backtickiem ma być parzysta — sprawdzam ````grep -c '^```' Playbook.md````. Dopiero potem przebudowuję HTML.

### Materiały źródłowe
Rozbudowuję z modułów OSCP/PEN-200 w `/home/kali/Offsec/Materialy/` (tytuły sekcji w tych plikach to `**N.N. Title**`, kod w fenced-blokach).

## Challenges

- [ElBandito](ElBandito/ElBandito.md)

- [WhatsYourName](Whatsyourname/WhatsYourName.md)

- [Extract](Extract/Extract.md)

- [Voyager](Voyager/Voyage.md)

- [Sequence](Sequence/Sequence.md)