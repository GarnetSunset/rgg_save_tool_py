import argparse
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
    "v5b": "STarYZgr3DL11",
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
    "y8": "Like a Dragon: Infinite Wealth (y8)",
    "v5b": "Virtua Fighter 5 Open Beta (v5b)",
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
    "v5b": [
        b"\x28\x76\x4f\x04\x3c\x28\x45\x48\x02\x68",
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
        sys.exit(1)

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


def process_file(input_file, game, output_file=None, to_steam=None, to_gamepass=None):
    """
    Processes the input file: encrypt, decrypt, or convert Ishin saves.
    - Encrypts/decrypts based on file extension (.json -> .sav/sys and vice versa).
    - Converts Ishin saves if `to_steam` or `to_gamepass` is specified.
    """
    base, ext = os.path.splitext(input_file)

    # Determine operation (encrypt/decrypt) based on file extension
    encrypt = ext == ".json"
    decrypt = ext in (".sav", ".sys")

    if not encrypt and not decrypt:
        print(f"Unsupported file type for {input_file}.")
        exit(1)

    # Set default output file name
    if output_file is None:
        if encrypt:
            output_file = f"{base.split('_')[0]}.sav"
        else:
            output_file = f"{base}_{game}.json"

    try:
        # Read input file
        with open(input_file, "rb") as f:
            data = bytearray(f.read())

        # Ishin-specific platform conversion
        if game == "ik" and (to_steam or to_gamepass):
            if to_steam == to_gamepass:  # Ensure exactly one conversion option
                print(
                    "Error: Only one of --to-steam or --to-gamepass may be specified."
                )
                exit(1)

            save_from = "Steam" if to_gamepass else "Game Pass"
            save_to = "Game Pass" if to_gamepass else "Steam"
            print(f"Converting Ishin save from {save_from} to {save_to}.")

            # Modify the 12th byte from the end for platform conversion
            data[-12] = 0x21 if to_steam else 0x8F

        # Encrypt or decrypt data if no conversion occurred
        elif encrypt:
            data = encrypt_data(game, data)
        elif decrypt:
            data = decrypt_data(game, data)

        # Write output file
        with open(output_file, "wb") as f:
            f.write(data)

        print(f"Processed '{input_file}' to '{output_file}'")

    except IOError as e:
        print(f"Error processing '{input_file}': {e.strerror}")
        exit(1)


def identify_game_from_save(filename):
    try:
        with open(filename, "rb") as file:
            file_header = file.read(10)  # Read first 10 bytes
        for game, headers in game_headers.items():
            if any(file_header.startswith(header) for header in headers):
                game_name = game_names[game]
                print(f"Detected game based on file header: {game_name}")
                return game
        # If no match found, return None
        return None
    except IOError as e:
        print(f"Error processing '{filename}': {e.strerror}")
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
    parser = argparse.ArgumentParser(
        description="""Process RGG game save files.
        Encrypts .json to .sav or .sys and decrypts .sav or .sys to .json.
        Converts Ishin (ik) saves between Steam and Game Pass if specified.""",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    print(f"Current working directory: {os.getcwd()}")
    parser.add_argument("input_file", help="The file to process")
    parser.add_argument(
        "output_file", help="(optional) The file to save to", nargs="?", default=None
    )

    parser.add_argument(
        "--to-steam", help="Convert Ishin saves to Steam", action="store_true"
    )
    parser.add_argument(
        "--to-gamepass", help="Convert Ishin saves to Game Pass", action="store_true"
    )

    # Game abbreviation argument
    game_list = "\n".join([f"{k}: {v}" for k, v in game_names.items()])
    parser.add_argument(
        "-g",
        dest="game",
        help=f"(Optional) The game abbreviation\n\nChoices:\n{game_list}",
        choices=game_names,
    )

    args = parser.parse_args()

    # Determine game abbreviation
    game = find_game_abbreviation(args.input_file, args.game)

    # Process the file (encrypt, decrypt, or convert)
    process_file(
        args.input_file, game, args.output_file, args.to_steam, args.to_gamepass
    )


if __name__ == "__main__":
    main()
