# Reguli pentru Claude

## Stil de scriere

1. **Nu folosi niciodata caracterul em dash** (linia lunga, U+2014). Foloseste in loc: virgula, doua puncte,
   paranteze, sau cratima simpla `-`. La fel, evita en dash-ul (U+2013): pentru intervale
   foloseste cratima simpla, ex. `45-52 °C`. Regula se aplica peste tot: mesaje in chat, fisiere
   markdown, comentarii in cod, mesaje de commit.

2. **Fara termeni prea abstracti sau de nisa.** Utilizatorul are experienta tehnica reala
   (rooting, custom ROM-uri, flashing), dar nu cunoaste automat tot jargonul specializat.
   Cand apare un termen de nisa, explica-l scurt la prima folosire.

   Exemple de termeni care au nevoie de explicatie scurta:
   - *device tree / DTS* = fisierul care descrie hardware-ul pentru kernel
   - *zap shader* = firmware semnat fara de care GPU-ul nu porneste
   - *pressure-vessel* = containerul in care Steam ruleaza jocurile
   - *remoteproc* = procesoarele auxiliare din SoC (DSP audio, DSP senzori)

   Prefera formularea directa in locul celei academice. "Nu porneste GPU-ul fara fisierul
   asta" bate "dependenta de firmware semnat este o preconditie de initializare".

## Context proiect

Vezi [docs/verification-log.md](docs/verification-log.md) pentru starea verificata a
proiectului. Pe scurt: OnePlus 8 global (IN2013/IN2010, nume de cod `instantnoodle`),
transformat in consola portabila cu Linux mainline. Telefonul se sterge complet, fara
Android, fara modem/apeluri.

Documentul original de cercetare (`Gaming Mainline OnePlus 8.md`) contine erori
importante identificate in log-ul de verificare. Nu il trata ca sursa de adevar.
