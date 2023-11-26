function httpGet(theUrl, callback) {
	var xmlHttp = new XMLHttpRequest();
	xmlHttp.onreadystatechange = function () {
		if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
			callback(xmlHttp.responseText);
		}
	}
	xmlHttp.open("GET", theUrl, true); // true for asynchronous 
	xmlHttp.send(null);
};
document.addEventListener("DOMContentLoaded", function () {
	const input = document.querySelector("input");

	input.addEventListener("input", updateValue);

	function updateValue(e) {
		console.log("this is happening?");
		const url = "http://localhost:8000/api/get.records?opts=" + encodeURI(input.value);
		httpGet(url, function (response) {
			response = JSON.parse(response);
			if (response["ok"]) {
				console.log(response);
			}
		});
		console.log(url);
	}
});