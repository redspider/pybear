#
# Copyright (c) 2020  Richard Clark
# Copyright (c) 2020  Joanna Rutkowska
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

import os.path
import re
import sqlite3
import datetime

__version__ = '0.0.20200629'

def timestamp_to_datetime(s):
    '''
    Convert a Core Data timestamp to a datetime. They're all a float of seconds
    since 1 Jan 2001. We calculate the seconds in offset.
    '''
    if not s:
        return None

    OFFSET = (datetime.datetime(2001, 1, 1, 0, 0, 0)
        - datetime.datetime.fromtimestamp(0)).total_seconds()
    return datetime.datetime.fromtimestamp(s + OFFSET)


class Image(object):
    def __init__(self, path, uri):
        self.uri = uri
        self.path = os.path.join(path, uri)

    def exists(self):
        # The only reason I know of for this to fail is for the welcome.png that
        # is in the default note, which is not stored in local images, but it
        # could happen part way through a sync so make sure you check.
        return os.path.exists(self.path)


class Tag(object):
    def __init__(self, bear, id, title):
        self._bear = bear
        self.id = id
        self.title = title

    def notes(self, include_trashed = False, exact_match = False):
        """Return all notes with this tag.

        If exact_match is True, then ignore notes which have more specific tags.
        E.g. if tag is '#gtd/errands', then notes with more specific tags, such
        as '#gtd/errands/bycar' will not be returned.
        """
        cursor = self._bear._db.cursor()
        cursor.execute('''
            SELECT * FROM ZSFNOTE
            JOIN Z_7TAGS ON
                ZSFNOTE.Z_PK = Z_7TAGS.Z_7NOTES AND Z_7TAGS.Z_14TAGS=?
        ''', [self.id])

        for note in cursor.fetchall():
            n = self._bear._row_to_note(note)
            if exact_match:
                def note_has_more_specific_tag (note):
                    for t in n.tags():
                        # Does the note have a tag that is more specific?
                        if t.title.startswith(self.title) and \
                           len (t.title) > len (self.title):
                            return True
                    else:
                        return False
                if note_has_more_specific_tag (n):
                    continue
            if not include_trashed and n.deleted:
                # FIXME: Recent versions of Bear (e.g. v1.7.7) apparently use a
                # different flag to indicate notes which have been moved to
                # "Trash". While it is tempting to check if the note has a
                # 'trashed' attribute, which indeed a note gets upon moving to
                # Trash, this creates problems, because apparently notes which
                # got recovered from Trash retain their 'trashed' attribute.
                # This means we should not discriminate notes based on that
                # field, as we will be skiping valid (resotred) notes... :/
                continue
            yield n

    def __str__(self):
        return "({}) -> {}".format(self.id, self.title)


class Note(object):
    id = None
    created = None
    modified = None
    archived = None
    trashed = None
    deleted = False
    pinned = False
    title = None
    text = None

    def __init__(self, bear, int_id, id, created, modified, archived, trashed,
            deleted, pinned, title, text):
        self._bear = bear
        self.int_id = int_id
        self.id = id
        self.created = timestamp_to_datetime(created)
        self.modified = timestamp_to_datetime(modified)
        self.archived = timestamp_to_datetime(archived)
        self.trashed = timestamp_to_datetime(trashed)
        self.deleted = deleted
        self.pinned = pinned
        self.title = title
        self.text = text

    def tags(self):
        cursor = self._bear._db.cursor()
        cursor.execute('''
            SELECT * FROM ZSFNOTETAG
            JOIN Z_7TAGS ON
                Z_7TAGS.Z_7NOTES = ? AND Z_7TAGS.Z_14TAGS = ZSFNOTETAG.Z_PK
        ''', [self.int_id])

        for tag in cursor.fetchall():
            yield self._bear._row_to_tag(tag)

    def specific_tags(self):
        """
        Return list of *specific* tags for the note

        "Specific" means that if a note defines a tag, say
        `#projects/work/notebooks`, then any higher-level tags, such as
        `#projects` or `#projects/work` will _not_ be returned. This is in
        contrast to the default behaviour of pybear.Note.tags() which would
        return all these higher-order tags.
        """

        all_tags = sorted (self.tags(), \
                            key=lambda t: len(t.title))
        specific_tags = []
        for tag in all_tags:
            if tag.title in [ t.title[:len(tag.title)] \
                            for t in all_tags \
                            if len(t.title) > len (tag.title) ]:
                continue
            else:
                specific_tags.append (tag)
        return specific_tags

    def images(self):
        for uri in re.findall(r'\[image:([^\]]+)\]', self.text):
            yield Image(
                os.path.join(os.path.dirname(self._bear._path),
                    "Local Files/Note Images"),
                uri)

    def __str__(self):
        return "({}) {} ({} chars)".format(self.id, self.title, len(self.text))


