import json
import os
import sys
import zlib

import chardet

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
}

# Headers for automatic detection
gaiden_headers = [b"\x11\x69\x63\x27\x20\x04\x15\x69\x01\x5F", b"\x11\x69\x63\x27\x20\x04\x15\x69\x02\x40"]
y7_headers = [b"\x28\x76\x4F\x04\x3C\x28\x45\x48\x00\x72", b"\x28\x76\x4F\x04\x3C\x28\x45\x48\x07\x68"]
y7_gog_headers = [b"\x09\x11\x6A\x3A\x54\x43\x71\x6E\x52\x44", b"\x09\x11\x6A\x3A\x54\x43\x71\x6E\x55\x5E"]
yk2_headers = [b"\x28\x76\x4F\x04\x3C\x28\x45\x48\x02\x73", b"\x28\x76\x4F\x04\x3C\x28\x45\x48\x00\x68"]
lj_headers = [b"\x11\x69\x63\x27\x20\x04\x15\x69\x00\x54", b"\x11\x69\x63\x27\x20\x04\x15\x69\x02\x40"]
je_headers = [b"\x34\x52\x46\x2F\x0B\x08\x40\x6A\x5A\x7A", b"\x34\x52\x46\x2F\x0B\x08\x40\x6A\x5D\x62"]
ik_headers = [b"\x72\x75\x45\x77\x21\x72\x57\x4E\x2C\x4D", b"\x60\x75\x45\x77\x22\x72\x57\x4E\x2C\x4D"]
y6_headers = [b"\x2D\x6B\x1D\x04\x07\x22\x41\x51\x7F\x43", b"\x2D\x6B\x1D\x04\x07\x22\x41\x51\x7C\x5F"]


def xor_data(data, key):
    key_len = len(key)
    return bytearray((b ^ ord(key[i % key_len])) for i, b in enumerate(data))


def get_file_encoding(data):
    return chardet.detect(data)['encoding']


def modify_json_binary(data, new_key, new_value):
    # Shamelessly stolen from a ChotDDT
    new_data_str = f', "{new_key}": "{new_value}"'
    new_data_bytes = new_data_str.encode('utf-8')

    # Find the location of the last closing brace in the JSON
    json_end_idx = data.rfind(b'}')

    if json_end_idx == -1:
        print("Error: No JSON object found in the data.")
        return data

    # Insert the new data just before the closing brace
    modified_data = data[:json_end_idx] + new_data_bytes + data[json_end_idx:]

    return modified_data


def crc32_checksum(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def process_file(filename, game, encrypt=False):
    key = game_keys.get(game)
    if not key:
        print(f"Unsupported game: {game}")
        return

    # Adjusted file naming logic
    if encrypt:
        # Remove '.json' extension when encrypting
        if filename.lower().endswith(".json"):
            outname = filename[:-5]
        else:
            outname = filename + ".sav"
    else:
        # Add '.json' extension when decrypting
        outname = filename + ".json"

    try:
        with open(filename, "rb") as in_file:
            data = in_file.read()

        if encrypt:
            checksum = crc32_checksum(data)
            data = xor_data(data, key)
            data += checksum.to_bytes(4, byteorder="little")
        else:
            decrypted_data = xor_data(data[:-4], key)
            # Modify the JSON data within the binary data
            data = modify_json_binary(decrypted_data, 'rggsc_game_identifier', game)

        with open(outname, "wb") as out_file:
            out_file.write(data)

        print(f"Processed {filename} to {outname}")

    except IOError as e:
        print(f"Error processing {filename}: {e}")


def is_game_save(file_path, headers):
    with open(file_path, "rb") as file:
        file_header = file.read(10)  # Assuming headers are 10 bytes
    return any(file_header == header for header in headers)


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py [file] [optional: game number]")
        return

    filename = sys.argv[1]
    extension = os.path.splitext(filename)[1].lower()

    # Try automatic game detection first
    game_abbr = None
    if is_game_save(filename, gaiden_headers):
        game_abbr = "gd"
    elif is_game_save(filename, y7_headers):
        game_abbr = "y7"
    elif is_game_save(filename, y7_gog_headers):
        game_abbr = "y7_gog"
    elif is_game_save(filename, yk2_headers):
        game_abbr = "yk2"
    elif is_game_save(filename, lj_headers):
        game_abbr = "lj"
    elif is_game_save(filename, je_headers):
        game_abbr = "je"
    elif is_game_save(filename, ik_headers):
        game_abbr = "ik"
    elif is_game_save(filename, y6_headers):
        game_abbr = "y6"

    if extension == ".json":
        with open(filename, 'r') as f:
            dict = json.load(f)
        if "rggsc_game_identifier" in dict:
            game_abbr = dict['rggsc_game_identifier']

    # If game is not detected automatically, ask the user to choose
    if not game_abbr:
        print("Select the game:")
        for idx, game_name in enumerate(game_abbr_to_name.values(), start=1):
            print(f"{idx}. {game_name}")

        game_idx = int(input("Enter the game number: ")) - 1
        game_abbr = list(game_abbr_to_name.keys())[game_idx]

    if extension in (".sav", ".sys"):
        process_file(filename, game_abbr)
    elif extension == ".json":
        process_file(filename, game_abbr, encrypt=True)
    else:
        print(f"Skipping {filename}: Unsupported file type.")


if __name__ == "__main__":
    main()
