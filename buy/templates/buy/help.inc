<h4>What are those keys and how do I generate them?</h4>
  In order to access your new EOS account, you will need two key pairs, owner and active. Each key pair consists of a private key and a public key. The public key is safe to give out and will be publicly visible in the blockchain. The private key must be kept secret and stored securely.
  <p>Here are several generators you can use:
    <ul>
      <li><a href="https://eosrio.io/simpleos/" target="_new">SimplEOS</a> (Easy to use desktop wallet, supports generating keys offline)
      <li><a href="https://eoskey.io/" target="_new">EOSKEY</a> (offline key generator, easy to use, but no wallet included)</li>
      <li><a href="https://get-scatter.com/" target="_new">Scatter</a> (Chrome extension, recommended for daily use)</li>
      <li><a href="https://github.com/EOSIO/eos/wiki/Tutorial-Comprehensive-Accounts-and-Wallets" target="_new">Cleos</a>  (Official wallet by Block.one but command line tool, only for advanced users)</li>
      <li><a href="https://ipfs.io/ipfs/QmakCmYZf3SSmBbRWexBgAULUMg2W72eXEouxapHkPXJaH" target="_new">Simple javascript generator</a> (easiest to use but be careful)</li>
    </ul>
    
    </p>

<h4>Why do I need two keys, owner and active?</h4>
<p>The active key is the one you're gonna use for daily operations like interacting with dApps or money transfers. This would be the key that you're gonna import into your favorite wallet or Scatter if you want to interact with dApps. If this key gets compromised, you will be able to regain control of your account using the owner key and cancel outgoing transfers that haven't gone through yet.<p>
<p>The owner key is very important as whoever holds it is the real owner of the account. You will need it if you want to transfer control of the account to someone else. You can also use it to change the keys of your account. You can also use it to prove ownership of your account in case your active key gets compromised. That's why you should generate this key in an offline key generator in only store it in cold storage. 
</p>