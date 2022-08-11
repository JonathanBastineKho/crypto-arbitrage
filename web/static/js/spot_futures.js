var socket = io();
socket.on('connect', function() {
    console.log("connection established");
});

socket.on('arbitrage_data', function(data){
    var found = false;
    var table = document.getElementById('main_table');
    var tr = table.getElementsByTagName('tr');

    for (i=0; i < tr.length; i++){
        var td1 = tr[i].getElementsByTagName('td')[0];
        if(typeof td1 == 'undefined'){
            td1 = -1
        }
        if (td1.textContent == data['coin']){
            found = true;
            tr[i].getElementsByTagName('td')[1] = data['futures_price'];
            tr[i].getElementsByTagName('td')[2] = data['spot_price'];
            tr[i].getElementsByTagName('td')[3] = data['futures_market'];
            tr[i].getElementsByTagName('td')[4] = data['spot_market'];
            tr[i].getElementsByTagName('td')[5] = data['funding_rate'];
            break;
        }
    }

    if (found == false){
        var row = table.insertRow(-1);
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        var cell3 = row.insertCell(2);
        var cell4 = row.insertCell(3);
        var cell5 = row.insertCell(4);
        var cell6 = row.insertCell(5);
        cell1.innerHTML = data['coin'];
        cell2.innerHTML = data['futures_price'];
        cell3.innerHTML = data['spot_price'];
        cell4.innerHTML = data['futures_market'];
        cell5.innerHTML = data['spot_market'];
        cell6.innerHTML = data['funding_rate'];
    }
})