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

var allowedit = false;
httpGet(window.origin + "/api/get.allowedit", function(response)
{
	response = JSON.parse(response);
	if (response["ok"]) { allowedit = response["allowedit"]; }
});

document.addEventListener("DOMContentLoaded", function () {
	const input = document.querySelector("input");
	if (input)
	{
		const container = document.getElementById("container");

		input.addEventListener("input", updateRecords);
		let searchParams = new URLSearchParams(window.location.search);
		if (searchParams.get("opts"))
		{
			input.value = decodeURI(searchParams.get("opts"));
			updateRecords();
		}
		
		function updateRecords(e=null) {
			if(input.value)
			{
				const url = window.origin + "/api/get.records"+"?opts="+encodeURI(input.value + " as:html_entries");
				insertUrlParam("opts", encodeURI(input.value));
				var hideedit = false;
				for (const s of input.value.split(" "))
				{
					if(s.startsWith("md:"))
					{
						hideedit = true;
						break;
					}	
				}
				httpGet(url, function (response) {
					response = JSON.parse(response);
					if (response["ok"]) {
						const before_scroll = window.scrollY;
						container.innerHTML = response["records"];
						for(var i = 0; i < container.children.length; i++)
						{
							if (container.children[i].className == "entry" && allowedit && !hideedit)
							{
								var child = container.children[i];
								var edit = document.createElement("button");
								var remove = document.createElement("button");
								edit.style = " border: 0; background: none; box-shadow: none; border-radius: 0px;";
								remove.style = " border: 0; background: none; box-shadow: none; border-radius: 0px;";
								edit.textContent = "✏️";
								remove.textContent = "🗑️";
								const save_func = function (event)
								{
									var date = event.target.parentElement.querySelector(".date");
									var content = event.target.parentElement.querySelector(".content");
									event.target.textContent = "✏️";
									event.target.remove_button.textContent = "🗑️";
									event.target.remove_button.onclick = remove_func;
									event.target.onclick = edit_func;
									date = "'"+date.textContent.trim()+"'";
									const url = window.origin + "/api/edit.record";
									var text = JSON.stringify({"date":date,"text":content.textContent});
									httpPost(url, text, function (response, elem=event.target) { updateRecords(); });
								}
								const cancel_func = function (event)
								{
									event.target.textContent = "🗑️";
									event.target.edit_button.textContent = "✏️";
									event.target.onclick = remove_func;
									event.target.edit_button.onclick = edit_func;
									updateRecords();
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
											event.target.textContent = "💾";
											event.target.remove_button.textContent = "❌";
											event.target.remove_button.onclick = cancel_func;
											event.target.onclick = save_func;
											content.innerHTML = "";
											var pre = document.createElement("pre");
											pre.style = "background: #eee;"
											content.appendChild(pre);
											const [first, ...rest] = response["records"].split("] ");
											pre.textContent = rest.join("] ");
											pre.contentEditable = true;
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
											updateRecords();
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
						if (typeof variable !== 'undefined') { mermaid.run(); }
						window.scrollTo({ top: before_scroll });
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