let eos = require('./common').eos;

function main() {
  let creator = 'accountcreat';
  let hash = process.argv[2];
  let owner_key = process.argv[3];
  let active_key = process.argv[4];  
  
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

