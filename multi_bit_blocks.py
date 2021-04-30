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
    for order in range(num_bits+1):
        for comb in itertools.combinations_with_replacement(choices, order):
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
            pass
            # print(convert(i, 2, num_groups))
    return possibilities

def works(choices, num, max_target):
    for i in range(max_target):
        if find_choice(choices, num, i) is None:
            return False
    return True

#For using as a key in a dict
def bitstring_combination(bitstrings):
    return tuple(sorted(bitstrings))

import random
def random_bitstring(string_len):
    return random.randint(0, 2**string_len-1)

def make_random_bitstrings(string_len, num_strings, num_choices):
    """
    Make a list of random bitstrings.
    """
    bitstrings = list()
    
    for _ in range(num_strings):
        bitstring = random_bitstring(string_len)
        bitstrings.append(bitstring)
    return bitstrings

def get_num_overlaps(xors, bitstring, num_choices, found):
    result = 0
    for num, combs in xors.items():
        if num >= num_choices:
            continue
        for comb, xor in combs.items():
            total_xor = xor ^ bitstring
            if total_xor in found:
                result += 1
    return result

def make_bitstrings(string_len, num_strings, num_choices, i=5):
    """
    Construct a set of num_strings string_len long bitstrings
    such that for each string_len long bitstring,
    there is a subset of num_choices bistrings
    whose bitwise xor is that bitstring.
    """
    # random.seed(2)
    
    #A dictionary from bitstrings we can reach
    #to the combinations that make them
    found = {0: ()}
    bitstrings = list()
    
    #The empty comb has an xor of zero
    #This should work as a base
    xors = {0: {(): 0}}
    
    for i in range(num_strings):
        print(i)
        
        best_bitstring = random_bitstring(string_len)
        min_overlaps = get_num_overlaps(xors,
                                        best_bitstring,
                                        num_choices,
                                        found)
        
        for _ in range(i-1):
            bitstring = random_bitstring(string_len)
            #See how many overlaps this bitstring makes
            num_overlaps = get_num_overlaps(xors,
                                            bitstring,
                                            num_choices,
                                            found)
            
            if num_overlaps < min_overlaps:
                min_overlaps = num_overlaps
                best_bitstring = bitstring
            
            if num_overlaps == 0:
                break
        
        bitstrings.append(best_bitstring)
        
        #Update xors
        to_add = list()
        for num, combs in xors.items():
            #We can't add another to these combs
            if num >= num_choices:
                continue
            
            for comb, xor in combs.items():
                total_xor = xor ^ best_bitstring
                total_comb = comb + tuple([best_bitstring])
                total_comb = bitstring_combination(total_comb)
                to_add.append((total_xor, total_comb))
        
        for total_xor, total_comb in to_add:
            total_len = len(total_comb)
            if not total_len in xors:
                xors[total_len] = dict()
            xors[total_len][total_comb] = total_xor
            if not total_xor in found:
                found[total_xor] = total_comb
        
    return bitstrings, found

def test():
    block_bits = 10
    
    block_size = 2 ** block_bits
    num_bits = 2
    
    num_choices = math.comb(block_size, num_bits)
    num_groups = math.floor(math.log(num_choices, 2))
    
    # num_groups = 6
    
    # choices = get_choices(block_size, num_bits, num_groups)
    print('Block size: {}'.format(block_size))
    choices, combs = make_bitstrings(num_groups, block_size, num_bits)
    print('Found choices\n')
    
    num_worked = len(combs)
    # other_num_worked = get_num_successful(choices, num_bits, 2**num_groups, num_groups)
    num_failed = 2**num_groups - num_worked
    print('{} succeeded, {} failed'.format(num_worked, num_failed))
    # print('test: {}'.format(other_num_worked))
    
    save_filename = 'save_bitstrings.txt'
    
    if num_failed == 0:
        with open(save_filename, 'w') as save_file:
            for bitstring in choices:
                save_file.write(convert(bitstring, 2, num_groups) + '\n')
            save_file.write('\n')
            
            #Store the indices for fast retrieval
            indices = {b:choices.index(b) for b in choices}
            for target in sorted(list(combs)):
                c_indices = list([indices[c] for c in combs[target]])
                c_indices.sort()
                save_file.write('{}: {}\n'.format(convert(target, 2, num_groups), c_indices))

def main():
    test()

if __name__ == '__main__':
    main()