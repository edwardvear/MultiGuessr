var marker = null;

var map = L.map('MapContainer').setView([51.505, -0.09], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

var req = new XMLHttpRequest();
req.addEventListener("load", loadResults);
req.open("GET", "results/data");
req.send();

function loadResults() {
  var resp = JSON.parse(this.responseText);
  console.log(resp);
  var guesses = resp.guesses;
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
  
  // Scoreboard
  var scoreboard = document.getElementById('Scoreboard')
  for (dist of resp.dists) {
    var row = scoreboard.insertRow(-1);
    var distance = row.insertCell(0);
    var name = row.insertCell(1);
    distance.innerHTML = dist.dist;
    name.innerHTML = dist.name;
  }
}

function handleResetClick() {
  var req = new XMLHttpRequest();
  req.addEventListener("load", () => { window.location = window.location.pathname; });
  req.open("GET", "reset_room");
  req.send();
  console.log("Reset room");
}
