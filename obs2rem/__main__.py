import os
import argparse
import pathlib

from .utils import glob_with_exclusions, generate_temporary_path, create_blank_pdf
from . import rem_utils


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--obsidian-dir", type=pathlib.Path, required=True, dest='obsidian_dir')
    parser.add_argument("--obsidian-excludes", type=str, nargs='+', default=['_remarkable/**'], dest='obsidian_excludes')
    parser.add_argument("--remarkable-dir", type=pathlib.Path, required=True, dest='remarkable_dir')
    parser.add_argument("--remarkable-prefix", type=pathlib.Path, default='obsidian', dest='remarkable_prefix')
    args = parser.parse_args()

    assert os.path.exists(args.obsidian_dir)
    os.makedirs(args.remarkable_dir, exist_ok=True)

    collections, documents = rem_utils.filetree(args.remarkable_dir)

    ## Import PDFs in Obsidian

    obsidian_pdfs = glob_with_exclusions(
        os.path.join(args.obsidian_dir, '**', '*.pdf'),
        [os.path.join(args.obsidian_dir, p) for p in args.obsidian_excludes]
    )

    for pdf_path in obsidian_pdfs:
        rel_path = os.path.relpath(pdf_path, args.obsidian_dir)
        documents, collections = rem_utils.import_pdf(
            pdf_path,
            args.remarkable_dir,
            os.path.join(args.remarkable_prefix, rel_path),
            documents, collections
        )

    ## Import Markdown files in Obsidian

    with generate_temporary_path(suffix='.pdf') as blank_pdf_path:
        create_blank_pdf(blank_pdf_path)

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
                    documents, collections = rem_utils.import_pdf(
                        temp_pdf,
                        args.remarkable_dir,
                        os.path.join(args.remarkable_prefix, f'{rel_path}.pdf'),
                        documents, collections,
                        overwrite=True
                    )
                else:
                    print(f'Warning: Unable to convert {md_path} to PDF')
            # Create blank notes doc per MD file
            documents, collections = rem_utils.import_pdf(
                blank_pdf_path,
                args.remarkable_dir,
                os.path.join(args.remarkable_prefix, f'{os.path.splitext(rel_path)[0]}.notes.pdf'),
                documents, collections
            )
