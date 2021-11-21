#! /usr/bin/env python3
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This script reads a CSV describing books, and outputs JSON for the ones that can be
read online when it is called.

It currently examines Hoopla as provided by Minuteman, and MLN and BPL Overdrive/Libby.

The CSV used as input should have a column named "Title" and one named "Author".

If there is a column named "Bookshelves", then it is assumed to contain a comma-separated list,
and only rows for which the Bookshelves column contains "to-read" will be used.

This should make it easy to write inputs to this script, but also lets you just export your
Goodreads data and automatically only look up books that you have said you want to read but
haven't yet.

The script outputs JSON, but also writes progress indicators to stderr because all the
Web lookups are slow.

Hopefully, alternating between MLN and the multiple Overdrive locations will stop any one
from rate-throttling us.

Matching of works is imprecise, because different services record titles and authors in
different ways. This program does the best it can, using what details we know about how
each service works.
"""

from bs4 import BeautifulSoup
import bz2
import csv
import json
import os
import pickle
import re
import requests
import sys
import urllib.parse


OVERDRIVE_SUBDOMAINS = ("minuteman", "bpl")

GOODREADS_SERIES_REGEX = re.compile(r'(.+)\(([^\)]*), [#](\d+)\)')

def extract_title(title):
  """Parse a title that is part of a series as displayed by Goodreads."""
  regex = GOODREADS_SERIES_REGEX.match(title)
  if regex:
    return {"title": regex.group(1).strip(),
            "series": regex.group(2),
            "number": regex.group(3)}
  return {"title": title,
          "series": None,
          "number": None}


# Project Gutenberg has a ~8MB text file listing its catalog. There are a lot of
# transcription errors, and just variations in titles, so some extra logic goes into
# looking for matches.


GUTINDEX_URL = "https://www.gutenberg.org/dirs/GUTINDEX.ALL"
gutindex = None

MAIN_LINE = re.compile(r'(.*)\s+([0-9]+C?)\s*$')

PROPERTY_REGEX = re.compile(r'\[[A-Za-z]+: [^\]]+\]')

def process_gutenberg(parts):
  """Assemble Gutenberg catalog records into "title, by author" strings.

  The records tend to be of the form:

  Title, by author [spaces until about column 75] #####
    Title and author continuation
    [Label: data]
    [Label2: data]

  With a newline separating records.

  However, sometimes the lines after the title aren't indented, among other errors.
  The loop in the main gutenberg() function tries to make lists of strings representing
  records, and this assembles them into one string to match against."""
  record = " ".join(parts)
  new_record = None
  while True:
    new_record = PROPERTY_REGEX.sub("", record)
    if new_record == record:
      break
    record = new_record
  return [s.strip().lower() for s in record.split(", by ")]


def split_title(title):
  """Splits a title, or title and author, into individual words, probably."""
  return re.split(r'[-\s,:;\(\)]', title)


def gutenberg_match(work, title, author):
  """Fuzzy match of title and author, if provided, looking for each given word in the record."""
  for word in split_title(title):
    if not work[0] or work[0].find(word.lower()) == -1:
      return False
  if not author:
    return work
  for word in split_title(author):
    if not work[1] or work[1].find(word.lower()) == -1:
      return False
  return work


def gutenberg_lookup(gutindex, title, author):
  """Filter catalog to find likely matches, and if there's only one, return it."""
  works = list(gutindex.keys())
  for word in split_title(" ".join([title, author or ""])):
    filtered_works = []
    for work in works:
      if word.lower() in work[0] or word.lower() in (work[1] or []):
        filtered_works.append(work)
    if len(filtered_works) == 0:
      return None
    elif len(filtered_works) == 1:
      return gutenberg_match(filtered_works[0], title, author)
    works = filtered_works
  return filtered_works[0]  # Giving up, giving "most likely" of last set


