# Timmy Time Adventure for GFOS

Timmy Time Adventure 1.9 by Warcom Soft. (GPL-3 or later), from
https://github.com/warrior-rockk/timmy-time-adventure at commit
99e50ba0d3062773f4e08b93a4c31cf7fcd3946f, built for AmigaOS 3.2 / GFOS on
a 68040, 68060 or 68080. No FPU is needed.

Timmy is a little inventor whose time machine blows up and scatters him
and its pieces across history. Get him through the Jurassic, ancient
Egypt, the Middle Ages and the Wild West, past enemies and traps, to find
the four missing pieces and get back home. It was written for MS-DOS on a
486, in 320 x 200 with 256 colours, which is what it uses here too.

Status: see the pull request (stove build and lab).

## What is in the drawer

- `TimmyTime`: the game.
- `game.dat`, `player.dat`, `enemies.dat`, `objects.dat`, `collmap.dat`
  and one `.dat` and one `.bin` per level: the pictures, sounds, music,
  texts and maps.
- `DEMO.REC`, `DEMO2.REC`, `TUTORIAL.REC`: the title-screen demos and the
  tutorial, recorded by the author.
- `Libs/allegro4.library` and `Libs/acgame.library`: Allegro 4 for GFOS
  (gfopenallegro) on ACGame. The game opens them from its own `Libs/`.
- `User/`: your settings, high score and saved game (`TIMMY.CFG`), made
  the first time you play. Updates and `GFOpenUpTool REMOVE` leave it
  alone.
- `Controls`, `Manual.txt` (the author's manual, in Spanish and English),
  `Licences.txt`, `COPYING.txt`.

## Playing

Run Install-TimmyTime (or copy the TimmyTime drawer where you want it),
then double-click TimmyTime, or start it from a Shell from anywhere: the
game makes its own drawer its current directory while it runs. The keys
are in `Controls`, and Options changes them. The game is in English,
Spanish, Valencian, Galician, Basque, Catalan and Portuguese.

## How the port is made

- The code is upstream's, built against gfopenallegro's Allegro 4 with
  68040 soft float (`amiga/Makefile.amigaos`). The changes are each
  marked `__amigaos__`, except the demo files' reader below.
- Upstream builds its `.dat` files with its own `dat` tool, a macOS or
  Windows program. `amiga/tools/timmydat.py` writes the same Allegro 4
  datafiles with Python, in the tool's order (bitmaps, samples, MIDI,
  palettes, texts, each by name), and checks every index against the
  game's own `src/data/*.h`.
- The maps are written big-endian for the 68040 (`tools/tmx2bin.py
  --big-endian`), since `src/map.c` reads them field by field.
- The demo recordings are the DOS ones: `src/input.c` now reads and writes
  their 4-byte events with the frame time little-endian on any CPU, as
  DOS wrote them.
- The screen is acgame.library's choice of AGA or RTG (`GFX_AUTODETECT`
  for DOS's `GFX_VGA`), and sound asks allegro4.library's own drivers
  instead of probing for Sound Blaster cards.
- Sound and music are silent for now: gfopenallegro plays samples once
  ACGame has audio, and MIDI is not played yet.

## Building

    make -f amiga/Makefile.amigaos PREFIX=<stove>/prefix A4=<gfopenallegro>/allegro4 A4OUT=... ACGOUT=...

or, in Cradle, stove_build with the os32-gcc16-open6 stove and target
package (`package/build-amiga.sh`), which also builds allegro4.library
and acgame.library at the commits `package/package.env` pins, and packs
TimmyTime-VERSION-68040.lha and the GFOpenUp part.

    tests/host/run.sh <gfopenallegro>/allegro4

runs the host tests: every object of every `.dat` loads through
gfopenallegro's reader with the type its header names, the three fonts
grab from their bitmaps, and the big-endian maps match the DOS ones
field for field.

Designed, tested and delivered by The AmiCradle Team.
