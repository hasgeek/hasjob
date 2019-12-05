import magic
import mimetypes
import requests
from lxml import html


def test_for_meta_redirections(r):
    mime = magic.from_buffer(r.content, mime=True)
    extension = mimetypes.guess_extension(mime)
    if extension == '.html':
        html_tree = html.fromstring(r.text)
        try:
            attr = html_tree.xpath("//meta[translate(@http-equiv, 'REFSH', 'refsh') = 'refresh']/@content")[0]
            wait, text = attr.split(";")
            if text.lower().startswith("url="):
                url = text[4:].strip()
            else:
                url = text.strip()
            return True, url
        except IndexError:
            return False, None
    else:
        return False, None


def follow_redirections(r, s):
    """
    Recursive function that follows meta refresh redirections if they exist.
    """
    redirected, url = test_for_meta_redirections(r)
    if redirected:
        r = follow_redirections(s.get(url), s)
    return r


def final_url(url):
    s = requests.session()
    r = s.get(url)
    # test for and follow meta redirects
    return follow_redirections(r, s).url


if __name__ == '__main__':
    print(final_url('http://localhost:8000/'))