def gutenberg(title, author):
  """Download Project Gutenberg catalog and process it, then return the likely record, if any."""
  global gutindex
  if gutindex:
    book = gutenberg_lookup(gutindex, title, author)
    if book:
      return book + (gutindex[book],)
    else:
      return None

  if os.path.exists("/tmp/gutindex.pkl"):
    gutindex = pickle.load(open("/tmp/gutindex.pkl", "rb"))
    return gutenberg(title, author)

  line_count = 0
  gutindex = {}
  state = None
  ebook_no = None
  parts = []
  r = requests.get(GUTINDEX_URL)
  try:
    r.raise_for_status()
  except requests.exceptions.HTTPError as e:
    gutindex = "not found"
    raise e
  r.encoding = "UTF-8"
  with open("/tmp/gutindex.txt", "w") as f:
    f.write(r.text)
  for bytesline in r.iter_lines():
    line = bytesline.decode("utf8")
    line_count += 1
    if state == None:
      if line.strip() == "<==LISTINGS==>":
        state = "listings"
    elif state == "listings":
      if line.startswith("TITLE and AUTHOR"):
        state = "main"
    elif state == "main":
      if not line.strip():
        continue
      if line[0].isspace(): # If this is an indented line
        parts.append(line.strip())
      else:
        if ebook_no:
          if MAIN_LINE.match(line) or line.strip() == "<==End of GUTINDEX.ALL==>": # If we are starting a new section
            state = "main"
            processed = process_gutenberg(parts)
            book_title = processed[0]
            book_author = None
            if len(processed) > 1:
              book_author = processed[1]
            gutindex[(book_title, book_author)] = ebook_no

        if line.strip() == "<==End of GUTINDEX.ALL==>":
          break
        if line.startswith("="*20):
          state = "listings"
          ebook_no = None
          continue
        if line.startswith("~ ~ ~ ~ Posting Dates") or line.startswith("TITLE and AUTHOR"):
          ebook_no = None
          continue
        regex = MAIN_LINE.match(line)
        if regex:
          ebook_no = regex.group(2).strip()
          if ebook_no.endswith("C"):
            ebook_no = ebook_no[:-1]
          parts = [regex.group(1).strip()]
        else:
          # Special cases which are probably typos, like a 'k' on one line between two
          # unique titles that don't otherwise have a blank line between them.
          # Try to filter out the known garbage, then append and hope for the best.
          if line == "k":
            continue
          if line.strip() == "What Have the Greeks Done, by":
            continue
          parts.append(line.strip())
  pickle.dump(gutindex, open("/tmp/gutindex.pkl", "wb"))
  return gutenberg(title, author)


# Overdrive has separate URLs for each library, but doesn't need a login to report
# which books are available. The pages dynamically load their elements with JavaScript,
# so HTML analysis doesn't work. But, the page response includes raw JSON, which can be
# identified and read.


def overdrive_title(title_parts):
  return title_parts["title"]


def overdrive(subdomain, title, author):
  """Parse Overdrive to find books that are available.

  Overdrive won't let me use their API, and the HTML is generated dynamically by JS.
  But, first, the data is loaded as a JSON blob inserted into the page. So, we can
  parse that."""
  r = requests.get("https://{}.overdrive.com/search".format(subdomain),
                   params={"query": title,
                           "creator": author,
                           "sortBy": "relevance"})
  r.raise_for_status()
  data = {"available": False}
  # This is the start of the line where the JSON blobs reside.
  match = "window.OverDrive.mediaItems = "
  start = r.text.find(match)
  if start == -1:
    return data
  decoder = json.JSONDecoder()
  # This should read just one JSON object from the select spot in the text.
  # Since it stops after one object, we don't have to worry about otherwise detecting
  # the end of the JSON blob.
  media_items = decoder.raw_decode(r.text[start + len(match):])[0]
  for key in media_items:
    item = media_items[key]
    if item["title"] == title and item["type"]["name"] == "eBook" and item["isAvailable"]:
      data["available"] = True
      # This URL redirects to a specific one for your library if you are logged in.
      data["url"] = "https://{}.overdrive.com/media/{}".format(subdomain, key)
      break
  return data


