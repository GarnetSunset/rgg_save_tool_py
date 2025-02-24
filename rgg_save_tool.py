import argparse
import json
import os
import sys
import zlib

import msgpack

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
    "v5b": "STarYZgr3DL11",
    "yp": "STarYZgr3DL11",
}

# Mapping of human-readable game names to their key abbreviations
game_names = {
    "ik": "Like a Dragon: Ishin (ik)",
    "je": "Judgment (je)",
    "lj": "Lost Judgment (lj)",
    "gd": "Like a Dragon: Gaiden (gd)",
    "y6": "Yakuza 6 (y6)",
    "y7": "Yakuza 7 (y7)",
    "y7_gog": "Yakuza 7 GoG (y7_gog)",
    "yk2": "Yakuza Kiwami 2 (yk2)",
    "y8": "Like a Dragon: Infinite Wealth (y8)",
    "v5b": "Virtua Fighter 5 Open Beta (v5b)",
    "yp": "Like a Dragon: Pirate Yakuza In Hawaii (yp)",
}

# List of games that natively use msgpack encryption format
msgpack_games = ["yp"]

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
    "v5b": [
        b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x02\x68",
    ],
    "yp": [
        b"\x8D\x54\x46\xD6\x77\x2C\x02\x00\x70\xE1",
        b"\xDB\xF0\x4F\x04\x3C\x28\x6F\xD7\x5A\x2A",
    ],
}


def xor_data(data, key):
    key_len = len(key)
    return bytearray((b ^ ord(key[i % key_len])) for i, b in enumerate(data))


def calculate_checksum_y6(data):
    seed = 0x79BAA6BB6398B6F7
    checksum = 0
    add = 0
    sz_result = 0

    sz = len(data)
    if sz < 0x15B0:
        pass
    else:
        sz_result = sz
        result64 = seed
        excess64 = (result64 * sz) >> 64
        sz_result -= excess64
        sz_result = ((sz_result >> 1) + excess64) >> 12
        sz -= sz_result * 0x15B0

        for s in range(sz_result):
            read = s * 0x15B0
            for i in range(0x15B0):
                add += data[i + read]
                checksum += add

    read = sz_result * 0x15B0
    if sz >= 0x10:
        result64 = sz >> 4
        result64 *= 0x10
        sz -= result64
        for i in range(result64):
            add += data[i + read]
            checksum += add
        read += result64

    for i in range(sz):
        add += data[i + read]
        checksum += add

    result32 = 0x80078071
    excess32 = ((result32 * add) >> 32) >> 15
    add -= excess32 * 0xFFF1

    result32 = 0x80078071
    excess32 = ((result32 * checksum) >> 32) >> 15
    checksum -= excess32 * 0xFFF1

    checksum = (checksum << 16) | add
    return checksum


