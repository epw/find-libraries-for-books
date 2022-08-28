package org.willisson.eric.findlibrariesforbooks

import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.net.URLEncoder
import kotlin.text.Regex
import org.jsoup.Jsoup
import org.jsoup.nodes.Document
import org.jsoup.select.Elements

class Library {
    val OVERDRIVE_SUBDOMAINS = listOf("minuteman", "bpl")
    val GOODREADS_SERIES_REGEX = Regex.fromLiteral("""(.+)\(([^\)]*), [#](\d+)\)""")

    private fun extract_title(title: String) {
        val regex = GOODREADS_SERIES_REGEX.find(title)
        if (regex) {
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
        if (title_parts.series) {
            return "${title_parts.title} : ${title_parts.series}, Book ${title_parts.number}"
        }
        return title_parts.title
    }

    /** Read from Minuteman to extract Hoopla availability.

    Minuteman is nice enough to have a "Availble at Hoopla" annotation on the book results,
    so we can read that.
    */
    private fun minuteman(title, author) {
        val data = object {
            val hoopla: false
        }
	val doc: Document = Jsoup.connect(URLEncoder.encode("https://find.minlib.net/iii/encore/search/C__St:($title) a:($author)__Orightresult__U?lang=eng&suite=cobalt&fromMain=yes")).get()
	for (el in doc.select("div.searchResult")) {
	    val item_type = el.select("div.recordDetailValue > span.itemMediaDescription")[0].text().trim()
	    when (item_type) {
		"EBOOK" -> {
		    if ("at Hoopla" in el.text()) {
			data.hoopla = true
			val cover_src = el.select("div.itemBookCover > a > img")[0].attr("src")
			for (additional_info in el.select("div.addtlInfo > a") {
			    if ("Instantly available on hoopla." in additional_info.text()) {
				data.hoopla = additional_info.attr("href")
				// The full URL includes "image_size=thumb", so maybe edit that to make a better "full"
				data.covers = object {
				    val thumbnail: object {url: "https://find.minlib.net" + cover_src},
				    val full: object {url: "https://find.minlib.net" + cover_src}
				}
				break
			    }
			}
		    }
		}
	    }
	}
	return data
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
        if (gut) {
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
        if (mln_lookup.hoopla) {
            book_data.hoopla = mln_lookup.hoopla
            if mln_lookup.covers {
                book_data.covers = mln_lookup.covers
            }
            return listOf(book_data)
        }

	for (subdomain in OVERDRIVE_SUBDOMAINS) {
	    val overdrive_lookups = overdrive(subdomain, overdrive_title(title_parts), author)
	    val books = listOf()
	    for (book in overdrive_lookups) {
		if (book.available) {
		    val data = book_data.copy()
		    data.overdrive = subdomain
		    data.overdrive_url = book.url
		    data.format = book.format
		    data.covers = book.covers
		    books.add(data)
		}
	    }
	    return books
	}
    }
}
