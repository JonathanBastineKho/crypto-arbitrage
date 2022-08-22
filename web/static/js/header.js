var socket = io();
socket.on('user_balance', function(data){
    $('#usd_balance').html(`USD: ${data['USD']}`);
    $('#usdt_balance').html(`USDT: ${data['USDT']}`);
    $('#busd_balance').html(`BUSD: ${data['BUSD']}`);
})