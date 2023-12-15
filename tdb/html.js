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
								const save_func = function (event)
								{
									var date = event.target.parentElement.querySelector(".date");
									var content = event.target.parentElement.querySelector(".content");
									event.target.textContent = "edit";
									event.target.remove_button = "remove";
									event.target.remove_button.onclick = remove_func;
									event.target.onclick = edit_func;
									content.contentEditable = false;
									date = "'"+date.textContent.trim()+"'";
									const url = window.origin + "/api/edit.record";
									httpPost(url, JSON.stringify({ "date": date, "text": content.textContent }), function (response) {updateValue();});
								}
								const cancel_func = function (event)
								{
									var content = event.target.parentElement.querySelector(".content");
									event.target.textContent = "remove";
									event.target.edit_button.textContent = "edit";
									event.target.onclick = remove_func;
									event.target.edit_button.onclick = edit_func;
									content.contentEditable = false;
									updateValue();
								}
								const edit_func = function (event)
								{
									var date = event.target.parentElement.querySelector(".date");
									date = "'"+date.textContent.trim()+"'";
									const url = window.origin + "/api/get.records" + "?opts=" + encodeURI(date);
									httpGet(url, function(response)
									{
										response = JSON.parse(response);
										if(response["ok"])
										{
											var content = event.target.parentElement.querySelector(".content");
											event.target.textContent = "save";
											event.target.remove_button.textContent = "cancel";
											event.target.remove_button.onclick = cancel_func;
											event.target.onclick = save_func;
											content.innerHTML = "";
											var pre = document.createElement("pre");
											pre.style = "background: #eee;"
											pre.id = "record_pre";
											content.appendChild(pre);
											const [first, ...rest] = response["records"].split("] ");
											pre.textContent = rest.join("] ");
											content.contentEditable = true;
										}
									});
								}; // /api/edit.record
								const remove_func = function (event)
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
								edit.onclick = edit_func;
								edit.remove_button = remove;
								remove.onclick = remove_func;
								remove.edit_button = edit;
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