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

4. Plausibly doing this could destroy everything you love, or at least your notes. I haven't noticed a problem but
backup regularly.

All that said and with all the disclaimer in the world, it works ok for me.

IMPORTANT NOTE:

Tags are CASE SENSITIVE. When you go getting tag_by_title you're gonna confuse yourself if you look for the wrong case.
I could search case-insensitive but I figure that might lead to even more confusion.

## Installation

It probably needs python 3, I haven't tried anything else. The `requirements.txt` file has all the requirements, but
at the time of writing the only one is the Markdown package and that's only necessary for `bear_to_html`.

## How to use bear_to_jekyll

This is a tiny script that exports notes as (roughly) jekyll posts. you'll probably need to modify it to your needs.

This command will export ALL your notes to the given directory. Not really ideal unless it's a protected website. It
generates some simple front matter, including the title and tags.

    python bear_to_jekyll.py my/jekyll/posts/dir

This command will export anything in either of the tags "public" or "posts".

    python bear_to_jekyll.py --tag public --tag posts my/jekyll/posts/dir

In both cases relevant images (only) will be exported as well, in directories that look like big UUIDs - this is how
Bear represents them so I don't mess with that.

## How to use bear_to_html

Similar to the above, except this one will do some trivial markdown processing and try and give you HTML that mostly
works. It's not great - Bear uses some custom stuff for things like todo lists which don't come across well, and
handles things like header spacing much better than almost-vanilla python Markdown module does. It's readable though.

You can export this into a Dropbox dir for read-only access for example. Same arguments as bear_to_jekyll to export
just a subset of your notes.

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
