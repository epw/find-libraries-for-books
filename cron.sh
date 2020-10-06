#! /bin/bash

ROOT=$HOME/projects/find-libraries-for-books

cd $ROOT
./library.py $HOME/to_read.csv > $HOME/available_books.json
