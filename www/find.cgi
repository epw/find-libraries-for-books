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
    else:
      if not row:
        continue
      title = row[0]
      author = row[1]
    book = library.find_book(title, author, overdrive)
    if library.found_book(book):
      items.append(book)
  if csvfile is not None and csvfile.filename:
    items += lookup_books(books, None, overdrive)
  return items


def assemble_book(book):
  other = list(set(["openlibrary", "gutenberg"]) & set(book))
  if other:
    other = other[0]
  else:
    other = ""
  return {"title": book.get("title", ""),
          "author": book.get("author", ""),
          "overdrive": book.get("overdrive", ""),
          "hoopla": book.get("hoopla", ""),
          "other": other}


def make_row(book):
  return """<tr>
  <td>{title}</td>
  <td>{author}</td>
  <td>{overdrive}</td>
  <td>{hoopla}</td>
  <td>{other}</td>
</tr>""".format(title=book["title"],
                author=book["author"],
                overdrive=book["overdrive"],
                hoopla=book["hoopla"],
                other=book["other"])


def escape_filename(filename):
  return "".join(c for c in filename if c.isalnum() or c in (".", "_", "-"))


def page(books, csvfile, overdrive, renderonly=False):
  print("Content-Type: text/html\n")

  if overdrive:
    overdrive = overdrive.split(",")
  else:
    overdrive = library.OVERDRIVE_SUBDOMAINS

  if renderonly:
    books = escape_filename(books)
    with open(books) as f:
      book_data = json.load(f)
  else:
    book_data = lookup_books(books, csvfile, overdrive)

  embedded = []
  rows = []
  for book in book_data:
    assembled = assemble_book(book)
    embedded.append(assembled)
    rows.append(make_row(assembled))
  count = len(rows)
  rows = "\n".join(rows)

  with open("books.template.html") as f:
    print(f.read().format(count=count, rows=rows, books_json=json.dumps(embedded)))


def main():
  params = cgi.FieldStorage()
  csvfile = params["csvfile"] if "csvfile" in params else None
  page(params.getfirst("books", ""), None, params.getfirst("overdrive"), params.getfirst("renderonly"))


if __name__ == "__main__":
  main()
