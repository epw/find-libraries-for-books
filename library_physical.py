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

"""This is a special case of the normal library.py that just looks for physical
books in the Somerville library East branch."""

import json
import library
import sys

def main(argv):
  def inner(f):
    json.dump(library.physical_library(f), sys.stdout)

  if len(argv) < 2:
    inner(sys.stdin)
  else:
    with open(argv[1]) as f:
      inner(f)

  print()


if __name__ == "__main__":
  main(sys.argv)
