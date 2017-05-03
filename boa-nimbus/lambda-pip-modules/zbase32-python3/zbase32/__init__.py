#!/usr/bin/env python3
"""
Command line zbase32 encoder and decoder.
See http://philzimmermann.com/docs/human-oriented-base-32-encoding.txt
 
Please note that scrip loads the data in memory.
 
Copyright: Tocho Tochev <tocho AT tochev DOT net>
Licence: MIT
"""
 
import argparse
import functools
import itertools
import sys
 
 
ALPTHABET = b"ybndrfg8ejkmcpqxot1uwisza345h769"
 
 
def encode(bs):
    """Encode bytes bs using zbase32 encoding.
 
    Returns: bytearray
 
    >>> for i in range(20): assert(decode(encode(b'a'*i)) == b'a'*i)
    >>> encode(b'\\xd4z\\x04') == b'4t7ye'
    True
    """
    result = bytearray()
    for word in itertools.zip_longest(*([iter(bs)] * 5)):
        padding_count = word.count(None)
        n = functools.reduce(lambda x,y: (x<<8) + (y or 0), word, 0)
        for i in range(0, (40 - 8 * padding_count), 5):
            result.append(ALPTHABET[(n >> (35 - i)) & 0x1F])
    return result
 
 
def decode(bs):
    """Decode zbase32 encoded bytes.
 
    Returns: bytearray
 
    >>> decode(b'4t7ye') == b'\\xd4z\\x04'
    True
    """
    result = bytearray()
    reversed_alphabet = dict(map(reversed, enumerate(ALPTHABET)))
    reversed_alphabet[None] = 0
    bs = filter(lambda c: c not in b'\r\n', bs)
    try:
        for word in itertools.zip_longest(*([iter(bs)] * 8)):
            padding_count = word.count(None)
            n = functools.reduce(lambda x,y: (x<<5) + reversed_alphabet[y],
                       word,
                       0)
            for i in range(32, 5 * padding_count - 1, -8):
                result.append((n >> i) & 0xFF)
    except KeyError:
        raise ValueError("The input does not seem to be valid zbase32.")
    return result
 
 
def main():
    parser = argparse.ArgumentParser(
        description="zbase32 encoder and decoder"
    )
    parser.add_argument('--decode', '-d', action='store_true')
    parser.add_argument('file', nargs='?', type=argparse.FileType('rb'),
                        default=sys.stdin.buffer)
    args = parser.parse_args()
 
    if not args.decode:
        sys.stdout.buffer.write(encode(args.file.read()))
        sys.stdout.buffer.write(b'\n')
    else:
        sys.stdout.buffer.write(decode(args.file.read()))
 
 
if __name__ == '__main__':
    main()