import argparse
import os

def convert_ishin_save(input_file, output_file, to_steam):
    try:
        # Open the input file in binary mode
        with open(input_file, 'rb') as f:
            # Read all bytes from the file
            data = bytearray(f.read())
    except IOError as e:
        print(f"Error: Failed to open file '{output_file}': {e.strerror}")
        return 1

    # Determine the byte to write based on the --to-steam/--to-gamepass argument
    new_byte = 0x21 if to_steam else 0x8F

    # Replace the 12th byte from the end of the file with the new byte
    data[-12] = new_byte

    try:
        # Open the output file in binary write mode
        with open(output_file, 'wb') as f:
            # Write the modified bytes to the output file
            f.write(data)
    except IOError as e:
        print(f"Error: Failed to write to file '{output_file}': {e.strerror}")
        return 1

    print(f'Successfully converted save file from {input_file} to {output_file}.')

# Create an argument parser
parser = argparse.ArgumentParser()

# Add arguments for the input file, output file, and conversion direction
parser.add_argument('input_file')
parser.add_argument('output_file', nargs='?', default=None)
parser.add_argument('--to-steam', action='store_true')
parser.add_argument('--to-gamepass', action='store_true')

# Parse the command-line arguments
args = parser.parse_args()

# If the output file argument was not specified, construct a default output file path
if args.output_file is None:
    args.output_file = os.path.splitext(args.input_file)[0] + '_converted.sav'
    
# Make sure exactly one of --to-steam or --to-gamepass was specified
if args.to_steam == args.to_gamepass:
    print('Error: Exactly one of --to-steam or --to-gamepass must be specified.')
    exit(1)

# Call the conversion function
convert_ishin_save(args.input_file, args.output_file, args.to_steam)