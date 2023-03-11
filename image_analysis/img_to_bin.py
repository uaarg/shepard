import codecs
import binascii

def img_to_binary(fileName):
    with open(fileName, 'rb') as file:
        image_data = file.read()

    data = binascii.hexlify(image_data)

    binary = bin(int(data, 16))
    binary = binary[2:].zfill(32)

    binary_filename = fileName[:-4] + '.bin'
    with open(binary_filename, 'wb') as file:
        file.write(binary.encode())
    return binary_filename

def binary_to_image(fileName):
    binFile = open(fileName,'rb')
    binaryData = binFile.read()
    hexData = '%0*X' % ((len(binaryData) + 3) // 4, int(binaryData, 2))

    decode_hex = codecs.getdecoder("hex_codec")
    hexData = decode_hex(hexData)[0]

    png_filename = fileName[:-4] + '_from_binary.png'
    with open(png_filename, 'wb') as file:
        file.write(hexData)

def main():
    bin_file = img_to_binary('test1.png') # change file name
    binary_to_image(bin_file)

if __name__ == "__main__":
    main()