/* Timmy Time Adventure for GFOS: host test of the game's data.
 * Every object of every .dat (built by amiga/tools/timmydat.py) loads
 * through gfopenallegro's allegro4 reader by the index in the game's own
 * header, with the type that header names; the three fonts grab from
 * their bitmaps as game.c does.
 * Copyright (c) 2026 AmiCradle Team. GPL-3 or later, as Timmy Time Adventure. */
#include <stdio.h>
#include <string.h>
#include "allegro.h"
#include "data/gdata.h"

static int fails;
#define CHECK(c, ...) do { if (!(c)) { fails++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

static int type_of(const char *comment)
{
    if (!strcmp(comment, "BMP")) return DAT_BITMAP;
    if (!strcmp(comment, "SAMP")) return DAT_SAMPLE;
    if (!strcmp(comment, "MIDI")) return DAT_MIDI;
    if (!strcmp(comment, "PAL")) return DAT_PALETTE;
    if (!strcmp(comment, "DATA")) return DAT_DATA;
    return 0;
}

/* header lines: #define NAME <tab> INDEX <tab> //TYPE */
static int check_dat(const char *dat, const char *header)
{
    char line[256], name[64], comment[16];
    int idx, n = 0;
    FILE *h = fopen(header, "r");
    DATAFILE_INDEX *ix = create_datafile_index(dat);
    CHECK(h != NULL, "%s missing", header);
    CHECK(ix != NULL, "%s: no index", dat);
    if (!h || !ix) return 0;
    while (fgets(line, sizeof line, h)) {
        if (sscanf(line, " #define %63s %d //%15s", name, &idx, comment) != 3) continue;
        DATAFILE *d = load_datafile_object_indexed(ix, idx);
        CHECK(d != NULL, "%s #%d %s did not load", dat, idx, name);
        if (!d) continue;
        CHECK(d->type == type_of(comment), "%s #%d %s: type %08x", dat, idx, name, d->type);
        if (d->type == DAT_BITMAP) {
            BITMAP *b = d->dat;
            CHECK(b && b->w > 0 && b->h > 0 && bitmap_color_depth(b) == 8, "%s %s: bad bitmap", dat, name);
        }
        if (d->type == DAT_SAMPLE) CHECK(((SAMPLE *)d->dat)->len > 0, "%s %s: empty sample", dat, name);
        unload_datafile_object(d);
        n++;
    }
    fclose(h);
    destroy_datafile_index(ix);
    printf("%s: %d objects\n", dat, n);
    return n;
}

int main(int argc, char **argv)
{
    const char *dir = argc > 1 ? argv[1] : ".", *hdr = argc > 2 ? argv[2] : "src/data";
    static const char *dats[][2] = {
        { "game.dat", "gdata.h" }, { "player.dat", "pdata.h" }, { "collmap.dat", "cdata.h" },
        { "objects.dat", "odata.h" }, { "enemies.dat", "edata.h" }, { "jurassic.dat", "judata.h" },
        { "west.dat", "wedata.h" }, { "medieval.dat", "medata.h" }, { "egypt.dat", "egydata.h" },
        { "tutorial.dat", "tutdata.h" },
    };
    char a[512], b[512];
    int i, total = 0;
    CHECK(allegro_init() == 0, "allegro_init");
    for (i = 0; i < (int)(sizeof dats / sizeof dats[0]); i++) {
        snprintf(a, sizeof a, "%s/%s", dir, dats[i][0]);
        snprintf(b, sizeof b, "%s/%s", hdr, dats[i][1]);
        total += check_dat(a, b);
    }
    CHECK(total == 190, "%d objects, want 190", total);

    /* the fonts, as game.c grabs them */
    snprintf(a, sizeof a, "%s/game.dat", dir);
    {
        DATAFILE_INDEX *ix = create_datafile_index(a);
        static const int fonts[] = { FONT_BMP, BIGFONT_BMP, MIDFONT_BMP };
        for (i = 0; ix && i < 3; i++) {
            DATAFILE *d = load_datafile_object_indexed(ix, fonts[i]);
            FONT *f = d ? grab_font_from_bitmap(d->dat) : NULL;
            CHECK(f != NULL, "font %d did not grab", i);
            if (f) {
                CHECK(text_height(f) > 0 && text_length(f, "TIMMY 0123") > 0, "font %d: no glyphs", i);
                CHECK(get_font_range_end(f, 0) - get_font_range_begin(f, 0) >= 58, "font %d: %d glyphs", i,
                      get_font_range_end(f, 0) - get_font_range_begin(f, 0) + 1);
                destroy_font(f);
            }
            if (d) unload_datafile_object(d);
        }
        if (ix) destroy_datafile_index(ix);
    }
    allegro_exit();
    printf(fails ? "test_data: %d FAILED\n" : "test_data: PASS\n", fails);
    return fails != 0;
}
