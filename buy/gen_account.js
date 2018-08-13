let Eos = require('eosjs');
let fs = require('fs');

let httpEndpoint = 'https://api.eosnewyork.io';
let chainId = 'aca376f206b8fc25a6ed44dbdc66547c36c6c33e3a119ffbeaef943642f0e906';

let creator = 'accountcreat';


let newaccount = process.argv[2];
let owner_key = process.argv[3];
let active_key = process.argv[4];

var secret = fs.readFileSync('buy/key.txt', {encoding: 'utf8'});
let keyProvider = [secret];

eos = Eos({httpEndpoint, chainId, keyProvider});
eos.transaction(tr => {
  tr.newaccount({
    creator: creator,
    name: newaccount,
    owner: owner_key,
    active: active_key
  })
  tr.buyrambytes({
    payer: creator,
    receiver: newaccount,
    bytes: 4000
  })
  tr.delegatebw({
    from: creator,
    receiver: newaccount,
    stake_net_quantity: '0.0500 EOS',
    stake_cpu_quantity: '0.1500 EOS',
    transfer: 1
  })
}).then((data) => {
  console.log(data.transaction_id);

}).catch((e) => {
    let error = JSON.stringify(e);
    console.log("ERROR: " + error);
    
  });
