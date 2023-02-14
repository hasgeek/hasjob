from werkzeug.datastructures import FileStorage

from hasjob.uploads import image_extension, process_image


def test_image_extension():
    # Common extensions
    assert image_extension('JPEG') == '.jpg'
    assert image_extension('JPEG2000') == '.jp2'
    assert image_extension('GIF') == '.gif'
    assert image_extension('PNG') == '.png'
    # Uncommon extensions
    assert image_extension('TIFF') == '.tif'
    assert image_extension('WEBP') == '.webp'


def test_process_image(shared_datadir):
    for filename in (
        'sample-jpg.jpg',
        'sample-jpg.png',
        'sample-png-rgba.png',
        'sample-png-rgba.jpg',
    ):
        with (shared_datadir / filename).open('rb') as f:
            processed = process_image(FileStorage(f, filename=filename))
            assert processed is not None
