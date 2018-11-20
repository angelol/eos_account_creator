let eos = require('./common').eos;

let creator = 'accountcreat';
let newaccount = process.argv[2];
let owner_key = process.argv[3];
let active_key = process.argv[4];

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
    bytes: 3000
  })
  tr.buyrambytes({
    payer: creator,
    receiver: creator,
    bytes: 160
  })
  tr.delegatebw({
    from: creator,
    receiver: newaccount,
    stake_net_quantity: '0.0500 EOS',
    stake_cpu_quantity: '0.1500 EOS',
    transfer: 0
  });
}).then((data) => {
  console.log(data.transaction_id);
}).catch((e) => {
    let error = JSON.stringify(e);
    console.log("ERROR: " + error);
});
