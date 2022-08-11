var socket = io();
socket.on('connect', function() {
    console.log("connection established");
});

socket.on('spot_data', function(data){
    var found = false;
    var table = document.getElementById('main_table');
    var tr = table.getElementsByTagName("tr");

    for(i=0; i < tr.length; i++){
        var td1 = tr[i].getElementsByTagName('td')[0];
        var td2 = tr[i].getElementsByTagName('td')[1];
        if(typeof td1 == 'undefined'){
            td1 = -1
        }
        if(typeof td2 == 'undefined'){  
            td2 = -1
        }
        if (td1.textContent  == data['coin'] && td2.textContent == data['market']){
            found = true;
            tr[i].getElementsByTagName('td')[2] = data['bid'];
            tr[i].getElementsByTagName('td')[3] = data['ask'];
            break;
        }
    }
    if (found == false){
        // Insert new row
        var row = table.insertRow(-1);
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        var cell3 = row.insertCell(2);
        var cell4 = row.insertCell(3);
        cell1.innerHTML = data['coin'];
        cell2.innerHTML = data['market'];
        cell3.innerHTML = data['bid'];
        cell4.innerHTML = data['ask'];
    }
});