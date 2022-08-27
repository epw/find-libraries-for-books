package org.willisson.eric.findlibrariesforbooks

import kotlin.text.Regex

class Library {
    val OVERDRIVE_SUBDOMAINS = listOf("minuteman", "bpl")
    val GOODREADS_SERIES_REGEX = Regex.fromLiteral("""(.+)\(([^\)]*), [#](\d+)\)""")
    
    private fun extract_title(title: String) {
	val regex = GOODREADS_SERIES_REGEX.find(title)
	if (!regex) {
	    return object {
		val title: regex.groups(0).trim(),
		val series: regex.group(1),
		val number: regex.group(2)
	    }
	}
	return object {
	    val title: title,
	    val series: null,
	    val number: null
	}
    }

    private fun mln_title(title_parts) {
	if title_parts.series {
	    return "${title_parts.title} : ${title_parts.series}, Book ${title_parts.number}"
	}
	return title_parts.title
    }
    
    private gutenberg(title, author) {
	// Unimplemented
    }
    
    fun find_book(title, author, bookshelves) {
	val title_parts = extract_title(title)
	val book_data = object {
	    val title: title,
	    val author: author,
	    val tags: bookshelves
	}

	val gut = gutenberg(title_parts.title, author)
	if gut {
	    book_data.gutenberg = gut
	    book_data.covers = object {
		val thumbnail: object {
		    val url: gutenberg_cover(gut, thumbnail=True),
		},
		val full: object {
		    val url: gutenberg_color(gut)
		}
	    }
	    return listOf(book_data)
	}

	val mln_lookup = minuteman(mln_title(title_parts), author)
	if mln_lookup.hoopla {
	    book_data.hoopla = mln_lookup.hoopla
	    if mln_lookup.covers {
		book_data.covers = mln_lookup.covers
	    }
	    return listOf(book_data)
	}
    }
}
