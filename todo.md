# particle system (instanced durch OpenGL)

**Idee**
Mithilfe von OpenGl

# shadowcasting

**Idee**
Vllt mithilfe von modernGL die pygamesurface in eine opengl textur verwandeln und dann mithilfe von vertex- und fragmentshadern shadowcasting zu machen.

Der hier hats hinbekommen:
https://github.com/MarkelZ/pygame-light2d
https://ncase.me/sight-and-light/
https://www.youtube.com/watch?v=Vtab9CHEMCA
https://github.com/ScriptLineStudios

# Async

**corroutines**

mit asyncio
https://blubberquark.tumblr.com/post/177559279405/asyncio-for-the-working-pygame-programmer-part-i


# Time

**delta time**

`dt = clock.get_fps(FPS) * 0.001`

**global timescale**

delta time mit irgendwas verkleinern / vergrößern BEVOR es weiter benutzt wird

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

*Neuschreiben*
Ich muss eigentlich als `elevation` die Azahl an höhentunterschied gemessen in `TILESIZE`.
Bsp: 
`1` ist eine Steigung von 0.5
`2` ist eine Steigung von 1.0


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


## Lighting

**Reference**

https://www.redblobgames.com/articles/visibility/
http://www.adammil.net/blog/v125_Roguelike_Vision_Algorithms.html
https://www.youtube.com/watch?v=NGFk44fY0O4

