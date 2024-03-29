#! /bin/bash
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
#
# Add this to your crontab with something like:
# 6 3 * * *	$HOME/find-libraries-for-books/cron.sh
log=$HOME/available_books_history

mkdir -p $log

ROOT=$HOME/projects/find-libraries-for-books

cd $ROOT
./library.py $HOME/to_read.csv > $HOME/available_books.json 2>/dev/null
cp $HOME/available_books.json $log/availale_books-`date -Iminutes`.json

