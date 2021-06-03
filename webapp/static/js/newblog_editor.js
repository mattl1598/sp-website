var xhr = new XMLHttpRequest();

// dealing with timezones
function localeToUTC(stringIn) {
	let date_obj = new Date(stringIn);
	return date_obj.toISOString().slice(0, 16);
}

function utcToLocale(stringIn) {
	let date_obj = new Date(stringIn);
	let offset = new Date().getTimezoneOffset();
	date_obj.setMinutes(date_obj.getMinutes() - 2*offset);
	return date_obj.toISOString().slice(0, 16);
}

function save_blog() {
	let savable = true;
	savable *= (title.value !== "");
	savable *= (raw.value !== "");
	savable *= (date.value !== "");

	if (savable){
		xhr.open("POST", "/blog_save", true);
		xhr.setRequestHeader('Content-Type', 'application/json');
		xhr.send(JSON.stringify({
			title: title.value,
		    content: raw.value,
			author: user_id
		}));

		xhr.onload = function() {
			if (xhr.status !== 200) { // analyze HTTP status of the response
				alert(`Error ${xhr.status}: ${xhr.statusText}`); // e.g. 404: Not Found
			} else { // show the result
				console.log(xhr.response)
				document.location.href = "/manage_blog/editor?post=" + xhr.response;
			}
		}
	}
}

function update_markdown() {
	rendered.innerHTML = marked(raw.value);
}