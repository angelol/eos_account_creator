{% load i18n %}
<h4>{% trans "What are those keys and how do I generate them?" %}</h4>
  {% trans "In order to access your new EOS account, you will need two key pairs, owner and active. Each key pair consists of a private key and a public key. The public key is safe to give out and will be publicly visible in the blockchain. The private key must be kept secret and stored securely." %}
  <p>{% trans "Here are several generators you can use:" %}
    <ul>
      <li><a href="https://eosrio.io/simpleos/" target="_new">SimplEOS</a> ({% trans "Easy to use desktop wallet, supports generating keys offline" %})</li>
      <li><a href="https://eoskey.io/" target="_new">EOSKEY</a> ({% trans "offline key generator, easy to use, but no wallet included" %})</li>
      <li><a href="https://get-scatter.com/" target="_new">Scatter</a> ({% trans "Chrome extension, recommended for daily use" %})</li>
      <li><a href="https://github.com/EOSIO/eos/wiki/Tutorial-Comprehensive-Accounts-and-Wallets" target="_new">Cleos</a>  ({% trans "Official wallet by Block.one but command line tool, only for advanced users" %})</li>
      <li><a href="https://ipfs.io/ipfs/QmW4XxaEg8cWsYisfjnjqLFi1MbHMYjt7nbCh8ZHwgg9c2" target="_blank">{% trans "Simple javascript generator" %}</a> ({% trans "easiest to use" %})</li>
    </ul>

    </p>