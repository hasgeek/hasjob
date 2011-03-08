from random import randint

#: This code adapted from http://en.wikipedia.org/wiki/Base_36#Python%5FConversion%5FCode
def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    """
    Convert positive integer to a base36 string.
    
    >>> base36encode(0)
    '0'
    >>> base36encode(60466175)
    'zzzzz'
    >>> base36encode(60466176)
    '100000'
    """
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')
    # Special case for zero
    if number == 0:
        return '0'
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = - number
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36


def base36decode(number):
    return int(number, 36)

def random_long_key():
    return base36encode(randint(1000000000000000,
                                10000000000000000))

def random_hash_key():
    """
    Returns a random key that is exactly five letters long.
    
    >>> for attempt in range(1000):
    ...     if len(random_hash_key()) != 5:
    ...         print "Length is not 5!"
    """
    base = base36encode(randint(0, 60466175)) # 60466175 is 'zzzzz'
    if len(base) < 5:
        base = '0'*(5-len(base))+base
    return base

if __name__ == '__main__':
    import doctest
    doctest.testmod()
