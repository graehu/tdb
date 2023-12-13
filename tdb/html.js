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

function httpPost(theUrl, data, callback) {
	var xmlHttp = new XMLHttpRequest();
	xmlHttp.onreadystatechange = function () {
		if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
			callback(xmlHttp.responseText);
		}
	}
	xmlHttp.open("POST", theUrl, true); // true for asynchronous 
	xmlHttp.setRequestHeader("Content-Type", "application/json");
	// console.log(data);
	xmlHttp.send(data);
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
						for(var i = 0; i < container.children.length; i++)
						{
							if (container.children[i].className == "entry")
							{
								var child = container.children[i];
								var edit = document.createElement("button");
								var remove = document.createElement("button");
								edit.textContent = "edit";
								remove.textContent = "remove";
								edit.onclick = function (event)
								{
									var date = event.target.parentElement.querySelector(".date");
									date = "'"+date.textContent.trim()+"'";
									if (window.confirm("edit " + date + " to say poop?")) {
										const url = window.origin + "/api/edit.record";
										httpPost(url, JSON.stringify({ "date": date, "text": "poop" }), function (response) {
											updateValue();
										});
									}
								}; // /api/edit.record
								remove.onclick = function (event)
								{
									var date = event.target.parentElement.querySelector(".date");
									date = "'"+date.textContent.trim()+"'";
									if (window.confirm("remove "+date+" from tdb?"))
									{
										const url = window.origin + "/api/remove.record";
										httpPost(url, JSON.stringify({"date":date}), function(response) {
												updateValue();
										});
									}

								}; // /api/remove.record
								child.appendChild(edit);
								child.appendChild(remove);
							}
						}
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