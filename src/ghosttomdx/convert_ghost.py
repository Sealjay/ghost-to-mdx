"""
A console script for ingesting a ghost export file,
and exporting mdx files.
"""
from argparse import ArgumentParser
import json
import jsonschema


def convert_ghost_export():
    """Run the conversion using parameters from the command line."""
    # Extract arguments from the command line interface, and make them human readable
    (import_file, export_json_schema_file) = parse_arguments()
    import_file_json = import_json_file(import_file)
    export_json_schema = import_json_file(export_json_schema_file)
    try:
        jsonschema.validate(export_json_schema, import_file_json)
    except jsonschema.exceptions.ValidationError as err:
        print(err)
        raise Exception("The export file does not match the schema file.") from err


def parse_arguments():
    """Read in the arguments from the command line, and return them as a usable object.
    No keyword arguments required.
    Returns:
    arguments -- a python object with the command line arguments passed to the script
    """
    par = ArgumentParser()
    par.add_argument(
        "-f",
        "--import-file",
        type=str,
        default="data/export.json",
        help="Import filename",
    )
    par.add_argument(
        "-s",
        "--export-schema",
        type=str,
        default="data/ghost-4.37.0.schema",
        help="Ghost export schema filename",
    )
    arguments = par.parse_args()
    return arguments.import_file, arguments.export_schema


def import_json_file(file_path):
    with open(file_path) as f:
        return json.load(f)

if __name__ == "__main__":
    convert_ghost_export()
