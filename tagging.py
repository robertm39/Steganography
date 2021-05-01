# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 20:34:31 2021

@author: rober
"""

import math

import numpy as np

from PIL import Image

import conversion as conv
import steganography as stega

# A tag is a sequence of bits at the start of a hidden message
# that describes the type and layout of the message.
#
# The first 64 bits are the check bits.
# If these bits have the right pattern,
# it is almost certain that there is a message.
#
# The next bit specifies whether the tag is short format or long format.
#
# In short format,
# the next 8 bits specify the type of the message
# the next 56 bits specify the format of the message (length, dimensions, etc.)
#
# In long format,
# The next 

TYPE_STRING_TAG = 0
TYPE_IMAGE_TAG = 1

def convert_to_string(fields, bits):
    width, length = [conv.bits_to_num(b) for b in fields]
    message = list()
    
    for i in range(length):
        char_bits = bits[i*width:(i+1)*width]
        char_num = conv.bit_to_num(char_bits)
        char = chr(char_num)
        message.append(char)
    
    return message

def convert_to_image(fields, bits):
    w, h, d, a = [conv.bits_to_num(b) for b in fields]
    
    shape = (w, h, d)
    
    num_bits = w*h*d*8
    bits = bits[:num_bits]
    
    return conv.bits_to_image(bits, shape, bool(a))

FROM_BITS_CONVERTER_FROM_TYPE = {TYPE_STRING_TAG: convert_to_string,
                                 TYPE_IMAGE_TAG: convert_to_image}

def convert_from_string(string):
    max_ord = max([ord(c) for c in string])
    width = math.ceil(math.log(max_ord, 2))
    
    
    
def convert_from_image(image):
    return [0] #No fields for now

TO_BITS_CONVERTER_FROM_TYPE = {TYPE_STRING_TAG: convert_from_string,
                               TYPE_IMAGE_TAG: convert_from_image}

NUM_CHECK_BITS = 64
CHECK_NUM = 15971532633023303877
CHECK_BITS = tuple(conv.get_bits(CHECK_NUM, width=NUM_CHECK_BITS))

FIELD_FIRST_SEGMENT_LENGTH = 3
FIELD_SEGMENT_LENGTH = 8

class CheckBitsError(Exception):
    pass

def validate_message(bits):
    """
    Check that the given message is a valid message using the 64 check bits.
    
    Parameters:
        bits: The bits of the message to check.
    
    Returns:
        bool: Whether the message is a valid message.
    """
    return bits[:NUM_CHECK_BITS] == CHECK_BITS

def read_field(i):
    """
    Read a field from the given bit-iterator.
    
    Parameters:
        i: The iterator over the bits to parse a length-spec from.
    
    Returns:
        [int]: The read field.
    """
    *bits, c = next(i), next(i), next(i), next(i)
    
    if not c:
        return bits
    
    while True:
        for _ in range(FIELD_SEGMENT_LENGTH):
            bits.append(next(i))
        if not next(i):
            return bits

def write_field(field):
    """
    Return the bit-string for the given field.
    
    Parameters:
        field: The field to write.
    
    Return:
        The bit-string for the given field.
    """
    f_bits = conv.get_bits(field)
    l = len(f_bits)
    
    if l <= FIELD_FIRST_SEGMENT_LENGTH:
        ext = FIELD_FIRST_SEGMENT_LENGTH - l
        return ([0] * ext) + f_bits + [0]
    
    num_sections = (l - FIELD_FIRST_SEGMENT_LENGTH) / FIELD_SEGMENT_LENGTH
    num_sections = math.ceil(num_sections)
    num_bits = num_sections * FIELD_SEGMENT_LENGTH + FIELD_FIRST_SEGMENT_LENGTH
    padding = [0] * (num_bits - l)
    
    mid_bits = padding + f_bits
    
    result = list()
    result.extend(mid_bits[:FIELD_FIRST_SEGMENT_LENGTH])
    result.append(1)
    mid_bits = mid_bits[FIELD_FIRST_SEGMENT_LENGTH:]
    
    for i in range(num_sections):
        s_bits = mid_bits[:FIELD_SEGMENT_LENGTH]
        result.extend(s_bits)
        
        if i == num_sections - 1:
            result.append(0)
        else:
            result.append(1)
    
    return result

def write_fields(fields):
    bits = list()
    for field, i in enumerate(fields):
        # The continuing bit
        if i == len(fields) - 1:
            bits.append(0)
        else:
            bits.append(1)
        
        bits.extend(write_field(field))
    return bits

def parse_message(bits):
    """
    Parse the message bits into the fields contained in the tag
    and the message itself.
    
    Parameters:
        bits: The bits of the message to parse.
    
    Returns:
        int: The type field.
        [[int]]: The format fields.
        [int]: The message bits, not including the tag.
    """
    #Validate the message
    if not validate_message(bits):
        raise CheckBitsError()
        
    bits = bits[NUM_CHECK_BITS:]
    
    b_iter = iter(bits)
    
    m_format = conv.bits_to_num(read_field(b_iter))
    
    fields = list()
    
    while True:
        #We've come to the end of the list of fields
        if not next(b_iter):
            return m_format, fields, list(b_iter)
        
        fields.append(read_field(b_iter))

def decode_message(image, block_size):
    """
    Decode the message from the given image with the given block size.
    
    Parameters:
        image: The image with the hidden message.
        block_size: The size of the blocks.
    
    Returns:
        The hidden message.
    """
    bits = stega.decode_message(image, block_size=block_size)
    
    m_type, fields, bits = parse_message(bits)
    converter = FROM_BITS_CONVERTER_FROM_TYPE[m_type]
    
    return converter(fields, bits)

def encode_message(carrier, message, block_size):
    m_type = None
    
    if isinstance(message, str):
        m_type = TYPE_STRING_TAG
    elif isinstance(message, Image.Image):
        m_type = TYPE_IMAGE_TAG
    
    check_bits = list(CHECK_BITS)
    converter = TO_BITS_CONVERTER_FROM_TYPE[m_type]
    rest_bits = converter(message)
    
    bits = check_bits + rest_bits
    bits = np.array(bits, dtype=np.uint8)
    
    return stega.encode_message(carrier, bits, block_size=block_size)

# def to_bits_with_tag(message):
#     if isinstance(message, str):
#         return string_to_bits_with_tag(message)
#     if isinstance(message, Image.Image):
#         return image_to_bits_with_tag(message)

# def from_bits_with_tag(bits):
#     #The first 8 bits tell the type
#     #The next 24 are the check bits
#     #The next 32 tell the format
#     type_bits = bits[:8]
    
#     check_bits = bits[8:32]
#     if check_bits != CHECK_BITS:
#         raise CheckBitsError()
    
#     format_tag = bits[32:64]
    
#     # print(type_bits)
#     # print(format_tag)
    
#     rest = bits[64:]
    
#     # type_tag = int(''.join(type_bits), 2)
#     type_tag = conv.bits_to_num(type_bits)
    
#     if type_tag == TYPE_STRING_TAG:
#         length = conv.bits_to_num(format_tag)
#         num_bits = length*7
#         # relevant_bits = rest[:num_bits]
#         relevant_bits = rest
#         return conv.bits_to_str(relevant_bits, width=7)
    
#     if type_tag == TYPE_IMAGE_TAG:
#         width_bits = format_tag[:14]
#         height_bits = format_tag[14:28]
#         depth_bits = format_tag[28:31]
#         alpha_bit = format_tag[31]
        
#         width = conv.bits_to_num(width_bits)
#         height = conv.bits_to_num(height_bits)
#         depth = conv.bits_to_num(depth_bits)
#         add_alpha = bool(alpha_bit)
        
#         shape = (width, height, depth)
#         num_bits = width*height*depth*8
#         relevant_bits = rest[:num_bits]
        
#         return conv.bits_to_image(relevant_bits, shape, add_alpha)

# def string_to_bits_with_tag(string):
#     #8 bits to tag it as a string
#     type_bits = conv.get_bits(TYPE_STRING_TAG, width=8)
#     # print('Type bits:')
#     # print(type_bits)
    
#     #32 bits to tell the length of the string in bits
#     len_bits = conv.get_bits(len(string), width=32)
    
#     bits = conv.str_to_bits(string)
    
#     result = type_bits + len_bits + CHECK_BITS + bits
#     return np.array(result, dtype=np.uint8)

# #May be fragile
# def get_depth(image):
#     if image.mode == 'YCbCr':
#         return 3
#     if image.mode == 'RGBA': #The alpha channel is removed
#         return 3
#     return len(image.mode)

# def image_to_bits_with_tag(image):
#     #8 bits to tag it as an image
#     type_bits = conv.get_bits(TYPE_IMAGE_TAG, width=8)
    
#     w, h = image.size
#     d = get_depth(image)
    
#     #14 bits to tell the width of the image
#     width_bits = conv.get_bits(w, width=14)
    
#     #14 bits to tell the height of the image
#     height_bits = conv.get_bits(h, width=14)
    
#     #3 bits to tell the depth of the image
#     depth_bits = conv.get_bits(d, width=3)
    
#     #One bit to tell whether an alpha channel needs to be added back
#     add_alpha = image.mode == 'RGBA'
#     add_alpha_num = int(add_alpha)
#     add_alpha_bit = conv.get_bits(add_alpha_num, width=1)
    
#     bits = conv.image_to_bits(image, add_alpha)
    
#     tag_bits = type_bits + width_bits + height_bits + depth_bits + add_alpha_bit
#     tag_bits = tag_bits = list(CHECK_BITS)
#     tag_bits = np.array(tag_bits) 
    
#     return np.concatenate([tag_bits, bits], axis=0)
#     # return tag_bits + bits
