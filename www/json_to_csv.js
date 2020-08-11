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

function convert_to_csv(colnames, array) {
  const str = [];

  for (let el of array) {
    let line = [];
    for (let col of colnames) {
      if (typeof (el[col]) == "string" &&
        (el[col].indexOf(",") != -1 || el[col].indexOf("\n") != -1)) {
        line.push('"' + el[col] + '"');
      } else {
        line.push(el[col]);
      }
    }
    str.push(line.join(","));
  }

  return str.join("\n");
}

function download_csv_file(colnames, array, filename) {
  const csv = convert_to_csv(colnames, array);

  const blob = new Blob([colnames.join(","), "\n", csv, "\n"],
    { type: "text/csv;charset=utf-8;" });
  if (navigator.msSaveBlob) { // IE 10+
    navigator.msSaveBlob(blob, filename);
  } else {
    const link = document.createElement("a");
    if (link.download == undefined) {
      console.error("Link downloads not supported, sorry.");
    } else {
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }
}
