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
from datetime import date
import json
import os
import shutil
import sys

from values import DB

def hide_book(title, author):
  db = []
  if os.path.exists(DB):
    try:
      with open(DB) as f:
        db = json.load(f)
    except json.decoder.JSONDecoderError:
      shutil.copy(DB, "{}-{}".format(DB, date.isoformat()))
  db.append({"title": title,
             "author": author})
  with open(DB, "w") as f:
    json.dump(db, f)
  print(json.dumps({"result": "success"}))


def main():
  print("Content-Type: text/json\n")
  try:
    params = json.load(sys.stdin)
  except Exception:
    err_type, value, traceback = sys.exc_info()
    print(json.dumps({"result": "error",
                      "error": err_type.__name__,
                      "value": str(value)}))
    exit(1)

  hide_book(params["title"], params["author"])


if __name__ == "__main__":
  main()
