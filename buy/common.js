let fs = require('fs');
let Eos = require('eosjs');

let httpEndpoint = 'https://eos.greymass.com';
let chainId = 'aca376f206b8fc25a6ed44dbdc66547c36c6c33e3a119ffbeaef943642f0e906';

var secret = fs.readFileSync('buy/key.txt', {encoding: 'utf8'});
let keyProvider = [secret];
let eos = Eos({httpEndpoint, chainId, keyProvider});

module.exports = {
  eos: eos,
  public_key: 'EOS7ss3n5jGaYSNqRdZqZreXbYhUrcgyf72w6gGqtRJSEFy5BWEA5'
};
