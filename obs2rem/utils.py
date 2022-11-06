import os
from uuid import uuid4
from datetime import datetime
from glob import glob
import tempfile
from contextlib import contextmanager
import fitz


def uuidgen():
    return str(uuid4())

def dtms():
    return str(int(datetime.now().timestamp() * 1000))

def glob_with_exclusions(query_pathname, excluded_pathnames):
    query = set(glob(query_pathname, recursive=True))
    for ep in excluded_pathnames:
        query -= set(glob(ep, recursive=True))
    return list(query)

@contextmanager
def generate_temporary_path(*args, **kwds):
    t = tempfile.NamedTemporaryFile(*args, **kwds)
    temp_path = t.name
    t.close()
    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def create_blank_pdf(dst):
    blank = fitz.open()
    blank.newPage()
    blank.save(dst)
