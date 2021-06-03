document.addEventListener("DOMContentLoaded", function() {
	const dropArea = document.getElementById(`dropArea`);

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
		dropArea.addEventListener(eventName, preventDefaults, false)
	});


	['dragenter', 'dragover'].forEach(eventName => {
		dropArea.addEventListener(eventName, highlight, false)
	});

	['dragleave', 'drop'].forEach(eventName => {
		dropArea.addEventListener(eventName, unhighlight, false)
	});

	dropArea.addEventListener('drop', handleDrop, false)
});

function highlight(e) {
	dropArea.classList.add('highlight')
}

function unhighlight(e) {
	dropArea.classList.remove('highlight')
}

function preventDefaults(e) {
	e.preventDefault()
	e.stopPropagation()
}
``
function handleDrop(e) {
	let dt = e.dataTransfer
	let files = dt.files
	let fileElem = document.getElementById(`fileElem`);
	fileElem.files = files
	fileSelected(files[0])
}

function uploadFile(file) {
	let url = '/manage_blog/upload'
	let formData = new FormData()

	formData.append('file', file)

	fetch(url, {
		method: 'POST',
		body: formData
	})
	.then((data) => { /* Done. Inform the user */
		return data.text()
	}).then(function(data) {
        console.log(data); // this will be a string
		window.location.href = "/manage_blog/editor?post=".concat(data);
	}).catch(() => { /* Error. Inform the user */ })
}

function upload_click() {
	let fileElem = document.getElementById(`fileElem`);
	uploadFile(fileElem.files[0]);
}

function fileSelected(file) {
	if (file !== null) {
		let file_preview = document.getElementById(`file_preview`);
		file_preview.classList.remove("hidden_flex");
		let filename = document.getElementById(`filename`);
		filename.innerHTML = file.name;
	} else {
		let file_preview = document.getElementById(`file_preview`);
		file_preview.classList.add("hidden_flex");
		let filename = document.getElementById(`filename`);
		filename.innerHTML = "";
	}
}
