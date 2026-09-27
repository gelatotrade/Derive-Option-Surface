# Historie bereinigen (Audit A01)

Stand 25.09.2026, Branch `paper2-kapital` bei `d51ede0`, noch ohne Upstream. Diese Anleitung beschreibt, wie die
Konto-Kennungen aus der Historie von Paper 2 verschwinden, bevor der Branch zum ersten Mal gepusht wird. Sie
schreibt nichts selbst um. Das Umschreiben geschieht auf einem **neuen** Branch; `paper2-kapital` bleibt, bis der
neue Branch geprüft ist. Die Präregistrierung `1d13227` und alle Commits davor bleiben unverändert.

Roh-IDs und unsalzte Hashes sind hier bewusst nicht wiedergegeben (Nachtrag 1.4).

## 1. Was im Arbeitsbaum schon behoben ist

Diese Änderungen liegen im Arbeitsbaum und müssen vor dem Umschreiben committet werden (Commit F):

- `tests/test_p2_ids.py`: `TOP` ist eine synthetische Liste (104, 101, 110, ...), das zweite Konto ist 4711. Neue
  Wächter: keine unsalzten Hashes in `results/`, `docs/paper2/`, `paper2/` **und** `tests/` (jetzt auch `.py`),
  keine Roh-IDs der Top-10 mit fünf und mehr Stellen in `tests/` (liest `data/p2/books/top_makers.json`, ohne die
  Datei übersprungen), keine `.DS_Store`/`.Rhistory` im Index, keine privaten Fixtures im Index.
- Die kontoidentifizierenden Fixtures liegen jetzt unter `data/p2/fixtures_private/` (gitignoriert):
  `pm_chain_accounts.json`, `sm_chain_accounts.json`, `books_chain_snapshot.json`, `books_events_day.json`,
  `b1_chain_cases.json` und der Generator `gen_b1_fixture.py`. Die Tests lesen sie dort und werden übersprungen,
  wenn sie fehlen (wie die v2-core-Fälle). `gen_a4_chain_fixtures.py` bleibt in `tests/fixtures/p2`, weil er auch
  die öffentlichen Fälle `sm_chain_cases.json` und `pm_chain_cases.json` erzeugt; die Kontofälle schreibt er jetzt
  nach `data/p2/fixtures_private/`.
- Der nicht identifizierende Teil von `books_chain_snapshot.json` (Adressen der Assets, Manager, Cash-Asset,
  Referenz des Encoders für die Konten 1 und 2) liegt öffentlich in `tests/fixtures/p2/books_registry.json`,
  damit die Tests der Registry weiterlaufen. Die dekodierten Kontostände, die `test_p2_books.py` als Literale
  prüfte (Cash-Saldo, ein Bein), stehen jetzt in der privaten Fixture unter `expected`.
- `tests/test_p2_books.py`: die Roh-ID neben dem Label M3 ist durch den Platzhalter 4242 ersetzt.
- `.DS_Store`, `paper/.DS_Store` und `paper/social/.Rhistory` sind aus dem Index genommen (A69) und in
  `.gitignore`.

In einem öffentlichen Klon ohne `data/` werden dadurch 19 Tests wegen fehlender privater Fixtures übersprungen und
der Wächter für Roh-IDs (1 Test) mangels Liste; auf dem Rechner des Autors laufen alle.

## 2. Betroffene Commits und Dateien

Geprüft mit `python3 scripts/p2_history_scrub.py check 1d13227^..paper2-kapital` (zählt nur, nennt keine IDs):

