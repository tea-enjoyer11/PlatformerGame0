# Slopes

**Kantige Slopes**
```
.......x
......xx
.....xxx
....xxxx
...xxxxx
..xxxxxx
.xxxxxxx
xxxxxxxx

colums
12345678
```
`x` gerhört zu der Slope, `.` ist Luft.

m = 0.5 (in diesem Beispiel)

y = m*x
Das Ergebnis einfach auf die Spieler Postion hinzufügen. (Erstnachdem der Spieler wieder auf localtile Höhe 0 gesetzt wurde, damit er nicht nach oben fliegt.)

**Runde Slopes**

Für diese könnte man eine art Cache für jede slope tile erstellen:
```
.......x
.......x
.......x
......xx
......xx
....xxxx
..xxxxxx
xxxxxxxx

colums
12345678
```
`x` gerhört zu der Slope, `.` ist Luft.
Man müsste für jeden Spalte die Höhe in px speichern, wo die slope aufhört, dann wenn man nach rechts läuft einfach die differenz der vorherigen und aktuellen auf die Spieler position addieren.
Für umgedrehte Slopes ist es dasselbe nur mit einem Vorzeichendreher.

