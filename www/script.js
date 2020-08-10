function download_books() {
    download_csv_file(["title", "author", "overdrive", "hoopla", "other"],
		      books_json, "table.csv");
}

function init() {
}

init();
