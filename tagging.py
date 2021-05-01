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

# 340,282,366,920,938,463,463,374,607,431,768,211,456
# Or around 340 undecillion numbers
# with a roughly 3.3e-39 chance of a spurious match
# or 0.0000000000000000000000000000000000000003314045800354739
#
# so I'm not going to bother with checking for spurious matches

# A tag is a sequence of bits at the start of a hidden message
# that describes the type and layout of the message.
#
# The first 128 bits are the check bits.
# If these bits have the right pattern,
# it is almost certain that there is a message.
#
# Then there is one variable-length field to specify the type of the message
# And a list of variable-length fields to specify the format.

TYPE_STRING_TAG = 0
TYPE_IMAGE_TAG = 1

def convert_to_string(fields, bits):
    length, width = [conv.bits_to_num(b) for b in fields]
    message = list()
    
    for i in range(length):
        char_bits = bits[i*width:(i+1)*width]
        char_num = conv.bits_to_num(char_bits)
        char = chr(char_num)
        message.append(char)
    
    return ''.join(message)

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
    
    m_type = TYPE_STRING_TAG
    length = len(string)
    width = math.ceil(math.log(max_ord, 2))
    
    type_bits = write_field(m_type)
    field_bits = write_fields([length, width])
    
    str_bits = list()
    for c in string:
        c_bits = conv.get_bits(ord(c), width=width)
        str_bits.extend(c_bits)    
    
    bits = type_bits
    bits.extend(field_bits)
    bits.extend(str_bits)
    
    return bits

#May be fragile
def get_depth(image):
    if image.mode == 'YCbCr':
        return 3
    if image.mode == 'RGBA': #The alpha channel is removed
        return 3
    return len(image.mode)

def convert_from_image(image):
    w, h = image.size
    d = get_depth(image)
    a = image.mode == 'RGBA'
    
    m_type = TYPE_IMAGE_TAG
    type_bits = write_field(m_type)
    field_bits = write_fields([w, h, d, int(a)])
    
    image_bits = conv.image_to_bits(image, bool(a))
    
    bits = type_bits
    bits.extend(field_bits)
    bits.extend(image_bits)
    return bits

TO_BITS_CONVERTER_FROM_TYPE = {TYPE_STRING_TAG: convert_from_string,
                               TYPE_IMAGE_TAG: convert_from_image}

NUM_CHECK_BITS = 128
# CHECK_NUM = 15971532633023303877
CHECK_NUM = 301745980665976028475011311407568552610
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
    return bits[:NUM_CHECK_BITS] == list(CHECK_BITS)

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
    for i, field in enumerate(fields):
        # The continuing bit
        if i == len(fields) - 1:
            bits.append(0)
        else:
            bits.append(1)
        f_bits = write_field(field)
        
        bits.extend(f_bits)
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
            fields.append(read_field(b_iter))
            return m_format, fields, list(b_iter)
        
        fields.append(read_field(b_iter))

def decode_message(image, block_size=None):
    """
    Decode the message from the given image with the given block size.
    
    Parameters:
        image: The image with the hidden message.
        block_size: The size of the blocks.
    
    Returns:
        The hidden message.
    """
    if block_size is None:
        w, h = image.size
        d = 3 #An estimate
        num_bits = w*h*d
        
        i = math.floor(math.log(num_bits, 2))
        
        # i = 1
        while i >= 1:
            #Keep going until the check bits match
            #or the block size is bigger than the image
            block_size = 2**i
            # print('Block size: {}'.format(block_size))
            try:
                bits = stega.decode_message(image, block_size=block_size)
                
                m_type, fields, bits = parse_message(bits)
                converter = FROM_BITS_CONVERTER_FROM_TYPE[m_type]
                return converter(fields, bits)
            
            except ValueError:
                i -= 1
                continue
            except CheckBitsError:
                i -= 1
                continue
        
        return converter(fields, bits)
    
    bits = stega.decode_message(image, block_size=block_size)
    
    m_type, fields, bits = parse_message(bits)
    converter = FROM_BITS_CONVERTER_FROM_TYPE[m_type]
    
    return converter(fields, bits)

def encode_message(carrier, message, block_size=None):
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
    
    #If the block size is unspecified,
    #choose the largest size that will work
    if block_size is None:
        w, h = carrier.size
        d = get_depth(carrier)
        num_bits = w*h*d
        
        num_message_bits = len(bits)
        block_power = 1
        prev_block_power = block_power
        capacity = (num_bits // (2** block_power)) * block_power
        
        while capacity >= num_message_bits:
            prev_block_power = block_power
            block_power += 1
            capacity = (num_bits // (2** block_power)) * block_power
        
        block_size = 2 ** prev_block_power
    
    
    return stega.encode_message(carrier, bits, block_size=block_size)
