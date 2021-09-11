#! /bin/bash

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <goodreads exported .csv>"
    exit 1
fi

cp "$1" $HOME/to_read.csv
