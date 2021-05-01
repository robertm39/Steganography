# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 14:52:58 2021

@author: rober
"""

import math

import numpy as np

from IPython.display import display
from PIL import Image

import conversion as conv
import tagging

def image_to_blocks(im_arr, block_size):
    im, ih, depth = im_arr.shape
    num_pixels = im*ih
    
    num_numbers = num_pixels * depth
    num_blocks = num_numbers // block_size
    used_numbers = num_blocks * block_size
    
    #Flatten the image
    flat = np.reshape(im_arr, [num_numbers])
    
    #Get rid of the unused bits
    truncated = flat[:used_numbers]
    
    #Group the chunks together
    chunked = np.reshape(truncated, (num_blocks, block_size))
    
    #Get the bits
    bits = np.mod(chunked, 2)
    
    return bits

def blocks_to_image(bits, width, height, depth):
    """
    Convert the given bits to an image with values only in the least
    significant bits.
    """
    num_blocks, block_size = bits.shape
    num_numbers = width * height * depth
    
    #Flatten and extend the bits
    num_bits = num_blocks * block_size
    flat_bits = np.reshape(bits, num_bits)
    
    extend = num_numbers - num_bits
    extend_bits = np.zeros([extend], dtype=np.uint8)
    flat_bits = np.concatenate([flat_bits, extend_bits])
    
    #Reshape the bits into the shape of an image
    im_arr = np.reshape(flat_bits, [width, height, depth])
    
    return im_arr

def get_chunk_nums(im_bits, num_blocks, block_size):
    """
    Return the array with the XOR of the active bits in each block.
    """
    count = get_count_array(num_blocks, block_size)
    prod = np.multiply(im_bits, count)
    chunk_nums = np.bitwise_xor.reduce(prod, axis=1)
    return chunk_nums

def get_count_array(num_blocks, block_size):
    """
    Return the count array.
    """
    count = np.arange(start=0, stop=block_size)
    count = np.stack([count]*num_blocks, axis=0)
    return count

def expand_message_bits(message_bits, block_size, num_blocks):
    bits_per_block = round(math.log(block_size, 2))
    num_bits = num_blocks * bits_per_block
    expansion = num_bits - len(message_bits)
    
    if expansion < 0:
        print('Message too long: {} - {}'.format(len(message_bits), num_bits))
        raise ValueError()
    
    message_bits = list(message_bits)
    message_bits = message_bits + ([0] * expansion)
    return message_bits

def remove_alpha(im_arr):
    _, _, d = im_arr.shape
    return im_arr[:, :, :d-1]

def encode_message(image, message_bits, block_size=64):
    """
    Encode the message bits into the given image.
    """
    has_alpha = image.mode == 'RGBA'
    
    im_arr = np.asarray(image)
    width, height, depth = im_arr.shape
    
    #Ignore alpha channel
    if has_alpha:
        depth -= 1
        im_arr = remove_alpha(im_arr)
    
    im_bits = image_to_blocks(im_arr, block_size=block_size)
    num_blocks, _ = im_bits.shape
    
    chunk_nums = get_chunk_nums(im_bits, num_blocks, block_size)
    
    # #Expand the message bits to the same number of bits
    message_bits = expand_message_bits(message_bits, block_size, num_blocks)
    
    #Also combine the message bits into chunks
    bits_per_block = round(math.log(block_size, 2))
    message_nums = conv.bits_to_nums(message_bits, width=bits_per_block)
    message_nums = np.array(message_nums)
    
    diffs = np.bitwise_xor(chunk_nums, message_nums)
    
    #Twiddle the bits in im_bits to make the right output
    for i in range(num_blocks):
        diff = diffs[i]
        im_bits[i, diff] = 1 - im_bits[i, diff]
    
    #Now the bits have been changed,
    #Reshape them into an image and combine them with the given image
    message_image = blocks_to_image(im_bits, width, height, depth)
    
    #Wipe out the low order bits
    im_arr = im_arr - np.mod(im_arr, 2)
    
    #Add the new low order bits
    im_arr[:, :, 0:depth] += message_image
    
    # #Add alpha back in
    if has_alpha:
        im_arr = conv.add_alpha(im_arr, 255)
    
    return Image.fromarray(im_arr)

def decode_message(image, block_size=64):
    """
    Decode the message from the given image.
    """
    im_arr = np.asarray(image)
    
    has_alpha = image.mode == 'RGBA'
    
    #Ignore alpha channel
    if has_alpha:
        im_arr = remove_alpha(im_arr)
    
    bits = image_to_blocks(im_arr, block_size=block_size)
    num_blocks, _ = bits.shape
    
    #The counting array
    count = get_count_array(num_blocks, block_size)
    
    #Do the operation
    prod = np.multiply(bits, count)
    
    ors = np.bitwise_xor.reduce(prod, axis=1)
    
    bits_per_block = round(math.log(block_size, 2))
    bits = list()
    for i in range(ors.shape[0]):
        bits.extend(conv.get_bits(ors[i], bits_per_block))
    
    return bits

def least_bit(image):
    im_arr = np.asarray(image)
    #Take modulus by 2 to get last bit
    new_im_arr = np.mod(im_arr, 2)
    
    #Set alpha to same as source image
    new_im_arr[:, :, 3] = im_arr[:, :, 3]
    
    #Magnify image for visibility
    new_im_arr[:, :, 0:3] *= 255
    
    return Image.fromarray(new_im_arr)

def density(block_size, width=7):
    
    bits_per_block = round(math.log(block_size, 2))
    letters_per_block = bits_per_block / width
    
    nums_per_pixel = 3
    return nums_per_pixel * letters_per_block / block_size

def decode_test():
    image = Image.open('images/encoded_doge_2.png')
    
    bits = decode_message(image)
    message = conv.bits_to_str(bits)
    print(message)

def encode_test():
    image = Image.open('images/doge_2.png')
    message = 'February eight, eighteen-seventy-eight,\n'\
              'South of Trout Creek, west of Cedar Lake,\n'\
              'On the winding mountain trail,\n'\
              'Of the North Pacific Union Rail,\n'\
              'The snow arrived on time; the circus train was running late'
    
    message_bits = conv.str_to_bits(message)
    
    image = encode_message(image, message_bits)
    display(image)
    
    image.save('images/encoded_doge_2.png')

def detection_test():
    image = Image.open('images/mountain_2.png')
    message = 'February eight, eighteen-seventy-eight,\n'\
              'South of Trout Creek, west of Cedar Lake,\n'\
              'On the winding mountain trail,\n'\
              'Of the North Pacific Union Rail,\n'\
              'The snow arrived on time; the circus train was running late'
    
    encoded = encode_message(image, message)
    
    display(image)
    display(encoded)
    display(least_bit(image))
    
    display(least_bit(encoded))

def image_bits_conversion_test():
    image = Image.open('images/secret/stego_small.png')
    w, h = image.size
    shape = (w, h, 3)
    
    bits = conv.image_to_bits(image, ignore_last_channel=True)
    new_image = conv.bits_to_image(bits, shape, add_last_channel=True)
    
    display(image)
    display(new_image)

def string_bits_conversion_test():
    message = 'In the suburbs I, I learned to drive'
    str_bits = conv.str_to_bits(message, width=7)
    new_message = conv.bits_to_str(str_bits, width=7)
    print(message)
    print(new_message)

def encode_image():
    carrier = Image.open('images/secret/image_1.jpg')
    to_encode = Image.open('images/secret/stego_small.png')
    
    bits = conv.image_to_bits(to_encode, ignore_last_channel=True)
    
    encoded = encode_message(carrier, bits, block_size=2**8)
    encoded.save('images/secret/encoded_1.png')

def decode_image():
    encoded = Image.open('images/secret/encoded_1.png')
    
    bits = decode_message(encoded, block_size=2**8)
    
    num_bits = 64*64*3*8
    bits = bits[:num_bits]
    
    image = conv.bits_to_image(bits, (64, 64, 3), add_last_channel=True)
    display(image)

def encode_with_tag():
    carrier = Image.open('images/secret/big_1.jpg')
    display(carrier)
    
    # message = ''
    message = Image.open('images/secret/small.png')
    
    bits = tagging.to_bits_with_tag(message)
    
    encoded = encode_message(carrier, bits, block_size=2**8)
    encoded.save('images/secret/tagged_2.png')

def decode_with_tag():
    encoded = Image.open('images/secret/tagged_2.png')
    bits = decode_message(encoded, block_size=2**8)
    
    message = tagging.from_bits_with_tag(bits)
    
    if isinstance(message, str):
        print(message)
    elif isinstance(message, Image.Image):
        display(message)

def new_encode_test():
    carrier = Image.open('images/doge_2.png')
    display(carrier)
    
    message = 'testing 1 2 3 4 5'

def new_decode_test():
    pass

def main():
    # encode_test()
    # decode_test()
    # detection_test()
    # image_bits_conversion_test()
    # string_bits_conversion_test()
    
    # encode_image()
    # decode_image()
    
    # encode_with_tag()
    decode_with_tag()

if __name__ == '__main__':
    main()