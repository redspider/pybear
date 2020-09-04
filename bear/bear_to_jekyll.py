#
# Copyright (c) 2020  Richard Clark
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
I really wanted to call this "inthewoods.py" but it seemed likely to cause confusion.
"""
import argparse
import os.path, os
import re
import shutil

import bear
import sys


def title_to_filename(path, title):
    """
    We build a simple filename from the title - i.e. "These Cats" becomes "these_cats.md". We do
    not check for existence, as we may be doing an overwrite deliberately.
    """

    name = re.sub(r'[^a-z0-9]','_',title.lower())
    return os.path.join(path, name)


def main():
    parser = argparse.ArgumentParser(description = 'Export Bear posts as Jekyll-compatible markdown')
    parser.add_argument('output', type = str,
                        help = 'directory to output to')
    parser.add_argument('--tag', type = str, action='append', help='Tag to export, you can specify multiple times. If no tags are specified all posts will be exported')
    parser.add_argument('--html', action = "store_true", help = "render as html")
    args = parser.parse_args()

    full_path = os.path.join(os.getcwd(), args.output)

    # Check directory exists
    if not os.path.isdir(full_path):
        print("The given output directory {} does not exist".format(full_path))
        sys.exit(1)

    # Open Bear database
    b = bear.Bear()

    # Check tags
    if args.tag:
        notes = []
        for tag in args.tag:
            t = b.tag_by_title(tag)
            if not t:
                print("The given tag '{}' does not exist - note they're case sensitive".format(tag))
                sys.exit(1)
            for note in t.notes():
                notes.append(note)
    else:
        notes = b.notes()

    # Iterate through all notes
    for note in notes:
        # Create a suitable filename
        filename = title_to_filename(full_path, note.title) + '.md'

        # Write out the post
        with open(filename, 'w', encoding = 'utf8') as f:

            f.write("""---
    title: {}
    date: {}
    tags: {}
    uuid: {}
    ---
    {}""".format(note.title, note.created.strftime('%Y-%m-%d %H:%M:%S +0000'), ' '.join([t.title for t in note.tags()]), note.id, note.text))

            # Images to copy
            for image in note.images():
                if image.exists():
                    # Figure out target path for image
                    target_path = os.path.join(full_path, image.uri)
                    # Make dir
                    os.makedirs(os.path.dirname(target_path), exist_ok = True)
                    # Copy file
                    shutil.copyfile(image.path, target_path)


if __name__ == "__main__":
    main()
