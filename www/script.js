// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

function example_data() {
  const books = document.getElementById("books");
  books.value = document.getElementById("example").textContent;
}

function download_books() {
  download_csv_file(["title", "author", "overdrive", "hoopla", "other"],
    books_json, "table.csv");
}

// This is now either a <tr> tag or a <div class="book"> tag,
// depending on whether the view is a table or cover tiles.
async function record_hide_book(tr) {
  const params = new URLSearchParams(location.search);
  if (params.get("daily") != "1") {
    return false;
  }

  const title = tr.querySelector(".title").textContent;
  const response = await fetch("hide_book.cgi", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      "title": title,
      "author": tr.querySelector(".author").textContent
    })
  });
  if (response.status != 200) {
    const line = document.createElement("div");
    line.textContent = `Error hiding book "${title}": ${response.status}.`;
    document.getElementById("errors").appendChild(line);
  }
  return (response.status == 200);
}

function hide_book_table(e) {
  for (let el of e.path) {
    if (el.tagName == "TR") {
      record_hide_book(el);
      el.parentElement.removeChild(el);
      break;
    }
  }
}

function book_events_table(tr) {
  if (!tr.querySelector("td")) {
    return;
  }
  tr.querySelector("td.hide").addEventListener("click", hide_book_table);
}

function hide_book_covers(e) {
  for (let el of e.path) {
    if (el.tagName == "DIV" && el.classList.contains("book")) {
      record_hide_book(el);
      el.parentElement.removeChild(el);
      break;
    }
  }
}

function book_events_covers(div) {
  const hide_el = div.querySelector(".hide");
  if (hide_el) {
    hide_el.addEventListener("click", hide_book_covers);
  }
}

function checkbox_to_param_bool(checkbox) {
    if (checkbox.checked) {
	return "1";
    }
    return "";
}

function change_audiobooks() {
    const query_params = new URLSearchParams(location.search);
    query_params.set("audiobooks", checkbox_to_param_bool(document.getElementById("audiobook")));
    location.search = query_params;
}
function change_covers() {
    const query_params = new URLSearchParams(location.search);
    query_params.set("covers", checkbox_to_param_bool(document.getElementById("covers")));
    location.search = query_params;
}

function change_filters() {
    const select = document.getElementById("filter");
    const books = document.getElementById("books");
    if (select.value == "(none)") {
	books.classList.remove("filtering");
    } else {
	books.classList.add("filtering");
    }
}

function init() {
    const query_params = new URLSearchParams(location.search);
    if (query_params.get("overdrive")) {
	document.getElementById("overdrive").value = query_params.get("overdrive");
    }

    let book_selector = "tr";
    let book_events = book_events_table;
    if (query_params.get("covers")) {
	book_selector = "div.book";
	book_events = book_events_covers;
    }
    Array.from(document.querySelectorAll(book_selector)).map(book_events);
}

init();
