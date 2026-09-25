# Vol-Feed-Prüfung

Lauf 2026-09-17 14:48 UTC, Kopf-Block 44,817,461.

## Kontinuität

177 Stichproben zu je 200 Blöcken ab Block 800,000 im Abstand 250,000; 14 verschiedene Emitter.

| Feed | Stichproben mit Events | erste | letzte | Lücken nach dem Start | Forward erste → letzte |
|---|---|---|---|---|---|
| BTC | 166 | 2,050,000 | 44,800,000 | 6: 2,300,000, 2,550,000, 2,800,000, 3,300,000, 3,550,000, 4,800,000 | 42,943.40 → 76,648.13 |
| ETH | 166 | 2,050,000 | 44,800,000 | 6: 2,300,000, 2,550,000, 2,800,000, 3,300,000, 3,550,000, 4,800,000 | 2,317.43 → 2,446.14 |
| HYPE | 57 | 30,800,000 | 44,800,000 | keine | 47.61 → 79.34 |

### Mögliche Ersatz-Feeds (unbekannte Adresse, Forward innerhalb ±15% des letzten Kern-Forwards)

| Block | Kern-Feed | Kandidat | Forward | Events |
|---|---|---|---|---|
| 4,550,000 | BTC (zuletzt 59,473.14) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 56,564.28 | 2 |
| 5,050,000 | BTC (zuletzt 68,791.35) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 68,003.50 | 1 |
| 5,300,000 | BTC (zuletzt 67,817.62) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 67,402.02 | 1 |
| 5,550,000 | BTC (zuletzt 64,213.20) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 63,807.27 | 1 |
| 5,800,000 | BTC (zuletzt 71,024.44) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 70,343.02 | 2 |
| 6,050,000 | BTC (zuletzt 66,545.80) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 66,142.01 | 1 |
| 6,300,000 | BTC (zuletzt 72,341.64) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 71,698.72 | 2 |
| 6,550,000 | BTC (zuletzt 64,379.25) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 64,204.52 | 1 |
| 6,800,000 | BTC (zuletzt 64,003.11) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 63,943.73 | 2 |
| 7,050,000 | BTC (zuletzt 64,492.04) | 0x533acdac4ac1155a0946d0e1890712d98984de1e | 64,371.20 | 6 |
| 40,300,000 | HYPE (zuletzt 64.06) | 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 70.32 | 7 |
| 40,550,000 | HYPE (zuletzt 53.87) | 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 61.63 | 7 |
| 40,800,000 | HYPE (zuletzt 73.85) | 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 73.27 | 6 |
| 41,050,000 | HYPE (zuletzt 67.53) | 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 75.41 | 7 |

### Unbekannte Emitter (weder Kern- noch bekannte Neben-Feeds)

| Adresse | Stichproben | erste | letzte | Forward (Median) |
|---|---|---|---|---|
| 0x533acdac4ac1155a0946d0e1890712d98984de1e | 16 | 4,550,000 | 8,550,000 | 6.388e+04 |
| 0xd38bfb9f699ddf649de4f64201583b28ed147f3e | 70 | 24,800,000 | 42,300,000 | 165.8 |

## Formel: neueste signierte Kurve gegen Live-Mark-IV

Prüft `svi_vol` (Referenz-Tau, SVI-Forward) ohne Zeitverzug. Δ IV in Vol-Einheiten (0,01 = 1 Vol-Punkt).

| Underlying | Verfall | Optionen | Alter der signierten Kurve (s) | max. abs. Δ IV | Median abs. Δ IV |
|---|---|---|---|---|---|
| BTC | 20260918 | 76 | 19 | 0.00001 | 0.00001 |
| BTC | 20260919 | 34 | 19 | 0.00001 | 0.00000 |
| BTC | 20260920 | 34 | 19 | 0.00001 | 0.00000 |
| ETH | 20260918 | 62 | 20 | 0.00001 | 0.00000 |
| ETH | 20260919 | 54 | 20 | 0.00001 | 0.00001 |
| ETH | 20260920 | 58 | 20 | 0.00001 | 0.00000 |
| HYPE | 20260918 | 60 | 22 | 0.00001 | 0.00001 |
| HYPE | 20260919 | 38 | 22 | 0.00001 | 0.00001 |

## Gegenprobe: letzte onchain gepushte Kurve gegen Live-Mark-IV

Die onchain Kurve läuft dem Backend-Mark um die angegebene Zeit hinterher; die Abweichung misst diesen Verzug, nicht die Formel.

| Underlying | Verfall | Optionen | max. abs. Δ IV | Median abs. Δ IV | Alter der SVI (s) |
|---|---|---|---|---|---|
| BTC | 20260918 | 76 | 0.01839 | 0.00531 | 184 |
| BTC | 20260919 | 34 | 0.00223 | 0.00165 | 184 |
| BTC | 20260920 | 34 | 0.02075 | 0.00607 | 184 |
| ETH | 20260918 | 62 | 0.01622 | 0.01148 | 206 |
| ETH | 20260919 | 54 | 0.00589 | 0.00210 | 206 |
| ETH | 20260920 | 58 | 0.00583 | 0.00450 | 206 |
| HYPE | 20260918 | 60 | 0.05320 | 0.04070 | 188 |
| HYPE | 20260919 | 38 | 0.03274 | 0.01326 | 188 |
| HYPE | 20260920 | 0 | – | – | 188 |