# My main library is in the Minuteman network, and their page lists whether each
# book is available on Hoopla. The pages are static enough HTML that can be parsed.


def mln_title(title_parts):
  """Convert title_parts to the way Minuteman represents books in series."""
  if title_parts["series"]:
    return "{} : {} Series, Book {}".format(title_parts["title"],
                                            title_parts["series"],
                                            title_parts["number"])
  return title_parts["title"]


def minuteman(title, author):
  """Read from Minuteman to extract Hoopla availability.

  Minuteman is nice enough to have a "Availble at Hoopla" annotation on the book results,
  so we can read that."""
  data = {"hoopla": False}
  query_str = urllib.parse.quote("C__St:({title}) a:({author})__Orightresult__U".format(
    title=title,
    author=author))
  try:
    r = requests.get("https://find.minlib.net/iii/encore/search/" + query_str,
                     params={"lang": "eng", "suite": "cobalt", "fromMain": "yes"})
  except requests.exceptions.ConnectionError:
    return data
  r.raise_for_status()
  soup = BeautifulSoup(r.text, "html.parser")
  for el in soup.find_all("div", class_="searchResult"):
    item_type = el.select("div.recordDetailValue > span.itemMediaDescription")[0].string.strip()
    if item_type == "EBOOK":
      if "at Hoopla" in el.stripped_strings:
        data["hoopla"] = True
        for additional_info in el.select("div.addtlInfo > a"):
          if "Instantly available on hoopla." in additional_info.stripped_strings:
            data["hoopla"] = additional_info["href"]
            break
  return data


def somervilleeast(title, author):
  """Look for physical books available in the Somerville Library East branch."""
  # This query string was derived from an advantaced search at https://find.minlib.net/iii/encore/home?lang=eng&suite=cobalt&advancedSearch=true
  # with a title and author, with format BOOK, location Somerville, collection SOMERVILLE/EAST
  query_str = urllib.parse.quote("C__St:({title}) a:({author}) f:a c:32 b:so2__Orightresult__U".format(
    title=title,
    author=author))
  r = requests.get("https://find.minlib.net/iii/encore/search/" + query_str,
                   params={"lang": "eng", "suite": "cobalt", "fromMain": "yes"})
  r.raise_for_status()
  soup = BeautifulSoup(r.text, "html.parser")
  data = {"somerville/east": False}
  for el in soup.find_all("div", class_="searchResult"):
    item_type = el.select("div.recordDetailValue > span.itemMediaDescription")[0].string.strip()
    if item_type == "BOOK":
#      items_container = el.select("div.ItemsContainer")
      table = el.select("div.bibHoldingsWrapper table.itemTable")
      for row in table[0]("tr"):
        tds = list(row("td"))
        if not tds:
          continue
        print(tds[0])
        if tds[0].string.strip().startswith("SOMERVILLE/EAST"):
          if tds[2].chilren[0].string.strip() == "Available":
            data["somerville/east"] = "Available"
            break

#      availability_message = items_container[0].select_one("span.availabilityMessage")
#      print(availability_message.string.strip())
#      if (availability_message.select("span.itemsAvailable")[0].string.strip() == "Available"
#         and availability_message.string.strip()
#      availability = el.select("div.ItemsContainer span.itemsAvailable")[0].string.strip()
#      data["somerville/east"] = availability
  return data


# The Internet Archive's Open Library is easy, with a documented JSON API.


def open_library(title, author):
  """Read from Open Library.

  Documentation is at https://openlibrary.org/dev/docs/api/search ."""
  r = requests.get("https://openlibrary.org/search.json",
                   params={"q": title,
                           "author": author,
                           "mode": "ebooks",
                           "has_fulltext": "true"})
  r.raise_for_status()
  for doc in r.json()["docs"]:
