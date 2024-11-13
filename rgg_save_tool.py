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
game_names = {
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
        # conflicts with second gd header
        # b"\x11\x69\x63\x27\x20\x04\x15\x69\x02\x40",
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


def encrypt_data(game, data):
    key = game_keys.get(game)
    if not key:
        print(f"Unsupported game: {game}")
        exit(1)

    # Special handling for Ishin
    if game == "ik":
        # Exclude checksum and unknown data
        encoded_data = xor_data(data[:-16], key)
        # Append checksum and unknown data
        encoded_data += data[-16:]
        checksum = crc32_checksum(data[:-16])
        # Update the checksum
        encoded_data[-8:-4] = checksum.to_bytes(4, byteorder="little")
        return encoded_data
    else:
        encoded_data = xor_data(data, key)
        encoded_data += crc32_checksum(data).to_bytes(4, byteorder="little")
        return encoded_data


def decrypt_data(game, data):
    key = game_keys.get(game)
    if not key:
        print(f"Unsupported game: {game}")
        exit(1)

    # Special handling for Ishin
    if game == "ik":
        # Remove checksum and unknown data before decoding
        decoded_data = xor_data(data[:-16], key)
        # Append checksum and unknown data
        return decoded_data + data[-16:]
    else:
        # Remove checksum assumed to be last 4 bytes
        return xor_data(data[:-4], key)


def process_file(filename, game, encrypt=False):
    base, _ = os.path.splitext(filename)
    if encrypt:
        outname = f"{base.split('_')[0]}.sav"  # Restore to original .sav name
    else:
        outname = f"{base}_{game}.json"  # Append game abbreviation for JSON

    try:
        with open(filename, "rb") as in_file:
            data = in_file.read()

        if encrypt:
            data = encrypt_data(game, data)
        else:
            data = decrypt_data(game, data)

        with open(outname, "wb") as out_file:
            out_file.write(data)

        print(f"Processed {filename} to {outname}")

    except IOError as e:
        print(f"Error processing {filename}: {e.strerror}")
        exit(1)


def identify_game_from_save(filename):
    try:
        with open(filename, "rb") as file:
            file_header = file.read(10)  # Read first 10 bytes
        for game, headers in game_headers.items():
            if any(file_header.startswith(header) for header in headers):
                print(f"Detected game based on file header: {game_names[game]}")
                return game
        # If no match found, return None
        return None
    except IOError as e:
        print(f"Error processing {filename}: {e.strerror}")
        exit(1)


def find_game_abbreviation(filename, abbr_arg=None):
    # Attempt to get game from command line argument
    game_abbr = None if abbr_arg not in game_names else abbr_arg

    # Attempt to detect game from filename
    if not game_abbr:
        for abbr in game_names:
            if f"_{abbr}." in filename:
                game_abbr = abbr
                break

    # If not found in filename, try detecting from file header
    if not game_abbr:
        game_abbr = identify_game_from_save(filename)

    if not game_abbr:
        print("Failed to detect game. Please specify a game abbreviation.")
        exit(1)
    return game_abbr


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py [file] [optional: game abbreviation]")
        print("\ngame abbreviations:")
        for game, name in game_names.items():
            print(f"{game}: {name}")
        return

    filename = sys.argv[1]
    extension = os.path.splitext(filename)[1].lower()

    abbr_arg = sys.argv[2] if len(sys.argv) > 2 else None
    game_abbr = find_game_abbreviation(filename, abbr_arg)

    if extension == ".json":
        process_file(filename, game_abbr, encrypt=True)
    elif extension in (".sav", ".sys"):
        process_file(filename, game_abbr)
    else:
        print(f"Unsupported file type for {filename}.")
        exit(1)


if __name__ == "__main__":
    main()
