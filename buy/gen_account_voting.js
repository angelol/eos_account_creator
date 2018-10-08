const common = require('./common')
const eos = common.eos;
const public_key = common.public_key;

const creator = 'accountcreat';
const newaccount = process.argv[2];
const owner_key = process.argv[3];
const active_key = process.argv[4];
const voting_key = process.argv[5];

create_account()
.then((data) => {
  console.log("Account created ", data.transaction_id);
  update_auth()
  .then((data) => {
    console.log("Permissions updated ", data.transaction_id);
  })
  .catch((error) => {
      console.log("ERROR while updating permissions: " + error);
  });
}).catch((error) => {
    console.log("ERROR: " + error);
});

function create_account() {  
  return eos.transaction(tr => {
    tr.newaccount({
      creator: creator,
      name: newaccount,
      owner: public_key,
      active: public_key
    })
    tr.buyrambytes({
      payer: creator,
      receiver: newaccount,
      bytes: 3000
    })
    tr.delegatebw({
      from: creator,
      receiver: newaccount,
      stake_net_quantity: '0.0500 EOS',
      stake_cpu_quantity: '0.1500 EOS',
      transfer: 0
    })
  })
}

// update_auth()

function update_auth() {
  return eos.transaction({actions: [{
    account: 'eosio',
    name: 'updateauth',
    authorization: [{
      actor: newaccount,
      permission: 'owner',
    }],
    data: {
      account: newaccount,
      permission: 'voting',
      parent: 'active',
      auth: { 
        "threshold": 1, 
        "keys": [ { 
          "key": voting_key, 
          "weight": 1 } ], 
        "accounts": [], 
        "waits": [] 
      }
    }
  }]})
  .then(data => {
    return eos.transaction({actions: [{
      account: 'eosio',
      name: 'linkauth',
      authorization: [{
        actor: newaccount,
        permission: 'owner',
      }],
      data: {
        account: newaccount,
        code: 'eosio',
        'type': 'voteproducer',
        requirement: 'voting'
      }
    }]})
  })
  .then(data => {
    return eos.transaction({actions: [{
      account: 'eosio',
      name: 'updateauth',
      authorization: [{
        actor: newaccount,
        permission: 'owner',
      }],
      data: {
        account: newaccount,
        permission: 'active',
        parent: 'owner',
        auth: { 
          "threshold": 1, 
          "keys": [ { 
            "key": active_key, 
            "weight": 1 } ], 
          "accounts": [], 
          "waits": [] 
        }
      }
    }]})
  })
  .then(data => {
    return eos.transaction({actions: [{
      account: 'eosio',
      name: 'updateauth',
      authorization: [{
        actor: newaccount,
        permission: 'owner',
      }],
      data: {
        account: newaccount,
        permission: 'owner',
        parent: '',
        auth: { 
          "threshold": 1, 
          "keys": [ { 
            "key": owner_key, 
            "weight": 1 } ], 
          "accounts": [], 
          "waits": [] 
        }
      }
    }]})
  })
}
