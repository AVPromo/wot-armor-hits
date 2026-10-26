# -*- coding: utf-8 -*-
"""Render the docs images: a screenshot of each page by headless Microsoft Edge, at 2x.

    C:\\Python27\\python.exe docs/render.py   -> docs/install-guide.png from docs/install-guide.html
"""
import os
import subprocess
import sys

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
EDGE_PATHS = (
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
)
# The pages: (source, image, width and height of the page in CSS pixels).
PAGES = (
    ('install-guide.html', 'install-guide.png', 1200, 900),
)
SCALE = 2


def edgePath():
    for path in EDGE_PATHS:
        if os.path.isfile(path):
            return path
    sys.exit('Microsoft Edge not found')


def render(edge, source, image, width, height):
    url = 'file:///' + os.path.join(DOCS_DIR, source).replace('\\', '/')
    subprocess.check_call([
        edge, '--headless=new', '--disable-gpu', '--hide-scrollbars',
        '--force-device-scale-factor=%d' % SCALE, '--window-size=%d,%d' % (width, height),
        '--screenshot=' + os.path.join(DOCS_DIR, image), url,
    ])


def main():
    edge = edgePath()
    for source, image, width, height in PAGES:
        render(edge, source, image, width, height)


if __name__ == '__main__':
    main()
