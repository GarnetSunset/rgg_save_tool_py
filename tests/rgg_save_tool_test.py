import os
import unittest
import zlib
from unittest.mock import mock_open, patch

from rgg_save_tool import (
    crc32_checksum,
    decrypt_data,
    encrypt_data,
    find_game_abbreviation,
    game_headers,
    game_keys,
    identify_game_from_save,
    main,
    process_file,
    xor_data,
)


class RGGSaveToolTests(unittest.TestCase):
    def test_xor_data_uses_key_correcly(self):
        data = "mudamudamuda".encode("utf-8")
        key = "muda"
        expected_output = bytes.fromhex("000000000000000000000000")
        self.assertEqual(xor_data(data, key), expected_output)

    @patch("zlib.crc32", return_value=-123456)
    def test_checksum_value_is_unsigned(self, mock_crc32):
        checksum = crc32_checksum(b"test data")
        # Ensure the checksum is converted to be unsigned
        self.assertEqual(checksum, 4294843840)

    encrypted_file = "saves/test.sav"
    decrypted_file = "saves/test_ik_ik.json"

    @patch("sys.argv", ["rgg_save_tool.py", "saves/test_ik.json"])
    def test_encrypt_end_to_end(self):
        main()  # Encrypt the decrypted file
        self.assertTrue(os.path.exists(self.encrypted_file))

        # Check the checksum of the encrypted file
        with open(self.encrypted_file, "rb") as in_file:
            data = in_file.read()
        self.assertEqual(zlib.crc32(data), 349881174)

    @patch("sys.argv", ["rgg_save_tool.py", "saves/test_ik.sav"])
    def test_decrypt_end_to_end(self):
        main()  # Decrypt the decrypted file
        self.assertTrue(os.path.exists(self.decrypted_file))

        with open(self.decrypted_file, "rb") as in_file:
            data = in_file.read()
        self.assertEqual(zlib.crc32(data), 1644199928)

    converted_file = "test_converted.sav"

    # Test save is from steam.
    @patch(
        "sys.argv",
        [
            "rgg_save_tool.py",
            "saves/test_ik.sav",
            converted_file,
            "-g",
            "ik",
            "--to-gamepass",
        ],
    )
    def test_ik_to_gamepass_end_to_end(self):
        main()  # Decrypt the decrypted file
        self.assertTrue(os.path.exists(self.converted_file))

        with open(self.converted_file, "rb") as in_file:
            data = in_file.read()
        self.assertEqual(zlib.crc32(data), 2233312336)

    # Clean up any remaining files after all tests have run, pass or fail
    @classmethod
    def tearDownClass(self):
        if os.path.exists(self.encrypted_file):
            os.remove(self.encrypted_file)
        if os.path.exists(self.decrypted_file):
            os.remove(self.decrypted_file)
        if os.path.exists(self.converted_file):
            os.remove(self.converted_file)


class TestEncryptData(unittest.TestCase):
    def test_ik_game(self):
        unencrypted_data = bytes.fromhex("00000000000000000000000000000000")

        # expected_data and last_bytes from the last 32 bytes of test_ik.sav
        expected_data = bytes.fromhex("667545773572574e384d425366754577")
        last_bytes = bytearray(bytes.fromhex("ff3902fc210000004bc4f9afff000000"))
        # update crc32 checksum in last_bytes
        last_bytes[-8:-4] = crc32_checksum(unencrypted_data).to_bytes(4, "little")

        encrypted_data = encrypt_data("ik", unencrypted_data + last_bytes)
        self.assertEqual(encrypted_data[:-16], expected_data)
        # Check last 16 bytes for updated checksum and unknown data
        self.assertEqual(encrypted_data[-16:], last_bytes)

    def test_other_games(self):
        for game in game_keys.keys():
            # Skip "ik" as it has special handling
            if game != "ik":
                data = b"testdata"
                checksum = crc32_checksum(data)
                encrypted_data = encrypt_data(game, data)
                # Check if checksum is correct
                self.assertEqual(
                    int.from_bytes(encrypted_data[-4:], "little"), checksum
                )

    def test_unsupported_game(self):
        with self.assertRaises(SystemExit) as cm:
            encrypt_data("unsupported_game", b"testdata")
        self.assertEqual(cm.exception.code, 1)


class TestDecryptData(unittest.TestCase):
    def test_ik_game(self):
        encrypted_data = bytes.fromhex("667545773572574e384d425366754577")

        # expected_data and last_bytes from the last 32 bytes of test_ik.json
        expected_data = bytes.fromhex("00000000000000000000000000000000")
        last_bytes = bytes.fromhex("ff3902fc210000004bc4f9afff000000")
        # checksum is not changed in decryption

        decrypted_data = decrypt_data("ik", encrypted_data + last_bytes)
        self.assertEqual(decrypted_data[:-16], expected_data)
        # Check last 16 bytes for  checksum and unknown data
        self.assertEqual(decrypted_data[-16:], last_bytes)

    @patch("rgg_save_tool.xor_data")
    def test_other_games(self, mock_xor_data):
        # Mock the XOR operation to return the same data
        mock_xor_data.side_effect = lambda data, _: data
        for game in game_keys.keys():
            if game != "ik":  # Skip "ik" as it has special handling
                data = b"testdatachck"
                decrypted_data = decrypt_data(game, data)
                # The checksum should be removed
                self.assertEqual(decrypted_data, data[:-4])

    def test_unsupported_game(self):
        with self.assertRaises(SystemExit) as cm:
            encrypt_data("unsupported_game", b"testdata")
        self.assertEqual(cm.exception.code, 1)


