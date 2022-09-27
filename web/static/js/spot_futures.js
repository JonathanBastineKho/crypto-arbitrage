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
            )
    // Edit values
    } else {
        row.data()[1] = data['futures_price'].toFixed(5);
        row.data()[2] = data['spot_price'].toFixed(5);
        row.data()[5] = data['funding_rate'].toFixed(6);
        row.data()[6] = data['cum_7_day'].toFixed(6);
        row.data()[7] = data['cum_30_day'].toFixed(6);
        row.data(row.data());
    }
})
setInterval(function(){
    main_table.data().draw(false);
}, 1000);

// Modal Data

var modalIntervalID;
main_table.on('click', 'tbody tr', function(){
    $("#ModalCenter").modal('show');

    var data = main_table.row(this).data();
    modalIntervalID = setInterval(function(){
        $("#ModalLongTitle").text(data[0]);
        $("#futures_price").text(`Futures price: ${data[1]}`);
        $("#spot_price").text(`Spot price: ${data[2]}`);
        $("#funding_rate").text(`Funding rate: ${data[5]}`);
    }, 500);

    fetch(`/test/${data[3]}/${data[0]}`)
    .then(response => response.json())
    .then(data => {
        var DATA_COUNT = 90;
        var ctx = document.getElementById('chart').getContext('2d');
        var labels = [];
            for (let i = 0; i < DATA_COUNT; ++i) {
            labels.push(i);
        }
        var chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Funding Rate',
                    data: data,
                    fill: false,
                    borderColor: 'rgb(75, 192, 192)',
                }]
            },
            options: {
                scales: {
                    y: {
                        min: Math.min(...data) - 0.0005,
                        max: Math.max(...data) + 0.0005
                    },
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context){
                                return `${context.dataset.label}: ${context.parsed.y}`;
                            }
                        }
                    }
                }
            },
        });
    });
});

$("#ModalCenter").on('hidden.bs.modal', function(){
    clearInterval(modalIntervalID);
    $("#ModalLongTitle").text("Loading");
    $("#futures_price").text("Loading");
    $('#chart').remove();
    $('.modal-body').prepend('<canvas id="chart" width="700" height="500"><canvas>');
});