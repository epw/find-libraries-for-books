#! /usr/bin/env python3

import requests

def search(q):
  params = {"q":q}
  r = requests.get(url="https://www.googleapis.com/books/v1/volumes", params=params)
  rj = r.json()
  print(rj["totalItems"])
  for i in rj["items"]:
    print(i["volumeInfo"]["title"], i["volumeInfo"]["pageCount"])

def main():
  search("Good Omens")


if __name__ == "__main__":
  main()
