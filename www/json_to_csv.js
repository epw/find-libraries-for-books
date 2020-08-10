function convert_to_csv(colnames, array) {
    const str = [];

    for (let el of array) {
	let line = [];
	for (let col of colnames) {
	    line.push(el[col]);
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
