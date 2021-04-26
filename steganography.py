# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 14:52:58 2021

@author: rober
"""

import math

import numpy as np

from IPython.display import display

from PIL import Image

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
    
    print(im_arr.shape)
    print(flat.shape)
    
    #Get rid of the unused bits
    truncated = flat[:used_numbers]
    print(truncated.shape)
    
    #Group the chunks together
    chunked = np.reshape(truncated, (num_blocks, block_size))
    print(chunked.shape)
    
    #Get the bits
    bits = np.mod(chunked, 2)
    

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
    
    im_arr = np.asarray(image)
    
    least_bit_im_arr = least_bit(im_arr)
    
    least_bit_image = Image.fromarray(least_bit_im_arr)
    # display(least_bit_image)
    
    decode_message(im_arr)

def main():
    im_test()
    

if __name__ == '__main__':
    main()