class Bear(object):
    def __init__(self, path=None, *, connect=True):
        if path:
            self._path = path
        else:
            self._path = os.path.expanduser(
                '~//Library/Containers/net.shinyfrog.bear/Data/Library'
                '/Application Support/net.shinyfrog.bear/database.sqlite')
        if connect:
            self.connect()

    def connect(self, **kwds):
        self._db = sqlite3.connect(self._path, **kwds)
        self._db.row_factory = sqlite3.Row

    def notes(self):
        '''
        .. code-block:: sql

            CREATE TABLE ZSFNOTE (
                Z_PK                INTEGER PRIMARY KEY,
                Z_ENT               INTEGER,
                Z_OPT               INTEGER,
                ZARCHIVED           INTEGER,
                ZENCRYPTED          INTEGER,
                ZHASSOURCECODE      INTEGER,
                ZLOCKED             INTEGER,
                ZORDER              INTEGER,
                ZPERMANENTLYDELETED INTEGER,
                ZPINNED             INTEGER,
                ZSHOWNINTODAYWIDGET INTEGER,
                ZSKIPSYNC           INTEGER,
                ZTODOCOMPLETED      INTEGER,
                ZTODOINCOMPLETED    INTEGER,
                ZTRASHED            INTEGER,
                ZFOLDER             INTEGER,
                ZARCHIVEDDATE       TIMESTAMP,
                ZCREATIONDATE       TIMESTAMP,
                ZLOCKEDDATE         TIMESTAMP,
                ZMODIFICATIONDATE   TIMESTAMP,
                ZORDERDATE          TIMESTAMP,
                ZPINNEDDATE         TIMESTAMP,
                ZTRASHEDDATE        TIMESTAMP,
                ZLASTEDITINGDEVICE  VARCHAR,
                ZTEXT               VARCHAR,
                ZTITLE              VARCHAR,
                ZUNIQUEIDENTIFIER   VARCHAR,
                ZVECTORCLOCK        BLOB
            );
        '''

        cursor = self._db.cursor()
        cursor.execute("SELECT * FROM ZSFNOTE")

        for note in cursor.fetchall():
            yield self._row_to_note(note)

    def _row_to_note(self, row):
        return Note(
            bear = self,
            int_id = row['Z_PK'],
            id = row['ZUNIQUEIDENTIFIER'],
            created = row['ZCREATIONDATE'],
            modified = row['ZMODIFICATIONDATE'],
            archived = row['ZARCHIVEDDATE'],
            trashed = row['ZTRASHEDDATE'],
            deleted = row['ZPERMANENTLYDELETED'] != 0,
            pinned = row['ZPINNED'] != 0,
            title = row['ZTITLE'],
            text = row['ZTEXT']
        )

    def get_note(self, id):
        cursor = self._db.cursor()
        cursor.execute(
            'SELECT * FROM ZFSNOTE WHERE ZUNIQUEIDENTIFIER = ?', [id])
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_note(row)

    def tags(self):
        '''
        .. code-block:: sql

            CREATE TABLE ZSFNOTETAG (
                Z_PK                INTEGER PRIMARY KEY,
                Z_ENT               INTEGER,
                Z_OPT               INTEGER,
                ZMODIFICATIONDATE   TIMESTAMP,
                ZTITLE              VARCHAR
            );
        '''

        cursor = self._db.cursor()
        cursor.execute("SELECT * FROM ZSFNOTETAG")

        for tag in cursor.fetchall():
            yield self._row_to_tag(tag)

    def _row_to_tag(self, row):
        return Tag(
            bear = self,
            id = row['Z_PK'],
            title = row['ZTITLE']
        )

    def tag_by_title(self, title):
        cursor = self._db.cursor()
        cursor.execute('SELECT * FROM ZSFNOTETAG WHERE ZTITLE = ?', [title])

        tag = cursor.fetchone()
        if not tag:
            return None

        return self._row_to_tag(tag)
