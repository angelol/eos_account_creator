let Eos = require('eosjs');

let httpEndpoint = 'http://api.eosnewyork.io';
let chainId = 'aca376f206b8fc25a6ed44dbdc66547c36c6c33e3a119ffbeaef943642f0e906';
keyProvider = [''];

creator = 'accountcreat';


let newaccount = process.argv[2];
let public_key = process.argv[3];
console.log("newaccount: " + newaccount +"EOL");
console.log("public_key: " + public_key + "EOL");

eos = Eos({httpEndpoint, chainId, keyProvider});
eos.transaction(tr => {
  tr.newaccount({
    creator: creator,
    name: newaccount,
    owner: public_key,
    active: public_key
  })
  tr.buyrambytes({
    payer: creator,
    receiver: newaccount,
    bytes: Number(4000)
  })
  tr.delegatebw({
    from: creator,
    receiver: newaccount,
    stake_net_quantity: '0.1000 EOS',
    stake_cpu_quantity: '0.1000 EOS',
    transfer: 1
  })
}).then((data) => {
  console.log(data.transaction_id);

}).catch((e) => {
    let error = JSON.stringify(e);
    console.log("ERROR: " + error);
    
  });
