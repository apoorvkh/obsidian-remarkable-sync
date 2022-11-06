import os
import json
from glob import glob
import shutil
import fitz

from .utils import uuidgen, dtms


def get_relative_path(metadata, uuid):
    if metadata[uuid]['parent'] == '':
        return metadata[uuid]['visibleName']
    return os.path.join(
        get_relative_path(metadata, metadata[uuid]['parent']),
        metadata[uuid]['visibleName']
    )


def filetree(remarkable_dir):
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
        rel_path = get_relative_path(metadata, uuid)
        if metadata[uuid]['type'] == 'CollectionType':
            collections[rel_path] = uuid
        elif metadata[uuid]['type'] == 'DocumentType':
            documents[rel_path] = uuid

    return collections, documents


def makedirs(remarkable_dir, newdir, collections):
    if newdir in collections:
        return collections
    
    parent = os.path.dirname(newdir)
    visible_name = os.path.basename(newdir)

    if parent != '':
        collections = makedirs(remarkable_dir, parent, collections)

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


def import_pdf(
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

    collections = makedirs(remarkable_dir, parent_path, collections)
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
