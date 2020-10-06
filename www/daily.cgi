#! /usr/bin/env python3

import cgi, cgitb
cgitb.enable()


def main():
  print("Location: find.cgi?renderonly=1&books=available_books.json\n")


if __name__ == "__main__":
  main()
