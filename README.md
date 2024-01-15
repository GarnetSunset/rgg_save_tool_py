# rgg_save_tool_py

A tool for encrypting and decrypting RGG studios game saves.

Original Tool by [@SutandoTsukai181](https://github.com/SutandoTsukai181/yk2_save)

Original decryption code from [here](https://gist.github.com/simontime/59661a189b20fc3517b20d8c9f329017) by simontime. I
added proper checksum calculation and automatic game detection to the code, and converted it to python.

- Yakuza 6 Key discovered by @jason098
- Judgment Key discovered by [@Ret-HZ](https://github.com/Ret-HZ)
- Lost Judgment Key discovered by @jason098
- Ishin Key discovered by [@Ret-HZ](https://github.com/Ret-HZ)
- YLAD GOG Key discovered by [@Timo654](https://github.com/Timo654)
- Yakuza Kiwami 2 Key discovered by [@simontime](https://github.com/simontime)

## Finding save keys

In Ghidra

- Search for a function called: "GetFileTime", and scroll up on each xref, find a string in that function. If not find
  the next.
- Find strings for: "%s/%s/save%03d_icon0.dds" and scroll up on each xref, to find "GetFileTime" and search for a
  string. 