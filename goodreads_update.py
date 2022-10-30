#! /usr/bin/env python3

# This reads from a Goodreads RSS feed for a shelf, and prepends any new books
# found onto the file of books to check every night. This finally frees us from
# having to periodically use the rather slow Goodreads export function to get
# new books to read. It tries to keep as close as possible to the format of the
# Goodreads export, so that if the export is repeated, it can simply overwrite
# the added-to file, and the effects should be negligible.

# Right now, this is not written in a remotely portable way; it references files
# in my own directories on my private server. Edit URL and TO_READ for use.

# Note this destructively overwrites TO_READ, because it needs to insert new CSV
# rows starting at line 2. It's always a good idea to keep a backup of TO_READ
# because if the program crashes in the middle, it could have been deleted and
# not yet re-filled. Of course, simply repeating a Goodreads export should also
# recover it.

import csv
import feedparser
from pathlib import Path
import os
import sys

URL = open("private/eric_goodreads.rss").read().strip()
TO_READ = os.path.join(Path.home(), "to_read.csv")

def get_rss(url):
  return feedparser.parse(url)

def load_books(filename):
  if not os.path.exists(filename):
    return []
  with open(filename) as f:
    reader = csv.DictReader(f)
    return list(reader)

# This falls prey to "Lies Programmers Believe About Names", but the RSS feed
# doesn't have the field so I'm stuck with it for now.
def name_last_first(name):
  parts = name.split()
  return parts[-1] + ", " + " ".join(parts[:-1])
  
def rss_to_csv(e):
  return {
    "Book Id": e["book_id"],
    "Title": e["title"],
    "Author": e["author_name"],
    "Author l-f": name_last_first(e["author_name"]),
    "Additional Authors": "",
    "ISBN": '="' + e["isbn"] + '"',
    "ISBN13": "",
    "My Rating": e["user_rating"],
    "Average Rating": e["average_rating"],
    "Publisher": "",
    "Binding": "",
    "Number of Pages": e["num_pages"],
    "Year Published": e["book_published"],
    "Original Publication Year": "",
    "Date Read": e["user_read_at"],
    "Date Added": e["user_date_added"],
    "Bookshelves": e["user_shelves"],
    "Bookshelves with positions": "",
    "Exclusive Shelf": "to-read",
    "My Review": e["user_review"],
    "Spoiler": "",
    "Private Notes": "",
    "Read Count": "",
    "Recommended For": "",
    "Recommended By": "",
    "Owned Copies": "",
    "Original Purchase Date": "",
    "Original Purchase Location": "",
    "Condition": "",
    "Condition Description": "",
    "BCID": ""
  }
  
def update_books(books, rss):
  book_hash = {book["Book Id"]: book for book in books}
  for entry in reversed(rss.entries):
    row = rss_to_csv(entry)
    if entry["book_id"] in book_hash:
      book = books[books.index(book_hash[entry["book_id"]])]
      if book["Bookshelves"] != entry["user_shelves"]:
        print("Updating shelves for {}".format(entry["title"]))
        book["Bookshelves"] = entry["user_shelves"]
    else:
      print("Adding {}".format(entry["title"]))
      books.insert(0, row)
      book_hash[row["Book Id"]] = row

def save_books(books, filename):
  with open(filename, "w") as f:
    writer = csv.DictWriter(f, fieldnames=books[-1].keys())
    writer.writeheader()
    for book in books:
      writer.writerow(book)

def main():
  to_read = TO_READ
  url = URL
  if len(sys.argv) > 1:
    if len(sys.argv) < 3:
      print(f"Usage: {sys.argv[0]} <to_read.csv path> <Goodreads RSS URL>")
      exit()
    to_read = sys.argv[1]
    url = sys.argv[2]

  rss = get_rss(url)
  books = load_books(to_read)
  update_books(books, rss)
  save_books(books, to_read)

if __name__ == "__main__":
  main()
