/* Timmy Time Adventure for GFOS: start-up bits.
 * The game opens its files by bare names (game.dat, jurassic.bin, ...), so
 * the game's drawer (PROGDIR:) is the current directory while it runs, and
 * the Shell's comes back at exit. TIMMY.CFG goes in the User drawer.
 * Copyright (c) 2026 AmiCradle Team. GPL-3 or later, as Timmy Time Adventure. */
#include <stdlib.h>
#include <sys/stat.h>
#include <proto/dos.h>

unsigned long __stack = 256 * 1024;
static const char amiga_ver[] __attribute__((used)) =
  "$VER: TimmyTime 1.9 (16.11.2026)";

static BPTR progdir_lock, old_dir;
static int dir_changed;

static void amiga_restore_dir(void)
{
    if (dir_changed) {
        CurrentDir(old_dir);
        UnLock(progdir_lock);
        dir_changed = 0;
    }
}

static void __attribute__((constructor)) amiga_enter_progdir(void)
{
    progdir_lock = Lock((CONST_STRPTR)"PROGDIR:", ACCESS_READ);
    if (progdir_lock) {
        old_dir = CurrentDir(progdir_lock);
        dir_changed = 1;
        atexit(amiga_restore_dir);
    }
    mkdir("User", 0755);
}
