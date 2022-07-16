var socket = io();
socket.on('connect', function() {
    console.log("connection established");
});