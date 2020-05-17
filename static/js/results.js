var marker = null;

var map = L.map('MapContainer').setView([51.505, -0.09], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

var req = new XMLHttpRequest();
req.addEventListener("load", loadMarkers);
req.open("GET", "results/data");
req.send();

function loadMarkers() {
  console.log("Got Data!");
  console.log(this.responseText);
  var resp = JSON.parse(this.responseText);
  var guesses = resp.guesses;
  console.log(guesses[0]);
  for (var guess of guesses) {
    let latlng = L.latLng(guess.lat, guess.lng);
    L.marker(latlng)
      .bindTooltip(guess.name,
        {
          permanent: true,
          direction: 'bottom'
        }
      )
      .addTo(map);
  }

  let latlng = L.latLng(resp.answer.lat, resp.answer.lng);
  L.marker(latlng)
      .bindTooltip('Answer',
        {
          permanent: true,
          direction: 'bottom'
        }
      )
      .addTo(map);
}


function handleMapClick(e) {
  if (marker) {
    marker.setLatLng(e.latlng);
  } else {
    marker = L.marker(e.latlng).addTo(map);
  }
}

function handleSubmitClick() {
  if (marker) {
    let url = window.location.href;
    lat = marker.getLatLng().lat;
    lng = marker.getLatLng().lng;
    let new_url = url + '?lat=' + lat + '&lng=' + lng;
    // Maybe use url.location.replace to prevent player from going back after submitting
    window.location.replace(new_url);
  } else {
    console.log("Need to place a marker");
  }
}
