let eos = require('./common').eos;


function main() {
  let contract = 'accountcreat';
  
  eos.transaction(
    {
      actions: [
        {
          account: contract,
          name: 'clearexpired',
          authorization: [{
            actor: contract,
            permission: 'active'
          }],
          data: {
            sender: contract
          }
        }
      ]
    }
  ).then((data) => {
    console.log(data);

  }).catch((e) => {
      let error = JSON.stringify(e);
      console.log("ERROR: " + error);
      
    });

}

main();

