# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 14:52:58 2021

@author: rober
"""

import math

import numpy as np

from IPython.display import display

from PIL import Image

def bits_to_str(bits, width=7):
    """
    Convert a list of bits into a string.
    """
    result = list()
    for i in range(0, len(bits), width):
        chunk = list(bits[i:i+width])
        chunk = [str(i) for i in chunk]
        
        num = int(''.join(chunk), 2)
        
        result.append(chr(num))
        
    return ''.join(result)

def bits_to_nums(bits, width=6):
    """
    Convert a list of bits into a list of numbers.
    """
    result = list()
    for i in range(0, len(bits), width):
        chunk = list(bits[i:i+width])
        chunk = [str(i) for i in chunk]
        
        num = int(''.join(chunk), 2)
        result.append(num)
    return result

def str_to_bits(s, width=7):
    result = list()
    for char in s:
        num = ord(char)
        bits = get_bits(num, width=width)
        result.extend(bits)
    return result

def get_bits(num, width=6):
    """
    Return the bits in the number, from most significant to least.
    """
    result = list()
    for _ in range(width):
        result.append(num % 2)
        num //= 2
    return result[::-1]

def image_to_bits(im_arr, block_size):
    im, ih, depth = im_arr.shape
    num_pixels = im*ih
    num_numbers = num_pixels * (depth-1)
    num_blocks = num_numbers // block_size
    used_numbers = num_blocks * block_size
    
    #Ignore the alpha channel
    without_alpha = im_arr[:, :, :depth-1]
    
    #Flatten the image
    flat = np.reshape(without_alpha, [num_numbers])
    
    #Get rid of the unused bits
    truncated = flat[:used_numbers]
    
    #Group the chunks together
    chunked = np.reshape(truncated, (num_blocks, block_size))
    
    #Get the bits
    bits = np.mod(chunked, 2)
    
    return bits

def bits_to_image(bits, width, height, depth):
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
        print('Message too long')
    
    message_bits = message_bits + ([0] * expansion)
    return message_bits

def encode_message(image, message_bits, block_size=64):
    """
    Encode the message bits into the given image.
    """
    im_arr = np.asarray(image)
    width, height, depth = im_arr.shape
    
    #Ignore alpha channel
    depth -= 1
    
    im_bits = image_to_bits(im_arr, block_size=block_size)
    num_blocks, _ = im_bits.shape
    
    chunk_nums = get_chunk_nums(im_bits, num_blocks, block_size)
    
    # message_bits = str_to_bits(message)
    
    # #Expand the message bits to the same number of bits
    message_bits = expand_message_bits(message_bits, block_size, num_blocks)
    
    #Also combine the message bits into chunks
    bits_per_block = round(math.log(block_size, 2))
    message_nums = bits_to_nums(message_bits, width=bits_per_block)
    message_nums = np.array(message_nums)
    
    diffs = np.bitwise_xor(chunk_nums, message_nums)
    
    #Twiddle the bits in im_bits to make the right output
    for i in range(num_blocks):
        diff = diffs[i]
        im_bits[i, diff] = 1 - im_bits[i, diff]
    
    #Now the bits have been changed,
    #Reshape them into an image and combine them with the given image
    message_image = bits_to_image(im_bits, width, height, depth)
    
    #Wipe out the low order bits
    im_arr = im_arr - np.mod(im_arr, 2)
    
    #Add the new low order bits
    im_arr[:, :, 0:depth] += message_image
    
    #Add alpha back in
    im_arr[:, :, depth] = 255
    
    return Image.fromarray(im_arr)

def decode_message(image, block_size=64):
    """
    Decode the message from the given image.
    """
    im_arr = np.asarray(image)
    
    bits = image_to_bits(im_arr, block_size=block_size)
    num_blocks, _ = bits.shape
    
    #The counting array
    count = get_count_array(num_blocks, block_size)
    
    #Do the operation
    prod = np.multiply(bits, count)
    
    ors = np.bitwise_xor.reduce(prod, axis=1)
    
    bits_per_block = round(math.log(block_size, 2))
    bits = list()
    for i in range(ors.shape[0]):
        bits.extend(get_bits(ors[i], bits_per_block))
    
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
    with open('out_bits.txt', 'w') as file:
        for bit in bits:
            file.write(str(bit))
        file.write('\n')
    # print(bits)
    message = bits_to_str(bits)
    print(message)

def encode_test():
    image = Image.open('images/doge_2.png')
    message = 'February eight, eighteen-seventy-eight,\n'\
              'South of Trout Creek, west of Cedar Lake,\n'\
              'On the winding mountain trail,\n'\
              'Of the North Pacific Union Rail,\n'\
              'The snow arrived on time; the circus train was running late'
    
    message_bits = str_to_bits(message)
    # print(message_bits)
    
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

def main():
    encode_test()
    decode_test()
    # detection_test()

if __name__ == '__main__':
    main()