import os
import sys
import zlib

# Dictionary of keys for different games
game_keys = {
    "ik": "fuEw5rWN8MBS",
    "je": "OphYnzbPoV5lj",
    "lj": "jKMQEv7S4l9hd",
    "gd": "jKMQEv7S4l9hd",
    "y6": "VI3rbPckNsea7JOUMrgT",
    "y7": "STarYZgr3DL11",
    "y7_gog": "r3DL11STarYZg",
    "yk2": "STarYZgr3DL11",
    "y8": "STarYZgr3DL11",
}

# Mapping of human-readable game names to their key abbreviations
game_abbr_to_name = {
    "ik": "Like a Dragon: Ishin (ik)",  # Ret-HZ asked for this
    "je": "Judgment (je)",
    "lj": "Lost Judgment (lj)",
    "gd": "Like a Dragon: Gaiden (gd)",
    "y6": "Yakuza 6 (y6)",
    "y7": "Yakuza 7 (y7)",
    "y7_gog": "Yakuza 7 GoG (y7_gog)",
    "yk2": "Yakuza Kiwami 2 (yk2)",
    "y8": "Like a Dragon: Infinite Wealth",
}

# Headers for automatic detection
game_headers = {
    "gd": [
        b"\x11\x69\x63\x27\x20\x04\x15\x69\x01\x5f",
        b"\x11\x69\x63\x27\x20\x04\x15\x69\x02\x40",
    ],
    "ik": [
        b"\x72\x75\x45\x77\x21\x72\x57\x4e\x2c\x4d",
        b"\x60\x75\x45\x77\x22\x72\x57\x4e\x2c\x4d",
    ],
    "je": [
        b"\x34\x52\x46\x2f\x0b\x08\x40\x6a\x5a\x7a",
        b"\x34\x52\x46\x2f\x0b\x08\x40\x6a\x5d\x62",
    ],
    "lj": [
        b"\x11\x69\x63\x27\x20\x04\x15\x69\x00\x54",
        b"\x11\x69\x63\x27\x20\x04\x15\x69\x02\x40",
    ],
    "y6": [
        b"\x2d\x6b\x1d\x04\x07\x22\x41\x51\x7f\x43",
        b"\x2d\x6b\x1d\x04\x07\x22\x41\x51\x7c\x5f",
    ],
    "y7": [
        b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x00\x72",
        b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x07\x68",
    ],
    "y7_gog": [
        b"\x09\x11\x6a\x3a\x54\x43\x71\x6e\x52\x44",
        b"\x09\x11\x6a\x3a\x54\x43\x71\x6e\x55\x5e",
    ],
    "yk2": [
        b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x02\x73",
        b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x00\x68",
    ],
    "y8": [
        b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x06\x73",
        b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x05\x68",
    ],
}


def xor_data(data, key):
    key_len = len(key)
    return bytearray((b ^ ord(key[i % key_len])) for i, b in enumerate(data))


def crc32_checksum(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def process_file(filename, game, encrypt=False):
    key = game_keys.get(game)
    if not key:
        print(f"Unsupported game: {game}")
        return

    base, ext = os.path.splitext(filename)
    if encrypt:
        outname = f"{base.split('_')[0]}.sav"  # Restore to original .sav name
    else:
        outname = f"{base}_{game}.json"  # Append game abbreviation for JSON

    try:
        with open(filename, "rb") as in_file:
            data = in_file.read()

        if encrypt:
            data = xor_data(data, key) + crc32_checksum(data).to_bytes(
                4, byteorder="little"
            )
        else:
            data = xor_data(
                data[:-4], key
            )  # Remove checksum assumed to be last 4 bytes

        with open(outname, "wb") as out_file:
            out_file.write(data)

        print(f"Processed {filename} to {outname}")

    except IOError as e:
        print(f"Error processing {filename}: {e}")


def is_game_save(file_path, game):
    try:
        with open(file_path, "rb") as file:
            file_header = file.read(10)  # Read first 10 bytes
        return any(file_header.startswith(header) for header in game_headers[game])
    except KeyError:
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py [file] [optional: game abbreviation]")
        return

    filename = sys.argv[1]
    extension = os.path.splitext(filename)[1].lower()

    # Attempt to detect game from filename
    game_abbr = None
    for key in game_keys:
        if f"_{key}." in filename:
            game_abbr = key
            break

    # If not found in filename, try detecting from file header
    if not game_abbr:
        for game, headers in game_headers.items():
            if is_game_save(filename, game):
                game_abbr = game
                print(f"Detected game based on file header: {game_abbr_to_name[game]}")
                break

    if not game_abbr:
        print("Failed to detect game automatically. Please specify game abbreviation.")
        return

    if extension == ".json":
        process_file(filename, game_abbr, encrypt=True)
    elif extension in (".sav", ".sys"):
        process_file(filename, game_abbr)
    else:
        print(f"Unsupported file type for {filename}.")


if __name__ == "__main__":
    main()
