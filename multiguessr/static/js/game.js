var marker = null;

var map = L.map('MapContainer').setView([51.505, -0.09], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

map.on('click', handleMapClick);


function handleMapClick(e) {
  if (marker) {
    marker.setLatLng(e.latlng);
  } else {
    marker = L.marker(e.latlng).addTo(map);
  }
}

function handleSubmitClick() {
  if (marker) {
    lat = marker.getLatLng().lat;
    lng = marker.getLatLng().lng;

    var xhr = new XMLHttpRequest();
    xhr.addEventListener("load", () => { window.location = window.location.pathname; });
    xhr.open("POST", "submit_guess");
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send("lat=" + lat + "&lng=" + lng);
  } else {
    // TODO create header or something to let the player know
    console.log("Need to place a marker");
  }
}

function handleLeaveClick() {
  var xhr = new XMLHttpRequest();
  xhr.addEventListener("load", () => { window.location = window.location.pathname; });
  xhr.open("GET", "leave_room");
  xhr.send();
}
