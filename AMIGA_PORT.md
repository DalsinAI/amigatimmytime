# Timmy Time for GFOS

Timmy Time for GFOS: AmigaOS 3.2 with GFOpenUp, on a 68040/68060 with FPU, using GFOpenUp's SDL2.module and GFOpenGPU.

Target: Cradle boards / os32-gcc16-open6 stove.

## Source

- Status: source hunt still open (no clear upstream pin yet).
- Prefer free/open 2D title matching the name if found; otherwise mark as blocked.

## Status

Intake advanced. Source pin pending. First stove build still to do.

## Build target

    STOVE=~/AmiCradle/stoves/os32-gcc16-open6

Uses shared OpenUp libraries (LIBS:GFOpenGPU/SDL2.module). Data path PROGDIR:. 68040 fit expected.

## Next

1. Identify and pin upstream source.
2. Adapt for OpenUp SDL2.module.
3. Package and run first Cradle test.

Designed, tested and delivered by The AmiCradle Team.
