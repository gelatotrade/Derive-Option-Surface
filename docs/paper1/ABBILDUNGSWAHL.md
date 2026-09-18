# Wie die neun Abbildungen ausgewaehlt wurden

18.09.2026. Drei unabhaengige Entwurfssaetze mit je acht Abbildungen (Blickwinkel Mechanismus, Empirie, Praktiker),
danach zwei Juroren mit verschiedenen Linsen: ein Referee, der gegen die Ergebnisdateien nachgerechnet hat, und eine
Gestaltungspruefung auf Lesbarkeit im zweispaltigen CAS-Satz bei 8 pt in Graustufen.

## Worin die Juroren uebereinstimmten

| Slot | Beide | Warum |
|---|---|---|
| T1 | P-T1 | Einzige Abbildung, die drei Mark-Pfade und drei Einheiten auf 2,8 Zoll traegt, weil alle Panels dieselbe x-Achse teilen. |
| T2 | E-T2 zusammen mit P-T2 | Der Referee wollte P-T2s Gebuehr-Hexbin als drittes Panel von E-T2, die Gestaltung wollte dieselbe Zusammenlegung von der anderen Seite. |
| Konzentration | E4 | Einzige Fassung, die beide Teile der H1-Regel zeigt: die Konzentration und die Koeffizienten, an denen H1 scheitert. |
| Zellenkarte | E5 | Einzige Gitterabbildung mit einer poolbaren Einheit und mit getrennter Darstellung von Effektgroesse und Belastbarkeit. |

## Worin sie auseinandergingen, und wie entschieden wurde

**Klassenabbildung: E3 gegen P2.** Der Referee wollte E3, weil nur dort steht, wie wenige Wallets eine Klasse tragen.
Die Gestaltung wollte P2, weil dessen Balken je Klasse lesbar ist und E3s Schwarm aus 10 749 Punkten als schwarzer
Block druckt. Entschieden: P2s Aufbau mit E3s Zahlen. Der Befund, dass 98,8 Prozent der Fills der dominanten Maker und
92,4 Prozent der MM-Programm-Fills von genau den zehn Verlust-Wallets aus H1 stammen, ist nachgerechnet und bleibt.

**Einheitenabbildung: E1 gegen P4.** Der Referee wollte E1 als Leseregel vor allen Ergebnissen. Die Gestaltung hat E1
mit 5 bewertet, weil seine auf das Gesamtmittel normierte Logachse bei einem Bezugswert von 0,264 kippen kann, lobt
aber E1s Panel b. Entschieden: P4 als Traeger, erweitert um E1s Panel b. Beide Befunde bleiben, die gefaehrliche Achse
faellt weg.

**Markqualitaet: Hauptteil oder Anhang.** Der Referee wollte EA1 im Hauptteil, weil das der am haertesten angegriffene
Punkt sein wird. Die Gestaltung wollte P-A1 im Anhang und hielt EA1 mit fuenf Zeichenflaechen fuer ueberladen.
Entschieden: Anhang, aber als eine gekuerzte Abbildung aus beiden, und im Text frueh referenziert. Der entlastende
Befund ist eine Nullbeziehung, und eine Nullbeziehung braucht keinen Hauptteil-Slot.

## Die Luecke, die kein Entwurf abgedeckt hat

Keine der 21 Abbildungen hatte eine Kalenderachse. Drei Folgen: H3 haette als einzige praeregistrierte Hypothese kein
Bild bekommen, obwohl sie als einzige ein Ereignis, ein Fenster und 100 Placebos hat. Die Stichprobe umspannt 33 Monate
und ist nachweislich nicht homogen, die Klasse MM-Programm ist erst ab dem 20.11.2024 vergebbar und HYPE tritt erst am
10.11.2025 in die Stichprobe ein. Und das eine Wallet, das 39,0 Prozent des Maker-Verlusts traegt, koennte in wenigen
Monaten aktiv gewesen sein. Deshalb gibt es F6 mit gemeinsamer Monatsachse.

Eine Korrektur am Juryurteil: der Referee nennt den 24.10.2025 als Eintritt von HYPE. Nachgerechnet ist der erste
HYPE-Fill der Stichprobe am 10.11.2025 22:06 UTC, davor null Fills.

## Was aus der Pruefung sofort in den Code ging

Der Referee hat einen Widerspruch gefunden, der nichts mit Abbildungen zu tun hat: die Kopfzahl zu H4 rechnete mit
9 999 Bootstrap-Ziehungen, die Sensitivitaetstabelle mit 1 999, und genau eine Zelle kippte dadurch ueber die
Ablehnungsschwelle. Behoben, neu gerechnet, mit einem Waechter auf den Mechanismus abgesichert. Die Urteile zu H1
bis H4 aendern sich nicht.
