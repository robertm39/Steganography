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
        
        #Reverse the order
        chunk = chunk[::-1]
        
        num = int(''.join(chunk), 2)
        
        # print(num)
        result.append(chr(num))
        # result.append(num)
    # return result
    return ''.join(result)

def bits_to_nums(bits, width=6):
    """
    Convert a list of bits into a list of numbers.
    """
    result = list()
    for i in range(0, len(bits), width):
        chunk = list(bits[i:i+width])
        chunk = [str(i) for i in chunk]
        
        #Reverse the order
        chunk = chunk[::-1]
        
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
    Return the bits in the number, from least significant to most.
    """
    result = list()
    for _ in range(width):
        result.append(num % 2)
        num //= 2
    return result

def image_to_bits(im_arr, block_size):
    im, ih, depth = im_arr.shape
    num_pixels = im*ih
    num_numbers = num_pixels * 3
    num_blocks = num_numbers // block_size
    used_numbers = num_blocks * block_size
    
    #Ignore the alpha channel
    without_alpha = im_arr[:, :, :3]
    
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
    
    # #Add the alpha dimension
    # alpha = np.ones([width, height, 1])
    # alpha *= 255
    
    return im_arr

def get_count_array(num_blocks, block_size):
    count = np.arange(start=0, stop=block_size)
    count = np.stack([count]*num_blocks, axis=0)
    return count

def encode_message(image, message, block_size=64):
    """
    Encode the message into the given image.
    """
    im_arr = np.asarray(image)
    width, height, depth = im_arr.shape
    depth -= 1
    
    im_bits = image_to_bits(im_arr, block_size=block_size)
    num_blocks, _ = im_bits.shape
    
    count = get_count_array(num_blocks, block_size)
    prod = np.multiply(im_bits, count)
    chunk_nums = np.bitwise_xor.reduce(prod, axis=1)
    # print(chunk_nums.shape)
    
    message_bits = str_to_bits(message)
    #Expand the message bits to the same number of bits
    bits_per_block = round(math.log(block_size, 2))
    num_bits = num_blocks * bits_per_block
    message_bits.extend([0] * (num_bits - len(message_bits)))
    
    
    #Also combine the message bits into chunks
    message_nums = bits_to_nums(message_bits, width=bits_per_block)
    message_nums = np.array(message_nums)
    # print(message_nums.shape)
    # print(message_nums)
    
    diffs = np.bitwise_xor(chunk_nums, message_nums)
    # print(diffs.shape)
    # print(diffs)
    
    #I'm gonna do this the slow way for now
    #until I figure out the fast, numpy way
    
    #Twiddle the bits in im_bits to make the right output
    for i in range(num_blocks):
        diff = diffs[i]
        im_bits[i, diff] = 1 - im_bits[i, diff]
    
    #Now the bits have been 
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

def least_bit(im_arr):
    #Take modulus by 2 to get last bit
    new_im_arr = np.mod(im_arr, 2)
    
    #Set alpha to same as source image
    new_im_arr[:, :, 3] = im_arr[:, :, 3]
    
    #Magnify image for visibility
    new_im_arr[:, :, 0:3] *= 255
    
    return new_im_arr

def decode_test():
    image = Image.open('images/encoded_doge_2.png')
    
    bits = decode_message(image)
    message = bits_to_str(bits)
    print(message)

def encode_test():
    image = Image.open('images/doge_2.png')
    message = 'Testing 123'
    # message = 'BBBBBBBBBBB'
    # message = 'CCCCCCCCCCC'
    # message = 'DDDDDDDDDDD'
    
    image = encode_message(image, message)
    display(image)
    
    image.save('images/encoded_doge_2.png')

def main():
    encode_test()
    decode_test()

if __name__ == '__main__':
    main()