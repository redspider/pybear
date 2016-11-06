# pybear

Extremely simple python library for accessing the Bear (writer) database.

Note that we make a number of terrible assumptions. The real Bear application makes use of Core Data and CloudKit
which do all kinds of fancy things. We sneak in under the covers to the base sqlite database, because it's easy. This
means a few important things:

1. If the data isn't in the local cache we won't see it - We don't do any kind of sync with CloudKit, so this really
needs to run on the system you use Bear most on, and even then occasionally you might not get a note for a while if
you entered it somewhere else.

2. If they change any field names or anything this isn't going to work until it's updated.

3. If the database path moves we might have to go play hide & seek again.

All that said and with all the disclaimer in the world, it works ok for me.

IMPORTANT NOTE:

Tags are CASE SENSITIVE. When you go getting tag_by_title you're gonna confuse yourself if you look for the wrong case.
I could search case-insensitive but I figure that might lead to even more confusion.

## How to use bear_to_jekyll

This is a tiny script that exports notes as (roughly) jekyll posts. you'll probably need to modify it to your needs.

This command will export ALL your notes to the given directory. Not really ideal unless it's a protected website. It
generates some simple front matter, including the title and tags.

    python bear_to_jekyll.py my/jekyll/posts/dir

This command will export anything in either of the tags "public" or "posts"

    python bear_to_jekyll.py --tag public --tag posts my/jekyll/posts/dir


## How to use the library:

### Get the titles of all your notes

    import bear

    b = bear.Bear()
    for note in b.notes():
        print(note.title)

### Get the titles of all your tags

    for tag in b.tags():
        print(tag.title)

### Get the text from all notes in the 'public' tag

    tag = b.tag_by_title('public')
    for note in tag.notes():
        print(note.text)
