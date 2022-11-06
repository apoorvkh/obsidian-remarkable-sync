import os
import json
from glob import glob
from uuid import uuid4
from datetime import datetime
import shutil
import tempfile
import pathlib
import argparse
import fitz
from contextlib import contextmanager


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

def remarkable_get_relative_path(metadata, uuid):
    if metadata[uuid]['parent'] == '':
        return metadata[uuid]['visibleName']
    return os.path.join(
        remarkable_get_relative_path(metadata, metadata[uuid]['parent']),
        metadata[uuid]['visibleName']
    )

def remarkable_filetree(remarkable_dir):
    ## Load metadata of existing remarkable files

    metadata = {}
    for fpath in glob(os.path.join(remarkable_dir, '*.metadata')):
        uuid = os.path.splitext(os.path.basename(fpath))[0]
        meta = json.load(open(fpath, 'r'))
        if meta['parent'] == 'trash': continue
        metadata[uuid] = meta

    ## Load paths of existing remarkable directories and files

    collections = {}
    documents = {}

    for uuid in metadata.keys():
        rel_path = remarkable_get_relative_path(metadata, uuid)
        if metadata[uuid]['type'] == 'CollectionType':
            collections[rel_path] = uuid
        elif metadata[uuid]['type'] == 'DocumentType':
            documents[rel_path] = uuid

    return collections, documents

def uuidgen(): return str(uuid4())

def dtms(): return str(int(datetime.now().timestamp() * 1000))

def remarkable_makedirs(remarkable_dir, newdir, collections):
    if newdir in collections:
        return collections
    
    parent = os.path.dirname(newdir)
    visible_name = os.path.basename(newdir)

    if parent != '':
        collections = remarkable_makedirs(remarkable_dir, parent, collections)

    dir_uuid = uuidgen()

    json.dump(
        {
            'deleted': False,
            'lastModified': dtms(),
            "metadatamodified": False,
            "modified": False,
            "parent": collections.get(parent, ""),
            "pinned": False,
            "synced": False,
            "type": "CollectionType",
            "version": 0,
            "visibleName": visible_name
        },
        open(os.path.join(remarkable_dir, f'{dir_uuid}.metadata'), 'w')
    )

    json.dump(
        {"tags": []},
        open(os.path.join(remarkable_dir, f'{dir_uuid}.content'), 'w')
    )

    collections[newdir] = dir_uuid
    return collections

def remarkable_import_pdf(
    src_pdf_path, remarkable_dir, dst_rel_path,
    documents, collections, overwrite=False
):
    dst_rel_path_no_ext = os.path.splitext(dst_rel_path)[0]
    if dst_rel_path_no_ext in documents:
        if overwrite:
            doc_uuid = documents[dst_rel_path_no_ext]
            del documents[dst_rel_path_no_ext]
            os.system('rm -r ' + os.path.join(remarkable_dir, f'{doc_uuid}*'))
        else:
            return documents, collections

    visible_name = os.path.basename(dst_rel_path_no_ext)
    parent_path = os.path.dirname(dst_rel_path)

    collections = remarkable_makedirs(remarkable_dir, parent_path, collections)
    parent_uuid = collections.get(parent_path, "")

    doc_uuid = uuidgen()

    shutil.copyfile(src_pdf_path, os.path.join(remarkable_dir, f'{doc_uuid}.pdf'))

    json.dump(
        {
            "deleted": False,
            "lastModified": dtms(),
            "metadatamodified": True,
            "modified": True,
            "parent": parent_uuid,
            "pinned": False,
            "synced": False,
            "type": "DocumentType",
            "version": 0,
            "visibleName": visible_name
        },
        open(os.path.join(remarkable_dir, f'{doc_uuid}.metadata'), 'w')
    )

    with fitz.open(src_pdf_path) as doc:
        num_pages = doc.pageCount

    json.dump(
        {
            "fileType": "pdf",
            "originalPageCount": num_pages,
            "pageCount": num_pages,
            "pages": [uuidgen() for _ in range(num_pages)],
            "redirectionPageMap": list(range(num_pages)),
        },
        open(os.path.join(remarkable_dir, f'{doc_uuid}.content'), 'w')
    )

    documents[dst_rel_path_no_ext] = doc_uuid
    return documents, collections


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--obsidian-dir", type=pathlib.Path, required=True, dest='obsidian_dir')
    parser.add_argument("--obsidian-excludes", type=str, nargs='+', default=['remarkable/**'], dest='obsidian_excludes')
    parser.add_argument("--remarkable-dir", type=pathlib.Path, required=True, dest='remarkable_dir')
    parser.add_argument("--remarkable-prefix", type=pathlib.Path, default='obsidian', dest='remarkable_prefix')
    args = parser.parse_args()

    assert os.path.exists(args.obsidian_dir)
    os.makedirs(args.remarkable_dir, exist_ok=True)

    collections, documents = remarkable_filetree(args.remarkable_dir)

    ## Import PDFs in Obsidian

    obsidian_pdfs = glob_with_exclusions(
        os.path.join(args.obsidian_dir, '**', '*.pdf'),
        [os.path.join(args.obsidian_dir, p) for p in args.obsidian_excludes]
    )

    for pdf_path in obsidian_pdfs:
        rel_path = os.path.relpath(pdf_path, args.obsidian_dir)
        documents, collections = remarkable_import_pdf(
            pdf_path,
            args.remarkable_dir,
            os.path.join(args.remarkable_prefix, rel_path),
            documents, collections
        )

    ## Import Markdown files in Obsidian

    with generate_temporary_path(suffix='.pdf') as blank_pdf:
        blank = fitz.open()
        blank.newPage()
        blank.save(blank_pdf)

        obsidian_mds = glob_with_exclusions(
            os.path.join(args.obsidian_dir, '**', '*.md'),
            [os.path.join(args.obsidian_dir, p) for p in args.obsidian_excludes]
        )

        for md_path in obsidian_mds:
            rel_path = os.path.relpath(md_path, args.obsidian_dir)
            # Convert MD file to PDF
            with generate_temporary_path(suffix='.pdf') as temp_pdf:
                status = os.system(f'pandoc -f markdown-yaml_metadata_block "{md_path}" -t pdf --pdf-engine=tectonic -o {temp_pdf}')
                if status == 0:
                    documents, collections = remarkable_import_pdf(
                        temp_pdf,
                        args.remarkable_dir,
                        os.path.join(args.remarkable_prefix, f'{rel_path}.pdf'),
                        documents, collections,
                        overwrite=True
                    )
                else:
                    print(f'Warning: Unable to convert {md_path} to PDF')
            # Create blank notes doc per MD file
            documents, collections = remarkable_import_pdf(
                blank_pdf,
                args.remarkable_dir,
                os.path.join(args.remarkable_prefix, f'{os.path.splitext(rel_path)[0]}.notes.pdf'),
                documents, collections
            )
