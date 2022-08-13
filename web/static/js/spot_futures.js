var main_table = $('#main_table').DataTable();
var socket = io();
socket.on('connect', function() {
    console.log("connection established");
});

socket.on('arbitrage_data', function(data){
    // Search coin
    var row = main_table.row(function(idx, rowdata, node){
        return rowdata[0] == data['coin'] ? true : false;
    });
    // Check if coin available
    if(typeof row.data() == 'undefined'){
        main_table.row.add(
            [data['coin'], data['futures_price'], 
            data['spot_price'], data['futures_market'],
            data['spot_market'], data['funding_rate']]
            ).draw();
    // Edit values
    } else {
        row.data()[1] = data['futures_price'];
        row.data()[2] = data['spot_price'];
        row.data()[5] = data['funding_rate'];
        row.data(row.data()).draw();
    }
})