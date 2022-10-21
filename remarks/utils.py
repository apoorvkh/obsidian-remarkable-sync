import os
from glob import glob
import json

from .conversion.parsing import (
    get_pdf_to_device_ratio,
    get_rescaled_device_dims,
)


def get_relative_path(uuid):
    if metadata[uuid]['parent'] == '':
        return metadata[uuid]['visibleName']
    return os.path.join(get_relative_path(metadata[uuid]['parent']), metadata[uuid]['visibleName'])

def stem(x):
   return os.path.splitext(os.path.basename(x))[0]

def get_pdf(input_path, uuid):
    return os.path.join(input_path, uuid + '.pdf')

def get_pdf_page_dims(doc, page_idx=0):
    page = doc.loadPage(page_idx)
    return page.rect.width, page.rect.height

def get_rescaled_page_dims(pdf_src, page_idx=0):
    pdf_w, pdf_h = get_pdf_page_dims(pdf_src, page_idx)
    scale = get_pdf_to_device_ratio(pdf_w, pdf_h)
    rm_w_rescaled, rm_h_rescaled = get_rescaled_device_dims(scale)
    return rm_w_rescaled, rm_h_rescaled

def get_pages(input_path, uuid):
    content = json.load(open(
        os.path.join(input_path, uuid + '.content'), 'r'))
    if "redirectionPageMap" in content:
        return content["pages"], content["redirectionPageMap"]
    return content["pages"]

def get_rm_files(input_path, uuid):
    return list(glob(os.path.join(input_path, uuid, '*.rm')))

def get_highlights_files(input_path, uuid, rm_files):
    return [
        os.path.join(input_path, uuid + '.highlights', stem(rmf) + '.json')
        for rmf in rm_files
    ]
