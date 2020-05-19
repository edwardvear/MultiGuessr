var marker = null;

var map = L.map('MapContainer').setView([51.505, -0.09], 13);
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
    let request_url = "submit_guess" + '?lat=' + lat + '&lng=' + lng;

    var req = new XMLHttpRequest();
    req.addEventListener("load", () => { window.location = window.location.pathname; });
    req.open("GET", request_url);
    req.send();
  } else {
    // TODO create header or something to let the player know
    console.log("Need to place a marker");
  }
}

function handleLeaveClick() {
  var req = new XMLHttpRequest();
  req.addEventListener("load", () => { window.location = window.location.pathname; });
  req.open("GET", "leave_room");
  req.send();
}
