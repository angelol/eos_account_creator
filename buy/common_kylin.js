let fs = require('fs');
let Eos = require('eosjs');

let httpEndpoint = 'https://api-kylin.eosasia.one';
let chainId = '5fff1dae8dc8e2fc4d5b23b2c7665c97f9e9d8edf2b6485a86ba311c25639191';

var secret = fs.readFileSync('buy/key.txt', {encoding: 'utf8'});
let keyProvider = [secret];
let eos = Eos({httpEndpoint, chainId, keyProvider});

module.exports = {
  eos: eos,
  public_key: 'EOS7R7sj7qvGPCT8ZutguKJeW6EsptBuHMTtXrQNEAyyBSzdN18N8'
};
