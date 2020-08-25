"""
Script to download the examples from the stac-spec repository.
This is used when upgrading to a new version of STAC.
"""
import os
import argparse
import json
from tempfile import TemporaryDirectory
from subprocess import call
from urllib.error import HTTPError

import pystac
from pystac.serialization import identify_stac_object, STACObjectType


def remove_bad_collection(js):
    links = js.get('links')
    if links is not None:
        filtered_links = []
        for link in links:
            rel = link.get('rel')
            if rel is not None and rel == 'collection':
                href = link['href']
                try:
                    json.loads(pystac.STAC_IO.read_text(href))
                    filtered_links.append(link)
                except (HTTPError, FileNotFoundError, json.decoder.JSONDecodeError):
                    print('===REMOVING UNREADABLE COLLECTION AT {}'.format(href))
            else:
                filtered_links.append(link)
        js['links'] = filtered_links
    return js


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get examples from the stac-spec repo.')
    parser.add_argument(
        'previous_version',
        metavar='PREVIOUS_VERSION',
        help='The previous STAC_VERSION that examples have already been pulled from.')

    args = parser.parse_args()

    stac_repo = 'https://github.com/radiantearth/stac-spec'
    stac_spec_tag = 'v{}'.format(pystac.get_stac_version())

    examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'examples'))

    with TemporaryDirectory() as tmp_dir:
        call(['git', 'clone', '--depth', '1', '--branch', stac_spec_tag, stac_repo, tmp_dir])

        example_dirs = []
        for root, _, _ in os.walk(tmp_dir):
            example_dirs.append(os.path.join(root))

        example_csv_lines = set([])

        for example_dir in example_dirs:
            for root, _, files in os.walk(example_dir):
                for fname in files:
                    if fname.endswith('.json'):
                        path = os.path.join(root, fname)
                        with open(path) as f:
                            try:
                                js = json.loads(f.read())
                            except json.decoder.JSONDecodeError:
                                # Account for bad examples that can't be parsed.
                                js = {}
                            example_version = js.get('stac_version')
                        if example_version is not None and \
                           example_version > args.previous_version:
                            relpath = '{}/{}'.format(pystac.get_stac_version(),
                                                     path.replace('{}/'.format(tmp_dir), ''))
                            target_path = os.path.join(examples_dir, relpath)

                            print('Creating example at {}'.format(target_path))

                            info = identify_stac_object(js)

                            # Handle the case where there are collection links that
                            # don't exist.
                            if info.object_type == STACObjectType.ITEM:
                                js = remove_bad_collection(js)

                            d = os.path.dirname(target_path)
                            if not os.path.isdir(d):
                                os.makedirs(d)

                            with open(target_path, 'w') as f:
                                f.write(json.dumps(js, indent=4))

                            # Add info to the new example-info.csv lines
                            line_info = [
                                relpath, info.object_type, example_version,
                                '|'.join(info.common_extensions), '|'.join(info.custom_extensions)
                            ]
                            line = '"{}"'.format('","'.join(line_info))
                            example_csv_lines.add(line)

        # Write the new example-info.csv lines into a temp file for inspection
        with open(os.path.join(examples_dir, 'examples-info-NEW.csv'), 'w') as f:
            txt = '\n'.join(sorted(example_csv_lines))
            f.write(txt)
