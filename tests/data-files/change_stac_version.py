"""
Script to change the version property of the test files for PySTAC.
This is used when upgrading to a new version of STAC.
"""
import os
import argparse
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('stac_version',
                        metavar='STAC_VERSION',
                        help='The STAC_VERSION to ensure all STAC objects are using.')

    args = parser.parse_args()

    data_files_dir = os.path.dirname(os.path.realpath(__file__))

    # Skip examples directory, which contains version specific STACs...
    dirs_to_check = [x for x in os.listdir(data_files_dir) if x != 'examples']

    for d in dirs_to_check:
        for root, _, files in os.walk(d):
            for fname in files:
                if fname.endswith('.json'):
                    path = os.path.join(root, fname)
                    with open(path) as f:
                        stac_json = json.load(f)
                    if 'stac_version' in stac_json:
                        cur_ver = stac_json['stac_version']
                        if not cur_ver == args.stac_version:
                            print('Changing {} version from {} to {}...'.format(
                                fname, cur_ver, args.stac_version))
                            stac_json['stac_version'] = args.stac_version
                            with open(path, 'w') as f:
                                json.dump(stac_json, f, indent=2)
