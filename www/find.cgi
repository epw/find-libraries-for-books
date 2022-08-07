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

import cgi, cgitb
cgitb.enable()

import csv
import json
import io
import library
import os

try:
  from private.values import DB
  from private.values import PEOPLE
except ModuleNotFoundError:
  from values import DB
  PEOPLE = {}

def lookup_books(books, csvfile, overdrive):
  if csvfile is not None and csvfile.filename:
    # In Python 2, I could have just said csv.DictReader(csvfile.file)
    # But because Python 3 has the wrong idea about unicode, I have to
    # read the whole thing and convert to a string and wrap in io.StringIO
    # Hopefully the CSV won't be too big. Thanks, Python.
    string = csvfile.file.read().decode("utf8")
    reader = csv.DictReader(io.StringIO(string))
  else:
    lines = books.split("\n")
    if lines[0].find("Title") != -1 and lines[0].find("Author") != -1:
      reader = csv.DictReader(lines)
    else:
      reader = csv.reader(lines)
  items = []
  for row in reader:
    if library.wrong_shelf(row):
      continue
    if "Title" in row:
      title = row["Title"]
      author = row["Author"]
      bookshelves = row.get("Bookshelves", "")
    else:
      if not row:
        continue
      title = row[0]
      author = row[1]
      bookshelves = ""
    if not title.strip():
      continue
    books = library.find_book(title, author, bookshelves, overdrive)
    for book in books:
      if library.found_book(book):
        items.append(book)
  if csvfile is not None and csvfile.filename:
    items += lookup_books(books, None, overdrive)
  return items


def a_tag(url, text):
  return "<a href='{}'>{}</a>".format(url, text)

def assemble_overdrive(book):
  if "overdrive_url" in book:
    return a_tag(book.get("overdrive_url"), book.get("overdrive", "ERROR"))
  return book.get("overdrive", "")


def assemble_hoopla(book):
  if "hoopla" in book:
    if book["hoopla"].startswith("http"):
      return a_tag(book["hoopla"], "Hoopla")
  return book.get("hoopla", "")


def assemble_other(book):
  if "gutenberg" in book:
    return a_tag("https://www.gutenberg.org/ebooks/{}".format(book["gutenberg"][2]), "gutenberg")
  if "openlibrary" in book:
    return "openlibrary"
  return ""


def assemble_access(book):
  overdrive = assemble_overdrive(book)
  hoopla = assemble_hoopla(book)
  other = assemble_other(book)
  return ", ".join([link for link in [overdrive, hoopla, other] if link])

def first(l):
  if len(l) > 0:
    return l[0]
  return None

def assemble_urls(book):
  gutenberg = None
  if "gutenberg" in book and len(book["gutenberg"]) >= 3:
    gutenberg = "https://www.gutenberg.org/ebooks/{}".format(book["gutenberg"][2])
  return [url for url in [book.get("overdrive_url"), book.get("hoopla"), gutenberg] if url]

def assemble_tags(book):
  return ", ".join(sorted(book.get("tags", [])))

def assemble_cover(book):
  if not book.get("covers"):
    return ""
  return "<img class='cover' src='{}'>".format(book["covers"]["thumbnail"]["href"])

def assemble_book(book):
  return {"title": book.get("title", ""),
          "covers": assemble_cover(book),
          "author": book.get("author", ""),
          "format": book.get("format", "ebook"),
          "access": assemble_access(book),
          "url": first(assemble_urls(book)),
          "tags": assemble_tags(book)}


def make_row(book, covers):
  if covers:
    return """<div class="book">
  <a class="book" href="{url}">
    <div>
      <div class="cover">{cover}</div>
      <div class="details">
        <div class="title">{title}</div>
        <div class="byline">by <span class="author">{author}</span></div>
      </div>
    </div>
  </a>
  <div class="filing">
    <div class="tags">
     {tags}
    </div>
    <div class="hide">X</div>
  </div>
</div>
""".format(title=book["title"],
           author=book["author"],
           url=book["url"],
           cover=book["covers"],
           tags=book["tags"])

  return """<tr>
  <td class="hide"><span>X</span></td>
  <td class="title">{title}</td>
  <td class="author">{author}</td>
  <td class="access">{access}</td>
  <td class="tags">{tags}</td>
</tr>""".format(title=book["title"],
                author=book["author"],
                access=book["access"],
                tags=book["tags"])

def inject_css(account):
  if account.get("hide"):
    return ""
  return """
th.hide, td.hide { display: none; }
div.book.hide { display: none; }
"""

def make_content(rows, covers):
  if covers:
    return """
  <div class="covertiles">
  {rows}
  </div>""".format(rows=rows)

  return """
  <table border="1">
    <tr>
      <th class="hide">Hide</th>
      <th>Title</th>
      <th>Author</th>
      <th>Access</th>
      <th>Tags</th>
    </tr>
    {rows}
  </table>""".format(rows=rows)

def page(books, csvfile, overdrive, daily=False, account=None, audiobooks=False, covers=False):
  print("Content-Type: text/html\n")

  if overdrive:
    overdrive = overdrive.split(",")
  else:
    overdrive = library.OVERDRIVE_SUBDOMAINS

  errors = ""

  audiobook_checked = ""
  if audiobooks:
    audiobook_checked = "checked"

  covers_checked = ""
  if covers:
    covers_checked = "checked"

  if daily:
    with open(books) as f:
      try:
        book_data = json.load(f)
      except json.decoder.JSONDecodeError as e:
        if os.path.getsize(f.name) == 0:
          errors = "Available books file empty."
        else:
          errors = str(e)
        book_data = []
  else:
    book_data = lookup_books(books, csvfile, overdrive)
    

  db = {}
  try:
    if os.path.exists(DB):
      with open(DB) as f:
        db = json.load(f)
  except:
    raise

  embedded = []
  rows = []
  hidden_count = 0
  for book in book_data:
    assembled = assemble_book(book)
    if audiobooks:
      if assembled["format"] != "audiobook":
        continue
    else:
      if assembled["format"] == "audiobook":
        continue
    hidden_book = False
    if account.get("hide"):
      for hidden in db:
        if hidden["title"] == assembled["title"] and hidden["author"] == assembled["author"]:
          hidden_count += 1
          hidden_book = True
          break
      if hidden_book:
        continue
    embedded.append(assembled)
    rows.append(make_row(assembled, covers))
  count = len(rows)
  rows = "\n".join(rows)

  with open("books.template.html") as f:
    print(f.read().format(personal_book_list=account["personal_book_list"],
                          inject_css=inject_css(account),
                          count=count,
                          content=make_content(rows, covers),
                          books_json=json.dumps(embedded),
                          hidden=hidden_count,
                          errors=errors,
                          covers_checked=covers_checked,
                          audiobook_checked=audiobook_checked))


def main():
  params = cgi.FieldStorage()
  csvfile = params["csvfile"] if "csvfile" in params else None
  books = params.getfirst("books", "")
  account = {
    "available": "available_books.json",
    "personal_book_list": "a local file on the server",
    "hide": True
  }
  daily = params.getfirst("daily", "").strip().lower() # Whether to set to filename for daily dump from ../cron.sh
  for person in PEOPLE:
    if daily == person:
      account = PEOPLE[person]
      break

  if daily:
    books = account["available"]
  page(books, None, params.getfirst("overdrive"), params.getfirst("daily"), account, params.getfirst("audiobooks"),
       params.getfirst("covers"))


if __name__ == "__main__":
  main()
