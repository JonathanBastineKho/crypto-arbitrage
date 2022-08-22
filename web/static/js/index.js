var main_table = $('#main_table').DataTable({
    "responsive" : true
});
var socket = io();
socket.on('connect', function() {
    console.log("connection established");
});

socket.on('spot_data', function(data){
    // Search coin
    var row = main_table.row(function(idx, rowdata, node){
        return rowdata[0] == data['coin'] ? true : false;
    });
    // Check if coin available
    if(typeof row.data() == 'undefined'){
        main_table.row.add(
            [data['coin'], data['market'], 
            data['bid'], data['ask']]
            ).draw();
    } else {
        row.data()[2] = data['bid'];
        row.data()[3] = data['ask'];
        row.data(row.data()).draw();
    }
});