| Datei | Befund | Commits |
|---|---|---|
| `tests/fixtures/p2/pm_chain_accounts.json` | ganze Kontostände, 3 unsalzte Hashes | `e7361d2` bis `d51ede0` (13) |
| `tests/fixtures/p2/sm_chain_accounts.json` | ganze Kontostände, 11 unsalzte Hashes | `e7361d2` bis `d51ede0` (13) |
| `tests/fixtures/p2/books_chain_snapshot.json` | Multicall-Antwort eines Top-10-Kontos, 1 Hash | `e7361d2` bis `d51ede0` (13) |
| `tests/fixtures/p2/books_events_day.json` | Tagesereignisse mit 109 Transaktions-Hashes und `tx_hash` des Fills, 1 Hash | `e7361d2` bis `d51ede0` (13) |
| `tests/fixtures/p2/b1_chain_cases.json` | Bücher von M2 und M3 an je einem Tag | `591d2d5` bis `d51ede0` (7) |
| `tests/fixtures/p2/gen_b1_fixture.py` | zwei Roh-IDs, die in der Fixture mit ihrem Label stehen | `591d2d5` bis `d51ede0` (7) |
| `tests/test_p2_ids.py` | geordnete Top-10-Liste, also der Schlüssel Roh-ID zu M1..M10 | `591d2d5` bis `d51ede0` (7) |
| `tests/test_p2_books.py` | eine Roh-ID neben dem Label M3 | `03ee4ca` bis `d51ede0` (4) |
| `results/p2/params/BTC_pm2_overrides.json` | 15 unsalzte Hashes | `e7361d2` bis `c4fcb59` (6) |
| `results/p2/params/ETH_pm2_overrides.json` | 16 unsalzte Hashes | `e7361d2` bis `c4fcb59` (6) |
| `results/p2/params/HYPE_pm2_overrides.json` | 10 unsalzte Hashes | `e7361d2` bis `c4fcb59` (6) |
| `docs/paper2/DATENSTAND.md` | Hashes aller zehn dominanten Konten | `e7361d2` bis `c4fcb59` (6) |

Nicht betroffen: die Commit-Nachrichten und alle Commits vor `e7361d2`, also auch `1d13227`, `cccfc01`,
`9b1394f` und `bd11559` (Prüfung über alle 82 Commits des Branches). Die Punkte A24 und A69 liegen vor `1d13227`
und werden hier nicht bereinigt (Abschnitt 6).

## 3. Werkzeug

`scripts/p2_history_scrub.py` (Tests: `tests/test_p2_history_scrub.py`, darunter ein Lauf von
`git filter-branch` auf einem Wegwerf-Repository). Das Skript enthält keine IDs; Liste und Salt liest es aus
`data/p2` des Checkouts, aus dem es gestartet wird.

- `index` bearbeitet den Index eines Commits, wie ihn `git filter-branch --index-filter` übergibt: entfernt die
  sechs Fixture-Dateien aus `tests/fixtures/p2`; ersetzt in Textdateien unter `results/p2/`, `docs/paper2/`,
  `paper2/` und `tests/` jeden unsalzten Hash (Umkehr durch Durchprobieren bis 250 000) durch das p2ids-Label
  (M1..M10 oder X mit Salt, also dieselben Labels wie ab `591d2d5`); ersetzt in `tests/` Roh-IDs der Top-10 mit fünf
  und mehr Stellen durch 4242 und in einem `tests/test_p2_ids.py` mit der echten `TOP`-Liste alle zehn IDs durch
  die synthetische Liste. Dateien von Paper 1 fasst es nicht an. Auf einem schon bereinigten Stand ändert es nichts.
- `check <Bereich>` durchsucht jeden Commit und gibt je Datei nur Zahlen aus; Exit-Code 1, wenn etwas übrig ist.

## 4. Ablauf

Voraussetzungen: alle Korrekturen des Audits auf `paper2-kapital` committet, Suite grün, Arbeitsbaum ohne
Änderungen an getrackten Dateien, `data/p2/secret_salt.txt` und `data/p2/books/top_makers.json` vorhanden. Aus dem
Wurzelverzeichnis des Repos, in zsh oder bash:

```sh
# 1. neuer Branch, umgeschrieben wird nur dieser, ab Stufe A (e7361d2)
git status --short --untracked-files=no            # muss leer sein
git branch paper2-kapital-bereinigt paper2-kapital
export P2_SCRUB="$PWD/scripts/p2_history_scrub.py"
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch \
  --index-filter 'python3 "$P2_SCRUB" index' \
  -- e7361d2^..paper2-kapital-bereinigt

# 2. prüfen
python3 scripts/p2_history_scrub.py check 1d13227^..paper2-kapital-bereinigt   # 0 Dateien, Exit 0
git diff --stat paper2-kapital paper2-kapital-bereinigt                        # leer: Endstand gleich
git merge-base --is-ancestor 1d13227 paper2-kapital-bereinigt && echo "1d13227 unveraendert"
git rev-list --reverse e7361d2^..paper2-kapital > data/p2/p2_alt.txt
git rev-list --reverse e7361d2^..paper2-kapital-bereinigt > data/p2/p2_neu.txt
paste -d' ' data/p2/p2_alt.txt data/p2/p2_neu.txt | while read alt neu; do
  p=$(git diff --quiet "$alt:docs/paper2/PRAEREGISTRIERUNG.md" "$neu:docs/paper2/PRAEREGISTRIERUNG.md" && echo gleich || echo ABWEICHUNG)
  d=$([ "$(git log -1 --format='%an %ad %cn %cd %s' "$alt")" = "$(git log -1 --format='%an %ad %cn %cd %s' "$neu")" ] && echo gleich || echo ABWEICHUNG)
  echo "$(git rev-parse --short "$alt") -> $(git rev-parse --short "$neu")  Praeregistrierung $p, Metadaten $d  $(git log -1 --format=%s "$alt")"
done

# 3. Branches tauschen, Sicherung von filter-branch entfernen
git branch -m paper2-kapital paper2-kapital-unbereinigt   # nur lokal, nie pushen
git branch -m paper2-kapital-bereinigt paper2-kapital
git checkout -q paper2-kapital
git update-ref -d refs/original/refs/heads/paper2-kapital-bereinigt
```

