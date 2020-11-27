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

"""This is an experiment into looking up metadata (mainly page length).

It uses the Google Books API.

The main trouble is that there are many editions of books and it's hard to
know which edition a library is lending.
"""

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
