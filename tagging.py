# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 20:34:31 2021

@author: rober
"""

from enum import Enum


import numpy as np

from PIL import Image

import conversion as conv

#A tag is a sequence of 40 bits.
#The tag describes the type and format of a message.
#The first 8 bits specify the type of the message/
#The next 32 bits specify the size and dimensions, if applicable.

TYPE_STRING_TAG = 0
TYPE_IMAGE_TAG = 1
# class TypeTag(Enum):
#     STRING = 0
#     IMAGE = 1

def to_bits_with_tag(message):
    if isinstance(message, str):
        return string_to_bits_with_tag(message)
    if isinstance(message, Image.Image):
        return image_to_bits_with_tag(message)

def from_bits_with_tag(bits):
    #The first 8 bits tell the type
    #The nest 32 tell the format
    type_bits = bits[:8]
    format_tag = bits[8:40]
    
    # print(type_bits)
    # print(format_tag)
    
    rest = bits[40:]
    
    # type_tag = int(''.join(type_bits), 2)
    type_tag = conv.bits_to_num(type_bits)
    
    if type_tag == TYPE_STRING_TAG:
        length = conv.bits_to_num(format_tag)
        num_bits = length*7
        # relevant_bits = rest[:num_bits]
        relevant_bits = rest
        return conv.bits_to_str(relevant_bits, width=7)
    
    if type_tag == TYPE_IMAGE_TAG:
        width_bits = format_tag[:14]
        height_bits = format_tag[14:28]
        depth_bits = format_tag[28:31]
        alpha_bit = format_tag[31]
        
        width = conv.bits_to_num(width_bits)
        height = conv.bits_to_num(height_bits)
        depth = conv.bits_to_num(depth_bits)
        add_alpha = bool(alpha_bit)
        
        shape = (width, height, depth)
        num_bits = width*height*depth*8
        relevant_bits = rest[:num_bits]
        
        return conv.bits_to_image(relevant_bits, shape, add_alpha)

def string_to_bits_with_tag(string):
    #8 bits to tag it as a string
    type_bits = conv.get_bits(TYPE_STRING_TAG, width=8)
    # print('Type bits:')
    # print(type_bits)
    
    #32 bits to tell the length of the string in bits
    len_bits = conv.get_bits(len(string), width=32)
    
    bits = conv.str_to_bits(string)
    
    return type_bits + len_bits + bits

#May be fragile
def get_depth(image):
    if image.mode == 'YCbCr':
        return 3
    if image.mode == 'RGBA': #The alpha channel is removed
        return 3
    return len(image.mode)

def image_to_bits_with_tag(image):
    #8 bits to tag it as an image
    type_bits = conv.get_bits(TYPE_IMAGE_TAG, width=8)
    
    w, h = image.size
    d = get_depth(image)
    
    #14 bits to tell the width of the image
    width_bits = conv.get_bits(w, width=14)
    
    #14 bits to tell the height of the image
    height_bits = conv.get_bits(h, width=14)
    
    #3 bits to tell the depth of the image
    depth_bits = conv.get_bits(d, width=3)
    
    #One bit to tell whether an alpha channel needs to be added back
    add_alpha = image.mode == 'RGBA'
    add_alpha_num = int(add_alpha)
    add_alpha_bit = conv.get_bits(add_alpha_num, width=1)
    
    bits = conv.image_to_bits(image, add_alpha)
    
    tag_bits = type_bits + width_bits + height_bits + depth_bits + add_alpha_bit
    tag_bits = np.array(tag_bits) 
    
    return np.concatenate([tag_bits, bits], axis=0)
    # return tag_bits + bits