# rgg_save_tool_py

A tool for encrypting and decrypting RGG studios game saves on PC.

## Download (For non-technical people)

To download an executable, that is to say a program you can run and use right now: [Download here!](https://github.com/GarnetSunset/rgg_save_tool_py/releases)

## Usage

``
python rgg_save_tool.py <input_file> [output_file] [-g <game_abbr>] [--ishin-to-steam | --ishin-to-gamepass]
``

### Arguments:

``input_file``: The path to the save file you want to process.

``output_file`` (optional): The path to save the processed file.

``-g <game_abbr>``: Specify the game abbreviation manually. Supported options:

```
ik: Like a Dragon: Ishin
je: Judgment
lj: Lost Judgment
gd: Like a Dragon: Gaiden
y6: Yakuza 6
y7: Yakuza 7
y7_gog: Yakuza 7 GoG
yk2: Yakuza Kiwami 2
y8: Like a Dragon: Infinite Wealth
v5b: Virtua Fighter 5 Open Beta
```

``--ishin-to-steam``: Converts an Ishin save from Game Pass to Steam.

``--ishin-to-gamepass``: Converts an Ishin save from Steam to Game Pass.

## Credits

Original Tool by [@SutandoTsukai181](https://github.com/SutandoTsukai181/yk2_save)

Original decryption code from [here](https://gist.github.com/simontime/59661a189b20fc3517b20d8c9f329017) by [@simontime](https://github.com/simontime). I
added proper checksum calculation and automatic game detection to the code, and converted it to python.

- Yakuza 6 Key discovered by @jason098
- Judgment Key discovered by [@Ret-HZ](https://github.com/Ret-HZ)
- Lost Judgment Key discovered by @jason098
- Ishin Key discovered by [@Ret-HZ](https://github.com/Ret-HZ)
- Ishin platform format conversion code, and Unit tests by [@jeottesen](https://github.com/jeottesen)
- YLAD GOG Key discovered by [@Timo654](https://github.com/Timo654)
- Yakuza Kiwami 2 Key discovered by [@simontime](https://github.com/simontime)
- Like a Dragon: Infinite Wealth Key discovered by [Committee of Nerds](https://www.youtube.com/watch?v=CjN4aUI-RJM)

## Finding save keys

In Ghidra

- Search for a function called: "GetFileTime", and scroll up on each xref, find a string in that function. If not find
  the next.
- Find strings for: "%s/%s/save%03d_icon0.dds" and scroll up on each xref, to find "GetFileTime" and search for a
  string.
