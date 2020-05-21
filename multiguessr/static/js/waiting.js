function setupSocket() {
  let roomname = document.getElementById("roomname").value;
  const socket = io('/' + roomname);
  socket.on('results_ready', function() {
    location.reload();
  });
}
