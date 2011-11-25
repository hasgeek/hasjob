import string
import re
from random import randint
from uuid import uuid4
from base64 import b64encode
from hashlib import md5
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


def md5sum(data):
    """
    Return md5sum of data as a 32-character string.

    >>> md5sum('random text')
    'd9b9bec3f4cc5482e7c5ef43143e563a'
    >>> md5sum(u'random text')
    'd9b9bec3f4cc5482e7c5ef43143e563a'
    >>> len(md5sum('random text'))
    32
    """
    return md5(data).hexdigest()


def get_email_domain(email):
    """
    Return the domain component of an email address.

    >>> get_email_domain('jace@pobox.com')
    'pobox.com'
    >>> get_email_domain('jace+test@pobox.com')
    'pobox.com'
    >>> get_email_domain('foobar')
    """
    try:
        return email.split('@')[1]
    except IndexError:
        return None


VALID_TAGS = {'strong': [],
              'em': [],
              'p': [],
              'ol': [],
              'ul': [],
              'li': [],
              'br': [],
              'a': ['href', 'title', 'target']
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


EMAIL_RE = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b', re.I)

def scrubemail(data, rot13=False, css_junk=None):
    """
    Convert email addresses in text into HTML links,
    and optionally obfuscate them with ROT13 and empty CSS classes,
    to hide from spambots.

    >>> scrubemail(u"Send email to test@example.com and you are all set.")
    u'Send email to <a href="mailto:test@example.com">test@example.com</a> and you are all set.'
    >>> scrubemail(u"Send email to test@example.com and you are all set.", rot13=True)
    u'Send email to <a class="rot13" data-href="znvygb:grfg@rknzcyr.pbz">test@example.com</a> and you are all set.'
    >>> scrubemail(u"Send email to test@example.com and you are all set.", rot13=True, css_junk='z')
    u'Send email to <a class="rot13" data-href="znvygb:grfg@rknzcyr.pbz">test&#64;<span class="z">no</span>examp<span class="z">spam</span>le.com</a> and you are all set.'
    >>> scrubemail(u"Send email to test@example.com and you are all set.", rot13=False, css_junk=('z', 'y'))
    u'Send email to <a href="mailto:test@example.com"><span class="y">test&#64;</span><span class="z">no</span><span class="y">examp</span><span class="z">spam</span><span class="y">le.com</span></a> and you are all set.'
    """
    def convertemail(m):
        aclass = ' class="rot13"' if rot13 else ''
        email = m.group(0)
        link = 'mailto:' + email
        if rot13:
            link = link.decode('rot13')
        if css_junk and len(email)>3:
            third = int(len(email) / 3)
            parts = (email[:third], email[third:third*2], email[third*2:])
            if isinstance(css_junk, (tuple, list)):
                css_dirty, css_clean = css_junk
                email = '<span class="%s">%s</span><span class="%s">no</span>'\
                    '<span class="%s">%s</span><span class="%s">spam</span>'\
                    '<span class="%s">%s</span>' % (
                    css_clean, parts[0], css_dirty, css_clean, parts[1],
                    css_dirty, css_clean, parts[2])
            else:
                email = '%s<span class="%s">no</span>%s<span class="%s">spam</span>%s' % (
                    parts[0], css_junk, parts[1], css_junk, parts[2])
            email = email.replace('@', '&#64;')
        if rot13:
            return '<a%s data-href="%s">%s</a>' % (aclass, link, email)
        else:
            return '<a%s href="%s">%s</a>' % (aclass, link, email)
    data = EMAIL_RE.sub(convertemail, data)
    return data


WORDSPLIT_RE = re.compile('\W+')
TAGSPLIT_RE = re.compile('<.*?>')

def striptags(text):
    """
    Remove HTML/XML tags from text, inserting spaces in their place:

    >>> striptags('<h1>title</h1>')
    ' title '
    >>> striptags('plain text')
    'plain text'
    >>> striptags(u'word<br>break')
    u'word break'
    """
    return TAGSPLIT_RE.sub(' ', text)


def getwords(text):
    """
    Get words in text by splitting text along punctuation
    and stripping out the punctuation:

    >>> getwords('this is some text.')
    ['this', 'is', 'some', 'text']
    >>> getwords('and/or')
    ['and', 'or']
    >>> getwords('one||two')
    ['one', 'two']
    >>> getwords("does not is doesn't")
    ['does', 'not', 'is', 'doesn', 't']
    >>> getwords(u'hola unicode!')
    [u'hola', u'unicode']
    """
    result = WORDSPLIT_RE.split(text)
    # Blank tokens will only be at beginning or end of text.
    if result[0] == '':
        result.pop(0)
    if result and result[-1] == '':
        result.pop(-1)
    return result


def get_word_bag(text):
    """
    Return a string containing all unique words in the given text, in alphabetical order.
    
    >>> get_word_bag("This is a piece\tof text with this extra bit!")
    'a bit extra is of piece text this with'
    """
    words = list(set(simplify_text(striptags(text)).split(' ')))
    words.sort()
    return " ".join(words)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
