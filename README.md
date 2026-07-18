# how to add songs

- must have 64x64 pixel album artwork in graphics directory and .grit file
you can copy an existing one and just rename it.
- put music in /music. hyphens usually break the code its better to not use them.
- edit /source/main.cpp
- add your song to the #include "mynewsong.h"
- add your song to the songs array. newsongTiles, newsongPal then in quotes is what actually shows up in the player text
