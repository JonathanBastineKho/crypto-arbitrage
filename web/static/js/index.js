var socket = io();
socket.on('connect', function() {
    console.log("connection established");
});

socket.on('my_response', function(data){
    console.log(data);
});