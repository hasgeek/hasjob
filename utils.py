import string
from random import randint
from uuid import uuid4
from base64 import b64encode
from BeautifulSoup import BeautifulSoup, Comment

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
    return ('0000' + base36encode(randint(0, 60466175)))[-5:] # 60466175 is 'zzzzz'

def newid():
    """
    Return a new random id that is exactly 22 characters long.
    """
    return b64encode(uuid4().bytes, altchars=',-').replace('=', '')


VALID_TAGS = {'strong': [],
              'em': [],
              'p': [],
              'ol': [],
              'ul': [],
              'li': [],
              'br': [],
              'a': ['href', 'title']
              }

def sanitize_html(value, valid_tags=VALID_TAGS):
    """
    Strips unwanted markup out of HTML.
    """
    soup = BeautifulSoup(value)
    comments = soup.findAll(text=lambda text:isinstance(text, Comment))
    [comment.extract() for comment in comments]
    # Some markup can be crafted to slip through BeautifulSoup's parser, so
    # we run this repeatedly until it generates the same output twice.
    newoutput = soup.renderContents()
    while 1:
        oldoutput = newoutput
        soup = BeautifulSoup(newoutput)
        for tag in soup.findAll(True):
            if tag.name not in valid_tags:
                tag.hidden = True
            else:
                tag.attrs = [(attr, value) for attr, value in tag.attrs if attr in valid_tags[tag.name]]
        newoutput = soup.renderContents()
        if oldoutput == newoutput:
            break
    return unicode(newoutput, 'utf-8')


def simplify_text(text):
    """
    Simplify text to allow comparison.
    
    >>> simplify_text("Awesome Coder wanted at Awesome Company")
    'awesome coder wanted at awesome company'
    >>> simplify_text("Awesome Coder, wanted  at Awesome Company! ")
    'awesome coder wanted at awesome company'
    >>> simplify_text(u"Awesome Coder, wanted  at Awesome Company! ")
    u'awesome coder wanted at awesome company'
    """
    if isinstance(text, unicode):
        text = unicode(text.encode('utf-8').translate(string.maketrans("",""), string.punctuation).lower(), 'utf-8')
    else:
        text = text.translate(string.maketrans("",""), string.punctuation).lower()
    return " ".join(text.split())


if __name__ == '__main__':
    import doctest
    doctest.testmod()
