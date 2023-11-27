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
	const container = document.getElementById("container");

	input.addEventListener("input", updateValue);

	function updateValue(e) {
		const url = window.origin + "/api/get.records"+"?opts="+encodeURI(input.value + " format:html_entries");
		httpGet(url, function (response) {
			response = JSON.parse(response);
			if (response["ok"]) {
				container.innerHTML = response["records"];
			}
		});
	}
});