Bricht Schritt 1 mit „A previous backup already exists“ ab, liegt noch eine Sicherung eines früheren Laufs vor;
dann den neuen Branch löschen und neu anlegen und `filter-branch -f` verwenden. Schritt 2 muss in jeder Zeile
„gleich“ zeigen, `git diff --stat` muss leer sein.

**Testlauf.** Am 25.09.2026 lief diese Folge in drei frischen Klonen dieses Repos (`git clone --no-local`), zuletzt
wörtlich aus dem Block oben; die Änderungen aus Abschnitt 1 waren dort als Commit F simuliert: 14 Commits umgeschrieben in rund 6 s,
`check` danach 0 Dateien (vorher 12), Endstand identisch, `PRAEREGISTRIERUNG.md` sowie Autor, Committer, Datum und
Nachricht in jedem Paar gleich, die Labels in den umgeschriebenen `*_pm2_overrides.json` bytegleich mit denen ab
`591d2d5`. Alle Läufe ergaben dieselben neuen Hashes. In den umgeschriebenen Commits fehlen die sechs Fixtures;
die damaligen Tests dieser Commits laufen dort ohne sie nicht, der Endstand ist davon nicht berührt.

## 5. Folgen für die zitierten Hashes

`1d13227` (Präregistrierung) und alle Commits davor behalten ihren Hash. Alle Commits ab `e7361d2` erhalten neue
Hashes, der Inhalt von `PRAEREGISTRIERUNG.md` und die Zeitstempel bleiben je Commit gleich. Der Testlauf ergab:

| alt | neu | Commit |
|---|---|---|
| `e7361d2` | `a2aa7c5` | Stufe A |
| `eb534fe` | `1d6b2de` | Nachtrag 1 |
| `9465210` | `3872ed0` | Nachtrag 2 |
| `bfc34c8` | `985ec99` | Nachtrag 3 |
| `c4fcb59` | `396e180` | Nachtrag 4 |
| `591d2d5` | `f459643` | Stufe B |
| `93b42bc` | `defbb03` | Stufe C |
| `03ee4ca` | `7634832` | MM-Sensitivität H2 |

Die Werte gelten nur, wenn Skript, Salt und Liste unverändert sind; massgeblich ist die Ausgabe von Schritt 2 des
echten Laufs. Danach nachzuziehen (auf dem bereinigten Branch, als neuer Commit):

- `paper2/main.tex` Z. 669 bis 671 (`eb534fe`, `9465210`, `bfc34c8`, `c4fcb59`) und der Kommentar
  `% src git:c4fcb59` Z. 679. `1d13227` in Z. 666 und 678 bleibt.
- `docs/paper2/ZAHLENPRUEFUNG.md` neu erzeugen (`scripts/p2_number_check.py`). Die Prüfung löst Hashes mit
  `git cat-file -e` auf; solange der alte Branch lokal liegt, findet sie die alten Hashes noch, in einem frischen
  Klon nicht mehr.
- `docs/paper2/MANUSKRIPT.md` Z. 305 und 316, `docs/paper2/ABBILDUNGSWAHL.md` Z. 813 und
  `tests/test_p2_number_check.py` (Beispiele mit `c4fcb59`, nur der Einheitlichkeit halber; die Tests lösen
  Hashes über einen Stub auf). `derive_surface/social_p2.py` nennt nur `1d13227` und bleibt.
- `docs/paper2/AUDIT.md` ist ein datierter Bericht über den alten Stand und bleibt; ein Satz mit Verweis auf diese
  Datei genügt.