class TestProcessFile(unittest.TestCase):
    @patch("builtins.open", side_effect=FileNotFoundError("test error"))
    def test_process_file_file_not_found(self, mock_file):
        with self.assertRaises(SystemExit) as cm:
            process_file("test.json", "y6")
        self.assertEqual(cm.exception.code, 1)

    # Patch prevents IOError false positive
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_data")
    def test_process_file_unsupported_game(self, mock_file):
        with self.assertRaises(SystemExit) as cm:
            process_file("test.json", "invalid")
        self.assertEqual(cm.exception.code, 1)

    @patch("rgg_save_tool.decrypt_data")
    @patch("rgg_save_tool.encrypt_data", return_value="encrypted data")
    @patch("builtins.open", new_callable=mock_open, read_data=b"test data")
    def test_process_file_encrypt(self, mock_file, mock_encrypt, mock_decrypt):
        process_file("test_y6.json", "y6")
        mock_decrypt.assert_not_called()
        mock_encrypt.assert_called_once_with("y6", b"test data")
        mock_file.assert_called_with("test.sav", "wb")
        mock_file().write.assert_called_once_with("encrypted data")

    @patch("rgg_save_tool.decrypt_data", return_value="decrypted data")
    @patch("rgg_save_tool.encrypt_data")
    @patch("builtins.open", new_callable=mock_open, read_data=b"test data")
    def test_process_file_decrypt(self, mock_file, mock_encrypt, mock_decrypt):
        process_file("test.sav", "y6")
        mock_decrypt.assert_called_once_with("y6", b"test data")
        mock_encrypt.assert_not_called()
        mock_file.assert_called_with("test_y6.json", "wb")
        mock_file().write.assert_called_once_with("decrypted data")


class TestGameSaveIdentification(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open)
    def test_file_is_a_game_save(self, mock_file):
        # Test each game and its associated headers
        for game, headers in game_headers.items():
            for header in headers:
                read_data = header + b"remaining_data"
                mock_file.return_value.read.return_value = read_data
                self.assertEqual(identify_game_from_save("fake_file"), game)

    @patch("builtins.open", new_callable=mock_open)
    def test_file_is_not_a_game_save(self, mock_file):
        # Test with data that doesn"t match the header
        mock_file.return_value.read.return_value = b"different_data"
        self.assertFalse(identify_game_from_save("fake_file"))

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_exit_when_file_not_found(self, mock_file):
        with self.assertRaises(SystemExit) as cm:
            identify_game_from_save("nonexistent_file")
        self.assertEqual(cm.exception.code, 1)


class TestFindGameAbbreviation(unittest.TestCase):
    @patch("sys.argv", ["rgg_save_tool.py", "test_file_ik.json", "ik"])
    def test_game_abbr_in_command_line(self):
        result = find_game_abbreviation("test_file_ik.json")
        self.assertEqual(result, "ik")

    def test_game_abbr_in_filename(self):
        result = find_game_abbreviation("test_file_lj.sav")
        self.assertEqual(result, "lj")

    @patch("rgg_save_tool.identify_game_from_save", return_value="ik")
    def test_detect_game_from_header(self, mock_from_game_save):
        result = find_game_abbreviation("test_file.sav")
        self.assertEqual(result, "ik")

    @patch("rgg_save_tool.identify_game_from_save", return_value=False)
    @patch("sys.exit", side_effect=SystemExit)
    def test_failed_detection(self, mock_from_game_save, mock_exit):
        with self.assertRaises(SystemExit) as cm:
            find_game_abbreviation("test_file.sav")
        self.assertEqual(cm.exception.code, 1)


class TestConvertIshinSave(unittest.TestCase):
    input_bytes = bytes.fromhex("00000000000000000000000000000000")

    @patch("builtins.open", new_callable=mock_open, read_data=input_bytes)
    def test_convert_to_steam(self, mock_file):
        output_bytes = bytes.fromhex("00000000210000000000000000000000")

        process_file("input.sys", "ik", to_steam=True)

        mock_file.assert_called_with("input_ik.json", "wb")
        mock_file().write.assert_called_once_with(output_bytes)

    @patch("builtins.open", new_callable=mock_open, read_data=input_bytes)
    def test_convert_to_gamepass(self, mock_file):
        output_bytes = bytes.fromhex("000000008F0000000000000000000000")

        process_file("input.sys", "ik", to_gamepass=True)

        mock_file.assert_called_with("input_ik.json", "wb")
        mock_file().write.assert_called_once_with(output_bytes)

    @patch("builtins.open", new_callable=mock_open, read_data=input_bytes)
    def test_default_output_file(self, mock_file):
        output_filename = "output.ext"
        output_bytes = bytes.fromhex("00000000210000000000000000000000")
        process_file("input.sys", "ik", to_steam=True, output_file=output_filename)

        mock_file.assert_called_with(output_filename, "wb")
        mock_file().write.assert_called_once_with(output_bytes)


if __name__ == "__main__":
    unittest.main()