def crc32_checksum(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def encrypt_data(game, data):
    key = game_keys.get(game)
    if not key:
        print(f"Unsupported game: {game}")
        sys.exit(1)

    if game == "ik":
        encoded_data = xor_data(data[:-16], key)
        encoded_data += data[-16:]
        checksum = crc32_checksum(data[:-16])
        encoded_data[-8:-4] = checksum.to_bytes(4, byteorder="little")
        return encoded_data
    elif game == "y6":
        encoded_data = xor_data(data, key)
        checksum = calculate_checksum_y6(data)
        encoded_data += checksum.to_bytes(4, byteorder="little")
        return encoded_data
    else:
        encoded_data = xor_data(data, key)
        encoded_data += crc32_checksum(data).to_bytes(4, byteorder="little")
        return encoded_data


def decrypt_data(game, data):
    key = game_keys.get(game)
    if not key:
        print(f"Unsupported game: {game}")
        sys.exit(1)
    if game == "ik":
        decoded_data = xor_data(data[:-16], key)
        return decoded_data + data[-16:]
    else:
        return xor_data(data[:-4], key)


def convert_bytes(obj):
    if isinstance(obj, bytes):
        return obj.hex()
    elif isinstance(obj, dict):
        return {k: convert_bytes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_bytes(v) for v in obj]
    return obj


def encrypt_msgpack(game, json_obj):
    key = game_keys.get(game)
    if not key:
        print(f"Unsupported game: {game}")
        sys.exit(1)
    packed = msgpack.packb(json_obj, use_bin_type=True)
    encrypted = bytes(packed[i] ^ ord(key[i % len(key)]) for i in range(len(packed)))
    checksum = crc32_checksum(packed)
    return encrypted + checksum.to_bytes(4, byteorder="little")


def decrypt_msgpack(game, data):
    key = game_keys.get(game)
    if not key:
        print(f"Unsupported game: {game}")
        sys.exit(1)
    decrypted = bytes(data[i] ^ ord(key[i % len(key)]) for i in range(len(data) - 4))
    try:
        unpacked = msgpack.unpackb(decrypted, raw=False)
        unpacked = convert_bytes(unpacked)
        return json.dumps(unpacked, indent=4, ensure_ascii=False).encode("utf-8")
    except Exception as e:
        print("Error unpacking msgpack data:", e)
        return decrypted


def process_file(
    input_file,
    game,
    output_file=None,
    ishin_to_steam=None,
    ishin_to_gamepass=None,
    force_msgpack=False,
):
    base, ext = os.path.splitext(input_file)
    encrypt_flag = ext == ".json"
    decrypt_flag = ext in (".sav", ".sys")

    if not encrypt_flag and not decrypt_flag:
        print(f"Unsupported file type for {input_file}.")
        sys.exit(1)

    if output_file is None:
        if encrypt_flag:
            output_file = f"{base.split('_')[0]}.sav"
        else:
            output_file = f"{base}_{game}.json"

    try:
        with open(input_file, "rb") as f:
            data = bytearray(f.read())

        # If force_msgpack is enabled or the game is natively msgpack-based, use msgpack functions.
        if force_msgpack or (game in msgpack_games):
            if encrypt_flag:
                text = data.decode("utf-8")
                json_obj = json.loads(text)
                data = encrypt_msgpack(game, json_obj)
            elif decrypt_flag:
                data = decrypt_msgpack(game, data)
        # Ishin-specific platform conversion
        elif game == "ik" and (ishin_to_steam or ishin_to_gamepass):
            if ishin_to_steam == ishin_to_gamepass:
                print(
                    "Error: Only one of --ishin-to-steam or --ishin-to-gamepass may be specified."
                )
                sys.exit(1)
            save_from = "Steam" if ishin_to_gamepass else "Game Pass"
            save_to = "Game Pass" if ishin_to_gamepass else "Steam"
            print(f"Converting Ishin save from {save_from} to {save_to}.")
            data[-12] = 0x21 if ishin_to_steam else 0x8F
        elif encrypt_flag:
            data = encrypt_data(game, data)
        elif decrypt_flag:
            data = decrypt_data(game, data)

        with open(output_file, "wb") as f:
            f.write(data)

        print(f"Processed '{input_file}' to '{output_file}'")
    except IOError as e:
        print(f"Error processing '{input_file}': {e.strerror}")
        sys.exit(1)


def identify_game_from_save(filename):
    try:
        with open(filename, "rb") as file:
            file_header = file.read(10)
        for game, headers in game_headers.items():
            if any(file_header.startswith(header) for header in headers):
                print(f"Detected game based on file header: {game_names[game]}")
                return game
        return None
    except IOError as e:
        print(f"Error processing '{filename}': {e.strerror}")
        sys.exit(1)


def find_game_abbreviation(filename, abbr_arg=None):
    game_abbr = None if abbr_arg not in game_names else abbr_arg
    if not game_abbr:
        for abbr in game_names:
            if f"_{abbr}." in filename:
                game_abbr = abbr
                break
    if not game_abbr:
        game_abbr = identify_game_from_save(filename)
    if not game_abbr:
        print("Failed to detect game. Please specify a game abbreviation.")
        sys.exit(1)
    return game_abbr


def main():
    parser = argparse.ArgumentParser(
        description="""Process RGG game save files.
        Encrypts .json to .sav or .sys and decrypts .sav or .sys to .json.
        Converts Ishin (ik) saves between Steam and Game Pass if specified.
        For msgpack-based games (e.g. Pirate Yakuza), decrypting outputs human-readable JSON.
        Use --msgpack to force msgpack mode.""",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    print(f"Current working directory: {os.getcwd()}")
    parser.add_argument("input_file", help="The file to process")
    parser.add_argument(
        "output_file", help="(optional) The file to save to", nargs="?", default=None
    )

    parser.add_argument(
        "--ishin-to-steam", help="Convert Ishin saves to Steam", action="store_true"
    )
    parser.add_argument(
        "--ishin-to-gamepass",
        help="Convert Ishin saves to Game Pass",
        action="store_true",
    )
    parser.add_argument(
        "--msgpack",
        help="Force msgpack mode for encryption/decryption",
        action="store_true",
    )

    game_list = "\n".join([f"{k}: {v}" for k, v in game_names.items()])
    parser.add_argument(
        "-g",
        dest="game",
        help=f"(Optional) The game abbreviation\n\nChoices:\n{game_list}",
        choices=game_names,
    )

    args = parser.parse_args()
    game = find_game_abbreviation(args.input_file, args.game)
    process_file(
        args.input_file,
        game,
        args.output_file,
        args.ishin_to_steam,
        args.ishin_to_gamepass,
        args.msgpack,
    )


if __name__ == "__main__":
    main()
