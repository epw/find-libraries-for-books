#! /usr/bin/env python3

import cgi, cgitb
cgitb.enable()

import csv
import json
import library


def lookup_books(books):
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
      book = library.find_book(row["Title"], row["Author"])
    else:
      if not row:
        continue
      book = library.find_book(row[0], row[1])
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


def page(books):
  print("Content-Type: text/html\n")

  book_data = lookup_books(books)

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
  page(params.getfirst("books", ""))


if __name__ == "__main__":
  main()
