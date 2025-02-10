#! /usr/bin/env python3

import logging
import os
import re
from pathlib import Path

try:
    import tqdm
except ImportError:
    pass


class ModelCleaner:

    _model_re = re.compile(r"^(\s)\(model\s\"(.*)\"")

    def __init__(self, existing_list: set[str], libs_dir: Path, output_dir: Path):
        self.existing_list = existing_list
        self.libs_dir = libs_dir
        self.output_dir = output_dir

        self.removed = 0
        self.processed = 0
        self.processed_libs = 0

    def clean_models(self):

        # for each .prtty dir in the base dir
        pretty_dirs = [
            d for d in self.libs_dir.iterdir() if d.is_dir() and d.suffix == ".pretty"
        ]

        if "tqdm" in globals():
            pretty_dirs = tqdm.tqdm(pretty_dirs)

        for pretty_dir in pretty_dirs:

            footprints = [
                f
                for f in pretty_dir.iterdir()
                if f.is_file() and f.suffix == ".kicad_mod"
            ]

            for footprint in footprints:
                rel_path = footprint.relative_to(self.libs_dir)
                self._clean_models_in_file(rel_path)

            self.processed_libs += 1

    def _model_exists(self, model_value: str) -> bool:

        # strip the prefix and extension
        # ${KICAD8_3DMODEL_DIR}/Package_TO_SOT_THT.3dshapes/TO-92S-2.wrl
        # -> Package_TO_SOT_THT.3dshapes/TO-92S-2
        model_value = model_value.split("/", maxsplit=1)[1]
        model_value = model_value.rsplit(".", maxsplit=1)[0]
        return model_value in self.existing_list

    def _clean_models_in_file(self, rel_path: str):

        res = []
        removed = False

        with open(os.path.join(self.libs_dir, rel_path), "r") as f:
            res = []
            close_string = None
            for line in f:

                # skip lines until the end of the matching string
                if close_string is not None:
                    if line.startswith(close_string):
                        close_string = None

                elif m := re.match(self._model_re, line):
                    indent = m.group(1)
                    model = m.group(2)

                    if not self._model_exists(model):
                        logging.debug(f"Removing model from: {rel_path}")
                        removed = True
                        close_string = indent + ")"
                    else:
                        # keep the model
                        res.append(line)
                else:
                    res.append(line)

        if removed:
            self.removed += 1

            out_file = os.path.join(self.output_dir, rel_path)
            os.makedirs(os.path.dirname(out_file), exist_ok=True)

            with open(out_file, "w") as f:
                f.writelines(res)

        self.processed += 1


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Clean non-existing 3D models fomr footprints"
    )

    # fmt: off
    parser.add_argument(
        "-e", "--existing", type=str,
        help="Path to list of existing 3D models"
    )
    parser.add_argument(
        "-d", "--directory", type=str, required=True,
        help="Path to directory of footprint libraries",
    )
    parser.add_argument(
        "-o", "--out-directory", type=str,
        help="Path to write the output to (or in place if not given)",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="Verbose output, use -vv for more debug",
    )
    # fmt: on

    args = parser.parse_args()

    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    existing = set()

    with open(args.existing, "r") as f:
        for line in f:
            existing.add(line.strip())

    if args.out_directory is not None:
        os.makedirs(args.out_directory, exist_ok=True)
    else:
        args.out_directory = args.directory

    cleaner = ModelCleaner(existing, Path(args.directory), Path(args.out_directory))

    cleaner.clean_models()

    logging.info(f"3D model dir has {len(existing)} models")
    logging.info(f"Processed {cleaner.processed} footprints")
    logging.info(f"Processed {cleaner.processed_libs} libraries")
    logging.info(f"Removed models from {cleaner.removed} footprints")
    logging.info(f"Kept models in {cleaner.processed - cleaner.removed} footprints")
    logging.info(f"Output written to {args.out_directory}")
