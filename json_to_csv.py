#! /usr/bin/env python3
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import io
import json
import sys


def convert_to_csv(colnames, f):
  s = io.StringIO()

  writer = csv.writer(s)

  writer.writerow(colnames)

  for el in json.load(f):
    line = []
    for col in colnames:
      if col in el:
        line.append(str(el[col]))
      else:
        line.append("")
    writer.writerow(line)

  return s.getvalue()


def usage(name):
  print("Usage: {} col1 col2 col3 < file.json".format(name))


def main(argv):
  if len(argv) < 2:
    usage(argv[0])
    exit(1)
  print(convert_to_csv(argv[1:], sys.stdin), end="")


if __name__ == "__main__":
  main(sys.argv)
