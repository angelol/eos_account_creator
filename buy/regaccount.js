let fs = require('fs');
let Eos = require('eosjs');
let ecc = require('eosjs-ecc');
let crypto = require('crypto');

let httpEndpoint = 'https://node1.eosvibes.io';
let chainId = 'aca376f206b8fc25a6ed44dbdc66547c36c6c33e3a119ffbeaef943642f0e906';

let creator = 'accountcreat';
var secret = fs.readFileSync('buy/key.txt', {encoding: 'utf8'});
let keyProvider = [secret];
let eos = Eos({httpEndpoint, chainId, keyProvider});


function main() {
  let creator = 'accountcreat';

  let hash = process.argv[2];
  let owner_key = process.argv[3];
  let active_key = process.argv[4];  
  console.log(hash);
  console.log(owner_key);
  console.log(active_key);
  eos.transaction(
    {
      actions: [
        {
          account: creator,
          name: 'regaccount',
          authorization: [{
            actor: creator,
            permission: 'active'
          }],
          data: {
            sender: creator,
            hash: hash,
            owner_key: owner_key,
            active_key: active_key
          }
        }
      ]
    }
  ).then((data) => {
    console.log(data.transaction_id);

  }).catch((e) => {
      let error = JSON.stringify(e);
      console.log("ERROR: " + error);
      
    });

}

main();