- Ein datierter **Nachtrag 5** am Ende von `PRAEREGISTRIERUNG.md`: Grund (A01), die Zuordnung alt zu neu für die
  vier Nachträge, die Feststellung, dass Text und Zeitstempel unverändert sind, und dass kein registriertes Urteil
  berührt ist. Ihn erst nach dem Lauf schreiben, weil die neuen Hashes erst dann feststehen. Das Manuskript nennt
  dann die neuen Hashes und verweist auf Nachtrag 5 (siehe A02). Nachtrag 5 auch in
  `docs/paper2/PREREGISTRATION_EN.md` übersetzen und den Blob-Hash im Kopf nachziehen; `tests/test_p2_prereg_en.py`
  schlägt sonst fehl. Die Übersetzung selbst nennt nur `1d13227` und den Blob-Hash des Originals, der beim
  Umschreiben gleich bleibt.

## 6. Nicht Teil dieser Bereinigung

- **A24, offene Entscheidung des Autors zu Paper 1.** `results/p1/h1_lorenz.csv` enthält 1 388 Wallet-Adressen
  (Commit `a26a59d`, in beiden lokalen Branches). `a26a59d` ist ein Vorfahre von `1d13227`. Die Adressen aus der
  Historie zu nehmen, hiesse ab `a26a59d` umzuschreiben; dann ändern sich `1d13227`, alle Hashes von Paper 2 und
  die späten Hashes von Paper 1 (die Präregistrierung von Paper 1, `3fd9caa`, `7f67eaf`, `837595c`, liegt davor).
  Das Skript fasst `results/p1` nicht an, und `check` sucht nicht nach Adressen. Im Arbeitsbaum ist nichts
  geändert.
- **A69.** `.DS_Store` (`fdb8014`), `paper/.DS_Store` und `paper/social/.Rhistory` (`0afff2c`) liegen ebenfalls
  vor `1d13227` und bleiben in der Historie; sie sind nur aus dem Index genommen. `.DS_Store` kann Dateinamen des
  lokalen Ordners enthalten.
- **Restliche schwache Merkmale.** Die alten Fassungen von `tests/test_p2_books.py` (`e7361d2` bis `d51ede0`)
  enthalten dekodierte Werte eines Top-10-Kontos an einem Block (Cash-Saldo, ein Optionsbein), aber keine ID und
  kein Label. Wer alle Konten an diesem Block per `eth_call` abfragt, fände das Konto; das Skript lässt diese
  Literale stehen.
- **Grenzen der Pseudonyme.** Die öffentliche Trade-Historie (`get_trade_history`) liefert je Fill die
  `subaccount_id`. Die Rangfolge M1 bis M10 (Nachtrag 1.4: meiste Maker-Fills in der Stichprobe von Paper 1) kann
  daher jeder nachrechnen, der das Tape lädt. Auch die X-Labels der Override-Konten lassen sich über die
  öffentlichen `LibOverrideUpdated`-Ereignisse und die Blocknummern in `results/p2/params/*_overrides.json`
  zuordnen. Die Pseudonyme schützen vor beiläufiger Zuordnung, nicht vor gezielter. Die Bereinigung stellt den
  Zustand her, den Nachtrag 1.4 beschreibt; das Papier sollte keinen weitergehenden Schutz behaupten.

## 7. Empfehlung

1. Jetzt bereinigen, solange der Branch lokal ist: Korrekturen committen, Abschnitt 4 ausführen, Nachtrag 5
   schreiben, Zitate nachziehen, Papier bauen, `scripts/p2_number_check.py` und die Suite laufen lassen. Die
   Kosten sind vier neue Nachtrags-Hashes bei unverändertem Text und unveränderter Präregistrierung.
2. Nur den bereinigten Branch pushen (`git push -u origin paper2-kapital`), nie `paper2-kapital-unbereinigt` und
   nie `git push --all`. Beim Integrieren einen Merge-Commit verwenden, weder Squash noch Rebase (A02). Danach die
   neuen Hashes extern verankern (OpenTimestamps oder OSF, A02).
3. `paper2-kapital-unbereinigt` lokal behalten, bis Push und Verankerung stehen; erst dann löschen
   (`git branch -D paper2-kapital-unbereinigt`). Die alten Objekte bleiben bis zu `git gc` im lokalen Repository
   und werden nicht gepusht.
4. A24 getrennt entscheiden. Den Satz über die Pseudonyme im Abschnitt „Data, code and pre-registration“ an
   Abschnitt 6 ausrichten.