#    if doc["title"].lower() == title.lower() and [True for a in doc.get("author_name", []) if a.lower() == author]:
    if doc["title"].lower() == title.lower():
      if "availability" in doc and doc["availability"]["status"] == "borrow_available":
        return True
  return False


def find_book(full_title, author, overdrive_subdomains=OVERDRIVE_SUBDOMAINS):
  """For each book, look it up in Minuteman for Hoopla, and in various Overdrive feeds.

  Also looks at Open Library and Gutenberg.

  Consolidate the data to tell us where to look for it."""
  title_parts = extract_title(full_title)
  data = {"title": full_title,
          "author": author}
  gut = gutenberg(title_parts["title"], author)
  if gut:
    data["gutenberg"] = gut
    return data
  try:
    mln_lookup = minuteman(mln_title(title_parts), author)
    if mln_lookup["hoopla"]:
      data["hoopla"] = mln_lookup["hoopla"]
      return data
  except requests.exceptions.HTTPError as e:
    sys.stderr.write(str(e))
  overdrive_place = None
  for subdomain in overdrive_subdomains:
    try:
      overdrive_lookup = overdrive(subdomain, overdrive_title(title_parts), author)
      if overdrive_lookup["available"]:
        overdrive_place = subdomain
        data["overdrive"] = overdrive_place
        data["overdrive_url"] = overdrive_lookup["url"]
        return data
    except requests.exceptions.HTTPError as e:
      sys.stderr.write(str(e))
  try:
    data["openlibrary"] = open_library(title_parts["title"], author)
  except requests.exceptions.HTTPError as e:
    sys.stderr.write(str(e))
  return data


def find_physical_book(full_title, author):
  """For each book, look it up in the Somerville East branch."""
  title_parts = extract_title(full_title)
  data = {"title": full_title,
          "author": author}
  try:
    lookup = somervilleeast(mln_title(title_parts), author)
    if lookup["somerville/east"]:
      data["somerville/east"] = lookup["somerville/east"]
      return data
  except requests.exceptions.HTTPError as e:
    sys.stderr.write(str(e))
  return data


def wrong_shelf(row):
  if "Bookshelves" in row:
    shelves = map(str.strip, row["Bookshelves"].split(","))
    return "to-read" not in shelves


def found_book(book):
  return (book.get("hoopla")
          or book.get("overdrive")
          or book.get("openlibrary")
          or book.get("gutenberg"))


def library(goodreads_csv, overdrive_subdomains):
  """Print JSON for which books from the filename are immediately available to take out at a library."""
  reader = csv.DictReader(goodreads_csv)
  items = []
  for row in reader:
    if wrong_shelf(row):
      continue
    sys.stderr.write("{} by {}\n".format(row["Title"], row["Author"]))
    book = find_book(row["Title"], row["Author"], overdrive_subdomains)
    if found_book(book):
      items.append(book)
  return items


def physical_library(goodreads_csv):
  """Print JSON for which books from the filename are immediately available to take out at a library."""
  reader = csv.DictReader(goodreads_csv)
  items = []
  for row in reader:
    if wrong_shelf(row):
      continue
    sys.stderr.write("{} by {}\n".format(row["Title"], row["Author"]))
    book = find_physical_book(row["Title"], row["Author"])
    if "somerville/east" in book:
      items.append(book)
  return items


def usage(prog):
  print("Usage: {} goodreads.csv")


def main(argv):
  overdrive_subdomains = OVERDRIVE_SUBDOMAINS
  def inner(f):
    json.dump(library(f, overdrive_subdomains), sys.stdout)

  if len(argv) < 2:
    inner(sys.stdin)
  else:
    if len(argv) > 2:
      overdrive_subdomains = argv[2].split(",")
    with open(argv[1]) as f:
      inner(f)

  print()


if __name__ == "__main__":
  main(sys.argv)
