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
        # print(num)
        # result.append(chr(num))
        result.append(num)
    return result
    # return ''.join(result)

def get_bits(num, width=6):
    """
    Return the bits in the number, from least significant to most.
    """
    result = list()
    for _ in range(width):
        result.append(num % 2)
        num //= 2
    return result

def decode_message(im_arr, block_size=64):
    bits_per_block = round(math.log(block_size, 2))
    
    im, ih, depth = im_arr.shape
    num_pixels = im*ih
    num_numbers = num_pixels * 3
    num_blocks = num_numbers // block_size
    used_numbers = num_blocks * block_size
    
    #Ignore the alpha channel
    without_alpha = im_arr[:, :, :3]
    
    #Flatten the image
    flat = np.reshape(without_alpha, [num_numbers])
    
    # print(im_arr.shape)
    # print(flat.shape)
    
    #Get rid of the unused bits
    truncated = flat[:used_numbers]
    # print(truncated.shape)
    
    #Group the chunks together
    chunked = np.reshape(truncated, (num_blocks, block_size))
    # print(chunked.shape)
    
    #Get the bits
    bits = np.mod(chunked, 2)
    
    #The counting array
    count = np.arange(start=0, stop=block_size)
    count = np.stack([count]*num_blocks, axis=0)
    # print(count.shape)
    
    #Do the operation
    prod = np.multiply(bits, count)
    
    ors = np.bitwise_xor.reduce(prod, axis=1)
    
    # print(ors.shape)
    # print(ors)
    
    bits = list()
    for i in range(ors.shape[0]):
        bits.extend(get_bits(ors[i]))
    
    return bits

def least_bit(im_arr):
    #Take modulus by 2 to get last bit
    new_im_arr = np.mod(im_arr, 2)
    
    #Set alpha to same as source image
    new_im_arr[:, :, 3] = im_arr[:, :, 3]
    
    #Magnify image for visibility
    new_im_arr[:, :, 0:3] *= 255
    
    return new_im_arr

def im_test():
    image = Image.open('images/doge_2.png')
    # display(image)
    
    im_arr = np.asarray(image, dtype=np.uint8)
    
    least_bit_im_arr = least_bit(im_arr)
    
    least_bit_image = Image.fromarray(least_bit_im_arr)
    # display(least_bit_image)
    
    bits = decode_message(im_arr)
    # print(bits)
    message = bits_to_str(bits)
    print(message)

def main():
    im_test()
    

if __name__ == '__main__':
    main()