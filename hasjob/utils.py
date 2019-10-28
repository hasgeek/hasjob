import re
from random import randint, choice
from coaster.utils import simplify_text

NO_NUM_RE = re.compile('[^0-9]+', re.UNICODE)

LEGAL_SUFFIX_RE = re.compile(r'''
    (  # Common descriptors
    Business\s+Systems|
    Consultancy|
    Consulting|
    Communications|
    Digital\s+Communications|
    Digital\s+Media|
    Digital\s+Services|
    Financial\s+Services|
    Global\s+Services|
    Global\s+Solutions|
    Healthcare|
    India|
    Infotech|
    Info\s+Solutions|
    Innotech|
    Learning|
    Software|
    Software\s+Development|
    Software\s+Labs|
    Software\s+Solutions|
    Software\s+Testing|
    Solutions|
    Technology|
    Technology\s+Solutions|
    Technologies|
    Media|
    )?\s+
    (  # Legal suffixes
    Private\s+Limited|
    Pvt\.?\s+Ltd\.?|
    Private\s+Ltd\.?|
    Pvt\.?\s+Limited|
    P\.?\s+Ltd\.?|
    \(P\)\s+Ltd\.?|
    Ltd\.?|
    Limited|
    LLP|
    Inc\.?|
    LLC\.?|
    )$''', re.VERBOSE | re.IGNORECASE)


def common_legal_names(candidate):
    """
    Attempt to break up a candidate name into common and legal names
    """
    candidate = candidate.strip()
    if LEGAL_SUFFIX_RE.search(candidate):
        legal_name = candidate
        common_name = LEGAL_SUFFIX_RE.sub('', candidate).strip()
        return common_name, legal_name
    else:
        return candidate, None


def string_to_number(value):
    """
    Convert a string containing a formatted number into an integer.
    """
    value = NO_NUM_RE.sub('', value)
    if value:
        return int(value)


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
    return ('0000' + base36encode(randint(0, 60466175)))[-5:]  # 60466175 is 'zzzzz'


def cointoss():
    """
    Return True or False at random, attempting to offset any bias from the underlying
    random number generator using John von Neumann's procedure.
    """
    # From https://en.wikipedia.org/wiki/Fair_coin#Fair_results_from_a_biased_coin
    r1 = r2 = None
    while r1 == r2:
        r1 = choice([True, False])
        r2 = choice([True, False])
    return r1


EMAIL_RE = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,63}\b', re.I)
# From http://www.codinghorror.com/blog/2008/10/the-problem-with-urls.html
URL_RE = re.compile(r'\(?\bhttps?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|]')
PHONE_DETECT_RE = re.compile('(^|[^0-9])([0-9][ .()_-]*){10}($|[^0-9])')


def redactemail(data, message=u'[redacted]'):
    """
    Remove email addresses from the given text, replacing with a redacted message.

    >>> redactemail(u"Send email to test@example.com and you are all set.")
    u'Send email to [redacted] and you are all set.'
    >>> redactemail(u"Send email to test@example.com and you are all set.", '[hidden]')
    u'Send email to [hidden] and you are all set.'
    """
    return EMAIL_RE.sub(message, data)


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
        if css_junk and len(email) > 3:
            third = int(len(email) / 3)
            parts = (email[:third], email[third:third * 2], email[third * 2:])
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


WORDSPLIT_RE = re.compile(r'\W+')
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


def escape_for_sql_like(query):
    r"""
    Escape the '%' and '_' wildcards in SQL LIKE clauses.
    Some SQL dialects respond to '[' and ']', so remove them.

    >>> escape_for_sql_like("query%_[]")
    "query\%\_%"
    """
    return query.replace(u'%', r'\%').replace(u'_', r'\_').replace(u'[', u'').replace(u']', u'') + u'%'


def strip_null(text):
    # Removes null byte from given text
    return text.replace('\x00', '')
