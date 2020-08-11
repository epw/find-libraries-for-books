# Find libraries for books

This program takes a list of books, and tries to find libraries where you could
immediately check them out. It knows how to interpret Overdrive/Libby, Hoopla
as surfaced by the Minuteman Library Network, the Internet Archive's Open
Library, and Project Gutenberg.

## Getting started

To start with, get Goodreads data by using Export button at
https://www.goodreads.com/review/import

This produces a CSV with the following headers:

> Book Id, Title, Author, Author l-f, Additional Authors, ISBN, ISBN13, My Rating, Average Rating, Publisher, Binding, Number of Pages, Year Published, Original Publication Year, Date Read, Date Added, Bookshelves, Bookshelves with positions, Exclusive Shelf, My Review, Spoiler, Private Notes, Read Count, Recommended For, Recommended By, Owned Copies, Original Purchase Date, Original Purchase Location, Condition, Condition Description, BCID

You can use this, or input a CSV with the columns `Title` and `Author`.
[`simple.csv`](simple.csv) contains an example.

My Overdrive/Libby libraries are the Minuteman Library Network and the Boston
Public Library. This is implemented in the `OVERDRIVE_SUBDOMAINS` variable in
[`library.py`](library.py).

## Caveats and potential improvements

Title normalization is a huge problem. Gutenberg didn't pick up
Blazing World because Goodreads called it "The Blazing World" while
Gutenberg calls it "The Description of a New World, Called the
Blazing-World". A little fuzzy matching exists, and more is needed.

Because of the multiple Web requests per book, it seems to take 1-10 seconds per
line in the CSV, most of the time. An interesting upgrade would be to
parallelize the lookups.

Another improvement would be to read from Hoopla more directly, instead of
going through MLN's catalog.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

## License

Apache 2.0; see [`LICENSE`](LICENSE) for details.

## Disclaimers

This project is not an official Google project. It is not supported by Google
and Google specifically disclaims all warranties as to its quality,
merchantability, or fitness for a particular purpose.

This is also not officially supported by or otherwise affiliated with Overdrive,
Hoopla, the Internet Archive, or Project Gutenberg.
