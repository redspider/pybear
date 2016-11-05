import os.path
import sqlite3


class Tag(object):
    def __init__(self, bear, id, title):
        self._bear = bear
        self.id = id
        self.title = title
    
    def notes(self):
        cursor = self._bear._db.cursor()
        cursor.execute("SELECT * FROM ZSFNOTE JOIN Z_5TAGS ON ZSFNOTE.Z_PK = Z_5TAGS.Z_5NOTES AND Z_5TAGS.Z_10TAGS=?", [self.id])

        for note in cursor.fetchall():
            yield self._bear._row_to_note(note)

    def __str__(self):
        return "({}) {}".format(self.id, self.title)


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

    def __init__(self, bear, int_id, id, created, modified, archived, trashed, deleted, pinned, title, text):
        self._bear = bear
        self.int_id = int_id
        self.id = id
        self.created = created
        self.modified = modified
        self.archived = archived
        self.trashed = trashed
        self.deleted = deleted
        self.pinned = pinned
        self.title = title
        self.text = text

    def tags(self):
        cursor = self._bear._db.cursor()
        cursor.execute("SELECT * FROM ZSFNOTETAG JOIN Z_5TAGS ON Z_5TAGS.Z_5NOTES = ? AND Z_5TAGS.Z_10TAGS=ZSFNOTETAG.Z_PK",
                       [self.int_id])

        for tag in cursor.fetchall():
            yield self._bear._row_to_tag(tag)

    def __str__(self):
        return "({}) {} ({} chars)".format(self.id, self.title, len(self.text))


class Bear(object):
    def __init__(self, path=None):
        if path:
            self._path = path
        else:
            self._path = os.path.expanduser('~//Library/Containers/net.shinyfrog.bear/Data/Library/Application '
                                      'Support/net.shinyfrog.bear/database.sqlite')
        self.connect()

    def connect(self):
        self._db = sqlite3.connect(self._path)
        self._db.row_factory = sqlite3.Row

    def notes(self):
        """
        CREATE TABLE ZSFNOTE ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZARCHIVED INTEGER, ZENCRYPTED
        INTEGER, ZHASSOURCECODE INTEGER, ZLOCKED INTEGER, ZORDER INTEGER, ZPERMANENTLYDELETED INTEGER,
        ZPINNED INTEGER, ZSHOWNINTODAYWIDGET INTEGER, ZSKIPSYNC INTEGER, ZTODOCOMPLETED INTEGER, ZTODOINCOMPLETED
        INTEGER, ZTRASHED INTEGER, ZFOLDER INTEGER, ZARCHIVEDDATE TIMESTAMP, ZCREATIONDATE TIMESTAMP, ZLOCKEDDATE
        TIMESTAMP, ZMODIFICATIONDATE TIMESTAMP, ZORDERDATE TIMESTAMP, ZPINNEDDATE TIMESTAMP, ZTRASHEDDATE TIMESTAMP,
        ZLASTEDITINGDEVICE VARCHAR, ZTEXT VARCHAR, ZTITLE VARCHAR, ZUNIQUEIDENTIFIER VARCHAR, ZVECTORCLOCK BLOB );
        """

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

    def tags(self):
        """
        CREATE TABLE ZSFNOTETAG ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZMODIFICATIONDATE 
        TIMESTAMP, ZTITLE VARCHAR );
        """

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
        cursor.execute("SELECT * FROM ZSFNOTETAG WHERE ZTITLE=?", [title])

        tag = cursor.fetchone()
        if not tag:
            return None

        return self._row_to_tag(tag)
