"""
Script to change the version property of the test files for PySTAC.
This is used when upgrading to a new version of STAC.
"""
import os
import re
import argparse
import json

import pystac as ps

TARGET_VERSION = ps.get_stac_version()


def migrate(path: str) -> None:
    try:
        with open(path) as f:
            stac_json = json.load(f)
    except json.decoder.JSONDecodeError:
        print(f'Cannot read {path}')
        raise

    if 'stac_version' in stac_json:
        cur_ver = stac_json['stac_version']
        #if not cur_ver == TARGET_VERSION:
        if True:
            print('  - Migrating {} from {} to {}...'.format(path, cur_ver, TARGET_VERSION))
            obj = ps.read_dict(stac_json, href=path)
            migrated = obj.to_dict(include_self_link=False)
            with open(path, 'w') as f:
                json.dump(migrated, f, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--file', metavar='FILE', help='Only migrate this specific file.')

    args = parser.parse_args()

    if args.file:
        migrate(os.path.abspath(args.file))
    else:

        data_files_dir = os.path.dirname(os.path.realpath(__file__))

        # Skip examples directory, which contains version specific STACs...
        dirs_to_check = [
            os.path.join(data_files_dir, x) for x in os.listdir(data_files_dir) if x != 'examples'
        ]

        for d in dirs_to_check:
            print(f'checking in {d}..')
            for root, _, files in os.walk(d):
                # Skip directories with a version tag
                if re.match(r".*-v\d.*", root):
                    continue
                for fname in files:
                    if fname.endswith('.json'):
                        path = os.path.join(root, fname)
                        migrate(path)
