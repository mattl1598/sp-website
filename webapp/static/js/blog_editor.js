const socket = io("/manage_blog/edit", { transports: ["websocket"] });

socket.on('connect', function() {
    socket.emit('join', {"room": id, "user_id": user_id})
});

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

function update_markdown() {
	// WEBSOCKET METHOD
	let data = {
		user_id: user_id,
		id: id,
		date: localeToUTC(date.value),
		title: title.value,
	    content: raw.value
	}
	rendered.innerHTML = marked(raw.value);
	socket.emit('edit', data)
}

socket.on('updated', function (data) {
	if (data["user_id"] !== user_id){
		title.value = data["title"];
		raw.value = data["content"];
		rendered.innerHTML = marked(raw.value);
	}
});
