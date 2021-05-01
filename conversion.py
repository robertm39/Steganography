# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 20:31:51 2021

@author: rober
"""

import numpy as np

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

def get_bits(num, width=6):
    """
    Return the bits in the number, from most significant to least.
    """
    result = list()
    for _ in range(width):
        result.append(num % 2)
        num //= 2
    return result[::-1]

def str_to_bits(s, width=7):
    result = list()
    for char in s:
        num = ord(char)
        bits = get_bits(num, width=width)
        result.extend(bits)
    return result

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

def image_to_bits(image, ignore_last_channel=True):
    """
    Convert an image into a 1-D array of bits.
    """
    im_arr = np.asarray(image)
    w, h, d = im_arr.shape
    
    if ignore_last_channel:
        #Get rid of the alpha channel
        d -= 1
        im_arr = im_arr[:, :, :d]
    
    #Flatten the image into a list of numbers
    flattened = np.reshape(im_arr, w*h*d)
    
    into_bits = np.unpackbits(flattened)
    
    return into_bits

def bits_to_image(bits, shape, add_last_channel=True):
    """
    Convert a 1-D array of bits into an image.
    """
    w, h, d = shape
    
    bits = np.array(bits)
    flat = np.packbits(bits)
    im_arr = np.reshape(flat, [w, h, d])
    
    if add_last_channel:
        im_arr = add_alpha(im_arr, 255)
    
    return Image.fromarray(im_arr)