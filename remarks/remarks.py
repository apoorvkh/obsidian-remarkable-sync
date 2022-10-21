import os

import fitz  # PyMuPDF

from .conversion.parsing import (
    parse_rm_file,
    get_pdf_to_device_ratio,
    rescale_parsed_data,
)
from .conversion.drawing import draw_pdf
from .utils import *


def run_remarks(input_path, uuid, output_path):

    # Open PDF if exists, else blank single-page A4 pdf

    pdf_path = get_pdf(input_path, uuid)
    if os.path.exists(pdf_path):
        pdf_src = fitz.open(pdf_path)
        pages, redirection_page_map = get_pages(input_path, uuid)
    else:
        pdf_src = fitz.open()
        pdf_src.new_page()
        pages = get_pages(input_path, uuid)
        redirection_page_map = [0] + [-1 for _ in range(len(pages) - 1)]

    # Insert blank pages (w/ dimension of page 0) where needed

    blank_doc = fitz.open()
    rm_w_rescaled, rm_h_rescaled = get_rescaled_page_dims(pdf_src, page_idx=0)
    blank_doc.newPage(width=rm_w_rescaled, height=rm_h_rescaled)

    for i, page_idx in enumerate(redirection_page_map):
        if page_idx == -1:
            pdf_src.insertPDF(blank_doc, start_at=i)

    blank_doc.close()

    # Draw lines on PDF

    rm_files = get_rm_files(input_path, uuid)
    highlights_files = get_highlights_files(input_path, uuid, rm_files)

    for rm_file, highlights_file in zip(rm_files, highlights_files):
        rm_uuid = stem(rm_file)
        if rm_uuid not in pages: continue
        page_idx = pages.index(rm_uuid)

        pdf_w, pdf_h = get_pdf_page_dims(pdf_src, page_idx=page_idx)
        scale = get_pdf_to_device_ratio(pdf_w, pdf_h)

        highlights, scribbles = parse_rm_file(rm_file, highlights_file)

        parsed_data = rescale_parsed_data(
            {"layers": highlights["layers"] + scribbles["layers"]},
            scale
        )

        draw_pdf(parsed_data, pdf_src[page_idx], inplace=True)

    # Save PDF

    pdf_src.save(output_path)
    pdf_src.close()
