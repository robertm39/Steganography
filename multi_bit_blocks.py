# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 12:56:21 2021

@author: rober
"""

import math
import itertools

def convert(num, base, width):
    #Represent a number in the given base, 1 < base <= 2
    result = list()
    for p in range(width-1, -1, -1):
        if num >= base ** p:
            num -= base ** p
            result.append('1')
        else:
            result.append('0')
    return ''.join(result)

def get_choices(block_size, num_bits, num_groups):
    #Find the base
    # print(num_groups)
    base = block_size ** (1/ num_groups)
    # print(base)
    #Get the choices
    choices = list()
    for i in range(block_size):
        in_base = convert(i, base, num_groups)
        # print(in_base)
        choices.append(int(in_base, 2))
    return choices

def find_choice(choices, num_bits, target):
    #Find a selection of numbers from choices
    #whose xor equals the target numbers
    for comb in itertools.combinations_with_replacement(choices, num_bits):
        result = 0
        for num in comb:
            result ^= num
        if result == target:
            return comb
    return None

def get_num_successful(choices, num, max_target, num_groups):
    possibilities = 0
    for i in range(max_target):
        if find_choice(choices, num, i) is not None:
            possibilities += 1
        else:
            print(convert(i, 2, num_groups))
    return possibilities

def works(choices, num, max_target):
    for i in range(max_target):
        if find_choice(choices, num, i) is None:
            return False
    return True

block_bits = 6

block_size = 2 ** block_bits
num_bits = 2

choices = math.comb(block_size, num_bits)
num_groups = math.floor(math.log(choices, 2))

# num_groups = 6

choices = get_choices(block_size, num_bits, num_groups)
print('')
num_worked = get_num_successful(choices, num_bits, 2**num_groups, num_groups)
num_failed = 2**num_groups - num_worked
print('{} succeeded, {} failed'.format(num_worked, num_failed))