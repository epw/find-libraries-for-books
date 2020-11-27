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

function download_books() {
  download_csv_file(["title", "author", "overdrive", "hoopla", "other"],
    books_json, "table.csv");
}

async function record_hide_book(tr) {
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

function hide_book(e) {
  for (let el of e.path) {
    if (el.tagName == "TR") {
      record_hide_book(el);
      el.parentElement.removeChild(el);
      break;
    }
  }
}

function book_events(tr) {
  if (!tr.querySelector("td")) {
    return;
  }
  tr.querySelector("td.hide").addEventListener("click", hide_book);
}
  
function init() {
    const query_params = new URLSearchParams(location.search);
    if (query_params.get("overdrive")) {
	document.getElementById("overdrive").value = query_params.get("overdrive");
    }

    Array.from(document.querySelectorAll("tr")).map(book_events);
}

init();
