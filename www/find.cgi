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
import library


def lookup_books(books, overdrive):
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


def page(books, overdrive):
  print("Content-Type: text/html\n")

  if overdrive:
    overdrive = overdrive.split(",")
  else:
    overdrive = library.OVERDRIVE_SUBDOMAINS

  book_data = lookup_books(books, overdrive)

  embedded = []
  rows = []
  for book in book_data:
    assembled = assemble_book(book)
    embedded.append(assembled)
    rows.append(make_row(assembled))
  rows = "\n".join(rows)
  
  with open("books.template.html") as f:
    print(f.read().format(rows=rows, books_json=json.dumps(embedded)))


def main():
  params = cgi.FieldStorage()
  page(params.getfirst("books", ""), params.getfirst("overdrive"))


if __name__ == "__main__":
  main()
