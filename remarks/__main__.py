import os
import pathlib
import argparse
from glob import glob
import json

from remarks import run_remarks, get_relative_path

__prog_name__ = "remarks"
__version__ = "0.1.1"


def main():
    parser = argparse.ArgumentParser(__prog_name__, add_help=False)

    parser.add_argument(
        "input_dir",
        help="xochitl-derived directory that contains *.pdf, *.content, *.metadata, and */*.rm files",
        metavar="INPUT_DIRECTORY",
    )
    parser.add_argument(
        "output_dir",
        help="Base directory for exported (*.pdf, *.png, *.md, and/or *.svg) files",
        metavar="OUTPUT_DIRECTORY",
    )
    parser.add_argument(
        "--uuid",
        type=str,
        default=None,
        help="UUID of specific file to update",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Show version number",
        version="%(prog)s {version}".format(version=__version__),
    )
    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message",
    )

    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir

    if not pathlib.Path(input_dir).exists():
        parser.error(f'Directory "{input_dir}" does not exist.')

    if not pathlib.Path(output_dir).is_dir():
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    metadata = {}

    for fpath in glob(os.path.join(input_dir, '*.metadata')):
        uuid = os.path.splitext(os.path.basename(fpath))[0]
        meta = json.load(open(fpath, 'r'))
        if meta['parent'] == 'trash': continue
        metadata[uuid] = meta

    if args.uuid is None:
        # Make directories
        for uuid in metadata.keys():
            if metadata[uuid]['type'] == 'CollectionType':
                os.makedirs(os.path.join(output_dir, get_relative_path(metadata, uuid)), exist_ok=True)
        # Produce annotated PDFs
        for uuid in metadata.keys():
            if metadata[uuid]['type'] == 'DocumentType':
                run_remarks(input_dir, uuid, os.path.join(output_dir, get_relative_path(metadata, uuid) + '.pdf'))
    else:
        uuid = args.uuid
        rel_path = get_relative_path(metadata, uuid)
        os.makedirs(os.path.join(output_dir, rel_path), exist_ok=True)
        run_remarks(input_dir, uuid, os.path.join(output_dir, rel_path + '.pdf'))


if __name__ == "__main__":
    main()
