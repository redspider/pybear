"""
This does a terrible job of markdown rendering, but it's better than nothing if you want to start off.
"""
import argparse
import os.path, os
import re
import shutil

import bear
import sys
import markdown
from markdown.inlinepatterns import Pattern
from markdown.util import etree
from markdown.extensions import Extension


class ImagePattern(Pattern):
    """
    Bear uses it's own special image tag format, it's not clear why - maybe to avoid conflicting with regular
    Markdown image tags. We can handle it though.
    """
    def handleMatch(self, m):
        el = etree.Element('img')
        el.attrib['src'] = m.group(2)
        return el


class ImageExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('bearimage', ImagePattern(r'\[image:([^\]]+)\]', md),"<reference")


def title_to_filename(path, title):
    """
    We build a simple filename from the title - i.e. "These Cats" becomes "these_cats.md". We do
    not check for existence, as we may be doing an overwrite deliberately.
    """

    name = re.sub(r'[^a-z0-9]', '_', title.lower())
    return os.path.join(path, name)


def get_css():
    """
    We hunt down the Bear app and grab their CSS that is normally used for HTML export. This is going to be pretty
    damn fragile, but I'd rather do that than include their code in here without permission.
    """
    paths = ['/Applications/Bear.app/Contents/Resources/HTMLExport.css',
             '/Applications/Bear 4.app/Contents/Resources/HTMLExport.css']

    for path in paths:
        if os.path.exists(path):
            return open(path, 'r').read()

    return '<!-- Could not find style file, see get_css() in bear_to_html.py -->'


def main():
    parser = argparse.ArgumentParser(description = 'Export Bear posts as Jekyll-compatible markdown')
    parser.add_argument('output', type = str,
                        help = 'directory to output to')
    parser.add_argument('--tag', type = str, action = 'append',
                        help = 'Tag to export, you can specify multiple times. If no tags are specified all posts will be exported')
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

    css = get_css()

    # Iterate through all notes
    for note in notes:
        # Create a suitable filename
        filename = title_to_filename(full_path, note.title) + '.html'

        # Write out the post
        with open(filename, 'w', encoding = 'utf8') as f:
            content = markdown.markdown(note.text,
                                      extensions = [
                                          ImageExtension(),
                                          'markdown.extensions.nl2br',
                                          'markdown.extensions.fenced_code'
                                      ])
            html = """<html>
    <head>
        <title>{}</title>
    </head>
    <body>
        <div class="note-wrapper">
        {}
        </div>
        <style>{}</style>
    </body>
</html>
""".format(note.title, content, css)
            f.write(html)

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
