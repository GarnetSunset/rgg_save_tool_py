import chardet
import json
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
gaiden_headers = [
    b"\x11\x69\x63\x27\x20\x04\x15\x69\x01\x5f",
    b"\x11\x69\x63\x27\x20\x04\x15\x69\x02\x40",
]
ik_headers = [
    b"\x72\x75\x45\x77\x21\x72\x57\x4e\x2c\x4d",
    b"\x60\x75\x45\x77\x22\x72\x57\x4e\x2c\x4d",
]
je_headers = [
    b"\x34\x52\x46\x2f\x0b\x08\x40\x6a\x5a\x7a",
    b"\x34\x52\x46\x2f\x0b\x08\x40\x6a\x5d\x62",
]
lj_headers = [
    b"\x11\x69\x63\x27\x20\x04\x15\x69\x00\x54",
    b"\x11\x69\x63\x27\x20\x04\x15\x69\x02\x40",
]
y6_headers = [
    b"\x2d\x6b\x1d\x04\x07\x22\x41\x51\x7f\x43",
    b"\x2d\x6b\x1d\x04\x07\x22\x41\x51\x7c\x5f",
]
y7_headers = [
    b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x00\x72",
    b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x07\x68",
]
y7_gog_headers = [
    b"\x09\x11\x6a\x3a\x54\x43\x71\x6e\x52\x44",
    b"\x09\x11\x6a\x3a\x54\x43\x71\x6e\x55\x5e",
]
yk2_headers = [
    b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x02\x73",
    b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x00\x68",
]
y8_headers = [
    b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x06\x73",
    b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x05\x68",
]


def xor_data(data, key):
    key_len = len(key)
    return bytearray((b ^ ord(key[i % key_len])) for i, b in enumerate(data))


def get_file_encoding(data):
    detected = chardet.detect(data)
    return detected["encoding"] if detected["encoding"] else "utf-8"


def modify_json_binary(data, modifications):
    try:
        detected = chardet.detect(data)
        encoding = detected["encoding"] if detected["encoding"] else "utf-8"
        data_str = data.decode(encoding, errors="ignore")

        if not data_str.strip().startswith(("{", "[")):
            raise ValueError("Decoded data does not appear to be valid JSON")

        data_json = json.loads(data_str)

        for key_path, value in modifications.items():
            keys = key_path.split(".")
            temp = data_json
            for key in keys[:-1]:
                temp = temp.setdefault(key, {})
            temp[keys[-1]] = value

        modified_str = json.dumps(data_json, ensure_ascii=False)
        return modified_str.encode(encoding)
    except json.JSONDecodeError as e:
        print(f"Error processing JSON data: {e}")
        return data


def crc32_checksum(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def read_game_version_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data["base"]["m_version"]


def process_file(filename, game, example_save_file=None, encrypt=False):
    modifications = {}
    if example_save_file and not encrypt:
        # If there's an example save file and we're decrypting, read the version from it
        target_version = read_game_version_from_file(example_save_file)
        modifications["base.m_version"] = (
            target_version  # Specify the nested path for the modification
        )
        print("Got example.")

    key = game_keys.get(game)
    if not key:
        print(f"Unsupported game: {game}")
        return

    try:
        with open(filename, "rb") as in_file:
            data = in_file.read()

        if encrypt:
            # Decrypt the data first if it's already in an encrypted state
            if game in [
                "ik",
                "ishin",
            ]:  # Special handling for specific games, if needed
                data = xor_data(
                    data[:-8], key
                )  # Adjust if your game's logic is different
            else:
                data = xor_data(
                    data[:-4], key
                )  # Standard decryption, removing checksum

            # Convert decrypted data to JSON and modify
            if modifications:
                data = modify_json_binary(data, modifications)

            # Re-encrypt the modified data
            data = xor_data(data, key)
            # Append the checksum back to the data
            checksum = crc32_checksum(data)
            data += checksum.to_bytes(4, byteorder="little")

        else:
            # Standard decryption logic
            data = xor_data(data[:-4], key)  # Adjust according to your game's specifics

            # If we need to modify the JSON after decryption
            if modifications:
                data = modify_json_binary(data, modifications)

        # Determine the output filename based on whether we're encrypting or decrypting
        outname = filename + (".json" if not encrypt else ".sav")

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
    game_abbr = sys.argv[2] if len(sys.argv) > 2 else None
    if game_abbr and game_abbr in game_abbr_to_name:
        print(f"Game selected: {game_abbr_to_name[game_abbr]}")
    else:
        if is_game_save(filename, gaiden_headers):
            game_abbr = "gd"
        elif is_game_save(filename, y7_headers):
            game_abbr = "y7"
        elif is_game_save(filename, y7_gog_headers):
            game_abbr = "y7_gog"
        elif is_game_save(filename, y8_headers):
            game_abbr = "y8"
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

    example_save_file = sys.argv[3] if len(sys.argv) > 3 else None

    # If game_abbr is None or not a valid key, ask the user to enter the game manually
    if not game_abbr or game_abbr not in game_abbr_to_name:
        print("Game not detected automatically or invalid game abbreviation provided.")
        print("Select the game:")
        for idx, game_name in enumerate(game_abbr_to_name.values(), start=1):
            print(f"{idx}. {game_name}")

        try:
            game_idx = int(input("Enter the game number: ")) - 1
            if game_idx < 0 or game_idx >= len(game_abbr_to_name):
                print("Invalid selection. Exiting.")
                return
            game_abbr = list(game_abbr_to_name.keys())[game_idx]
        except ValueError:
            print("Invalid input. Exiting.")
            return
    else:
        print(f"Game is: {game_abbr_to_name[game_abbr]}")

    if extension == ".json" and game_abbr != "ik" and game_abbr:
        with open(filename, "r", encoding="utf-8") as f:
            dict = json.load(f)
        if "rggsc_game_identifier" in dict:
            game_abbr = dict["rggsc_game_identifier"]

    # If game is not detected automatically, ask the user to choose
    if not game_abbr:
        print("Select the game:")
        for idx, game_name in enumerate(game_abbr_to_name.values(), start=1):
            print(f"{idx}. {game_name}")

        game_idx = int(input("Enter the game number: ")) - 1
        game_abbr = list(game_abbr_to_name.keys())[game_idx]

    if extension in (".sav", ".sys"):
        process_file(filename, game_abbr, example_save_file)
    elif extension == ".json":
        process_file(filename, game_abbr, example_save_file, encrypt=True)
    else:
        print(f"Skipping {filename}: Unsupported file type.")


if __name__ == "__main__":
    main()
