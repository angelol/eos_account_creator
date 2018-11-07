Array.prototype.insert = function ( index, item ) {
  this.splice( index, 0, item );
};

let blacklist = [];
function is_valid_public_key(key) {
	key = key.trim();
	if(blacklist.indexOf(key) != -1) {
		return false;
	}
	return eosjs_ecc.isValidPublic(key);
}
function is_valid_account_name(account_name) {
		let re = new RegExp("^([a-z1-5]){12}$");
		return re.test(account_name);
}

new Vue({
  el: '#app',
  data() {
    return {
      account: {
        name: '',
        active: '',
        owner: '',
        voting: ''
      },
      userConfirmation: false,
      q: "",
      scatter: null,
      msg: null,
      identity: null,
      tx: null,
      eos: null,
      eosOptions: {
	      httpEndpoint: 'https://eos.greymass.com',
        verbose: false,
      },
      eosAccount: null,
      eosError: null,
      eup: {},
      network: {
        name: "EOS Mainnet",
        protocol: 'https',
        blockchain: 'eos',
        host: 'eos.greymass.com',
        port: 443,
        chainId: 'aca376f206b8fc25a6ed44dbdc66547c36c6c33e3a119ffbeaef943642f0e906'
      }
    }
  },  
  mounted() {
    this.eos = EosApi(this.eosOptions)
  },
  methods: {
    getPermission: function(perm) {
      return this.eosAccount.permissions.find(p => p.perm_name === perm)
    },
    checkForm: function () {
      if(!this.isEmpty(this.account.active)) {
        if( !(is_valid_public_key(this.account.active) || is_valid_account_name(this.account.active))) {
          this.msg = {
            type: "error",
            message: "Please provide either a valid public key our account name for active permissions",
            isError: true
          }
          return false;
        }
      }
      
      if(!this.isEmpty(this.account.owner)) {
        if( !(is_valid_public_key(this.account.owner) || is_valid_account_name(this.account.owner))) {
          this.msg = {
            type: "error",
            message: "Please provide either a valid public key our account name for owner permissions",
            isError: true
          }
          return false;
        }
      }
      if(this.isEmpty(this.account.active) && this.isEmpty(this.account.owner) && this.isEmpty(this.account.voting)) {
        this.msg = {
          type: "error",
          message: "Please enter something",
          isError: true
        }
        return false;
      }
      return true;
    },
    isEmpty : function(str) {
      return str.trim() == "";
    },
    isKey: function(str) {
      if (str.startsWith('EOS') && str.length === 53) {
        return true
      }
      return false
    },
    search: function() {
      const self = this
      self.eosAccount = null      
      self.eos.getAccount(self.q)
      .then(res => {
        self.eosAccount = res
      })
      .catch(err => {
        self.eosError = err
      })
    },
    useKey: function(key, index) {
      Vue.set(this.eosUpdatedPerms[index], "key", key)
    },       
    reset: function() {
      this.msg = null
      this.tx = null      
    },
    suggestNetwork: function () {
      this.reset()
      if (this.scatter) {
        var self = this
        this.scatter.suggestNetwork(this.network).then(function (res) {
          console.log(res)
        }).catch(function (err) {
          self.msg = err
        })
      }
    },
    connectScatter: function () {
      this.reset()
      this.eosUpdatedPerms = [] 
      var self = this
      var options = {
        accounts: [this.network]
      }
      var scatter;
      if(window.ScatterJS) {
        window.ScatterJS.plugins( new ScatterEOS() );
        scatter = window.ScatterJS.scatter
      } else {
        scatter = this.scatter
      }
      scatter.connect('eos-account-creator.com').then(connected => {
        if(!connected) {
          this.msg = {
            type: 'Sorry',
            message: 'We are unable to locate the scatter plugin!',
            isError: true
          }
          return;
        }
        window.ScatterJS = null;
        this.scatter = scatter
        this.scatter.getIdentity(options)
          .then(function (identity) {
            identity.accounts.forEach((p) => {
              self.q = p.name
              if (self.account.name  === '') {
                self.account.name = p.name
              }
              self.eup = {
                key: null,
                authority: p.authority,
                account: p.name,
              }
            })
            self.search()    
            self.identity = identity
          })
          .catch(function (err) {
            self.msg = err
          })   
      })
      
      
      
      
    },
    forgetIdentity: function() {
      this.reset()
      this.identity = null
      if (this.scatter) {
        const self = this
        this.scatter.forgetIdentity().then(function(r){
          console.log()
        }).catch(function(err) {
          self.msg = err
        })
      }
    },
    prepareOpts: function(account, owner, accountOrKey, perm) {
      const opts = {
        account: account,
        permission: perm,
        parent: owner,
        auth:{
          threshold: 1,
          accounts: [],
          keys: []
        }
      }
      if (this.isKey(accountOrKey)) {
        opts.auth.keys.push({
          key: accountOrKey,
          weight: 1
        })
      } else if(accountOrKey.length === 12) {
        opts.auth.accounts.push({
          permission:{
            actor: accountOrKey,
            permission: 'active'
          },
          weight: 1
        })
      } else {
        return null
      }
      return opts
    },
    updateAccountKey: function () {
      this.reset()

      if(!this.checkForm()) {
        return;
      };
      const self = this
      if (self.scatter) {
        const eos = self.scatter.eos(self.network, Eos, {
          chainId: self.network.chainId
        })        
        const account = self.account.name
        // console.log("self.account.voting: ", self.account.voting)
        const opts = [
          self.prepareOpts(account, '', self.account.owner, 'owner'),
          self.prepareOpts(account, 'owner', self.account.active, 'active'),
          self.prepareOpts(account, 'active', self.account.voting, 'voting')
        ]
        eos.transaction(function(tx){
          opts.forEach(function(opt){
            if(opt !== null){
              tx.updateauth(opt, {authorization: `${self.eup.account}@${self.eup.authority}`})
              // console.log("opt: ", JSON.stringify(opt))
              
            }
          })
        })
        .then(r => {
          return eos.transaction(function(tx){
            opts.forEach(function(opt){
              if(opt !== null){
                if(opt.permission == 'voting') {
                  tx.linkauth({
                    account: opt.account,
                    code: 'eosio',
                    'type': 'voteproducer',
                    requirement: 'voting'
                  }, {
                    authorization: `${self.eup.account}@${self.eup.authority}`
                  })
                }
              }
            })
          })
        })
        .then(r => {
          self.tx = r
          self.account = {
            name: '',
            active: '',
            owner: ''
          }
          self.eosAccount = null
          self.userConfirmation = false
        }).catch(err => {
          self.msg = {
            type: err.name ? err.name : err.type,
            message: err.what? err.what: err.message,
            isError: true
          }
        })
      }
    }
  }
})
