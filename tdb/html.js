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
	if (input)
	{
		const container = document.getElementById("container");

		input.addEventListener("input", updateValue);
		let searchParams = new URLSearchParams(window.location.search);
		if (searchParams.get("opts"))
		{
			input.value = decodeURI(searchParams.get("opts"));
			updateValue();
		}
		
		function updateValue(e=null) {
			if(input.value)
			{
				const url = window.origin + "/api/get.records"+"?opts="+encodeURI(input.value + " as:html_entries");
				insertUrlParam("opts", encodeURI(input.value));
				httpGet(url, function (response) {
					response = JSON.parse(response);
					if (response["ok"]) {
						container.innerHTML = response["records"];
						if (mermaid) { mermaid.run(); }
					}
				});
			}
			else
			{
				removeUrlParam("opts");
			}
		}
	}
});

function removeUrlParam(key) {
	if (history.pushState) {
		let searchParams = new URLSearchParams(window.location.search);
		searchParams.delete(key);
		const param_str = searchParams.toString() ? '?'+searchParams.toString() : "";
		let newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + param_str;
		window.history.pushState({ path: newurl }, '', newurl);
	}
}
function insertUrlParam(key, value) {
	if (history.pushState) {
		let searchParams = new URLSearchParams(window.location.search);
		searchParams.set(key, value);
		const param_str = searchParams.toString() ? '?' + searchParams.toString() : "";
		let newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + param_str;
		window.history.pushState({ path: newurl }, '', newurl);
	}
}