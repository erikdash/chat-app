var timeoutID;
var timeout = 1000;


function setup() {
	document.getElementById("messageSend").addEventListener("click", postMessage, true);
	document.getElementById("messageText").addEventListener("keydown", function(event){ //enter key has same function as messageSend button
		if(event.keyCode == 13) {
			document.getElementById("messageSend").click();
			event.preventDefault();
		}
		return false;
	} );
    timeoutID = window.setTimeout(poller, timeout);
}

function postMessage() {
    var httpRequest = new XMLHttpRequest();

	if (!httpRequest) {
		alert('Failure to create an XMLHTTP instance');
		return false;
	}
    var messageText = document.getElementById("messageText").value;
	message = [username, messageText, room_id]
	httpRequest.onreadystatechange = function() { handlePost(httpRequest, message) };

    httpRequest.open("POST", "/new_message/");
	httpRequest.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

	var data;
	data = "messageText=" + messageText + "&username=" + username + "&room_id=" + room_id;

	httpRequest.send(data);
}

function handlePost(httpRequest, message) {
	if (httpRequest.readyState === XMLHttpRequest.DONE) {
		if (httpRequest.status === 200) {
			clearInput();
		} else {
			alert("There was a problem with the post request.");
		}
	}
}

function poller() {
	var httpRequest = new XMLHttpRequest();

	if (!httpRequest) {
		alert('Giving up. Cannot create an XMLHTTP instance');
		return false;
	}

	httpRequest.onreadystatechange = function() { handlePoll(httpRequest) };
	httpRequest.open("GET", "/messages/");
	httpRequest.send();
}

function handlePoll(httpRequest) {
	if (httpRequest.readyState === XMLHttpRequest.DONE) {
		if (httpRequest.status === 200) {
			var new_messages = JSON.parse(httpRequest.responseText);
			if(new_messages.length > 0 && new_messages[0]["author"] == "exit") {
				alert("room deleted");
				window.location.replace('/leaveroom/'); //kick the user out of the deleted room
			}
			else {
	            for (var i = 0; i < new_messages.length; i++) {
					addMessage(new_messages[i]["author"] + ": " + new_messages[i]["text"]);
				}

				timeoutID = window.setTimeout(poller, timeout);
			}

		} else {
			alert("There was a problem with the poll request. You'll need to refresh the page to recieve updates again!");
		}
	}
}

function clearInput() {
	document.getElementById("messageText").value = "";
}

function addMessage(messageData) {
	var listRef = document.getElementById("messagelist");
	var newListElement = document.createElement("li");
	newListElement.appendChild(document.createTextNode(messageData));
    listRef.appendChild(newListElement);
}

window.addEventListener("load", setup, true);
