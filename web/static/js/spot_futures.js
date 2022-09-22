var main_table = $('#main_table').DataTable({
    "responsive" : true
});
var socket = io();
socket.on('connect', function() {
    console.log("connection established");
});

socket.on('arbitrage_data', function(data){
    // Search coin
    var row = main_table.row(function(idx, rowdata, node){
        return rowdata[0] == data['coin'] && rowdata[3] == data["futures_market"] && rowdata[4] == data["spot_market"] ? true : false;
    });
    // Check if coin available
    if(typeof row.data() == 'undefined'){
        main_table.row.add(
            [data['coin'], data['futures_price'].toFixed(5), 
            data['spot_price'].toFixed(5), data['futures_market'],
            data['spot_market'], data['funding_rate'].toFixed(6),
            data['cum_7_day'].toFixed(6), data['cum_30_day'].toFixed(6)]
            ).draw(false);
    // Edit values
    } else {
        row.data()[1] = data['futures_price'].toFixed(5);
        row.data()[2] = data['spot_price'].toFixed(5);
        row.data()[5] = data['funding_rate'].toFixed(6);
        row.data()[6] = data['cum_7_day'].toFixed(6);
        row.data()[7] = data['cum_30_day'].toFixed(6);
        row.data(row.data()).draw(false);
    }
})