# pDoS

DDoS for the people

pDoS is a research project exploring the plausibility of organizing
collaborative large-scale DDoS attacks in a censorhip resistant way.

It relies on the ethereum blockchain to achieve resilience. Users can:

* submit a new operation, suggesting a target, a start time along with other
  parameters.
* join and commit to any operation that was previously submitted.
* participate in a DDoS operation that reached the required number of users.

_Warning:_ Do not attempt to launch a DoS using Tor for obvious ethical reasons.

# Architecture

pDoS is a a client operating in the ethereum blockchain through a daemon
communicating with a ethereum client. The wallets paying for the transaction
fees are managed in the user's ethereum client.

```
                 -~* TARGETS *~-                  +--------+
                       ||                         |        |
                       ||                         |      +--------+
  +--------+       +--------+       +--------+    +--------+      |
  |        +------>+        +------>+        +----------->      +--------+
  |        |       |        |       |        |           +--------+      |
  |        +<------+        +<------+        +<-----------------+        |
  +--------+       +--------+       +--------+                  +--------+
     pdos            pdosd        ethereum client           ethereum
   (client)         (daemon)      supporting RPC           blockchain
```

# Operations

pDoS is based on the concept of *operations*. An operation O is a proposal to
collaboratively attempt a DDoS attack on a defined target. An operation is
executed only if the number of participatnts reaches its defined threshold (it
is then *decided*).

```
target: STRING,                   # target to attack
service: STRING,                  # type of service to attack
threshold: INT64,                 # required number of participants
epoch_start: INT64,               # epoch in seconds (start of the attack)
epoch_stop: INT64,                # epoch in seconds (end of the attack)
staking: INT64,                   # amount in `ether` required to bid
info: STRING,                     # free-form information about the operation
```

_Important Note_: For now, only the "www" service is supported, accepting a
target defined as a **unique FQDN** (example: "www.site.com"). `pdos` will attempt to determine which service to attack between HTTP and HTTPS. You can also provide a unique **url** (example: "https://www.site.com/").

Participation to an operation (called *joining* an operation) represents a
commitment by the participant to lend its resources by running *pdosd* at the
planned time of the attack.


# Quickstart

Download or `git clone` this repository.

## Direct use

Install and run any local ethereum node supporting HTTP or Websockets RPC
(<https://geth.ethereum.org/downloads/> for example).

Install `python3` (tested: 3.7) along with `pip3`, then from the `pdos`
directory, install with:
```
pip3 install --user .
```

The `pdos` and `pdosp` executables will generally be installed in
`~/.local/bin`, you can alternatively use *miniconda* or *virtualenv* to
isolate the installation.

You can then:

* run your ethereum client, with RPC interface on `http://127.0.0.1:8545` (by
  default).
* run an instance of `pdosd` with:
  `pdosd --eth_account 0xADDR`, assuming
  `0xADDR` is the address of one of your node's
  accounts.
* if your node does not support private key management or if you don't want it to, run: `pdosd --eth_account 0xADDR --eth_privkey 0xPRIVKEY` or `pdosd --eth_wallet WALLET_FILE`.
* use `pdos`, starting with: `pdos help`.

_Note_: when using ethereum client's wallet API, `pdosd` **can't use any
ethereum funds** that were not previously unlocked inside the ethereum client.
We suggest that you create a dedicated ethereum account for `pdos`, containing
a very small amount of ethers to pay for pDoS transactions gas.

## Docker containers

You may have to enable forwarding when using containers, in order to reach the
real world, especially for the *geth* container if you need to use it (UDP port
forwarding).

```
$ sysctl net.ipv4.conf.all.forwarding=1
$ sudo iptables -P FORWARD ACCEPT
```

The container setup is made of 2 containers (see `docker-compose.yaml`). The
*geth* container launches a ethereum node & client, and the *pdos* container
allows use of *pdosd* and *pdos client*.

_Note_: you can use only 1 of the containers and deal with the other part
yourself, as long as command line parameters are consistent. Beware of exposing
ports to the internet, especially the 8545 geth RPC interface, which would
leave your wallet unprotected.

### Launching a *geth* instance

In project root dir, type `docker-compose build`.

Then type the following commands to start a *geth* instance on *mainnet* and
*pdosd* instance:
```
docker-compose run --use-aliases geth
docker-compose run --use-aliases pdosd
```

_Important Note_: geth data directory is set to: `~/.config/pdos/geth_datadir`.
It will contain the synced blockchain and your private (passphrase encrypted)
data.

For testing on *Ropsten* network, you can use:
```
docker-compose run --use-aliases geth --testnet
docker-compose run --use-aliases pdosd --testnet
```

For development, you can use:
```
docker-compose run --use-aliases geth --mine --dev
docker-compose run --use-aliases pdosd --deploy --networktype PoA
```

In dev mode, geth will open a local private node and pdosd will use a geth
generated ethereum address.

Then *pdos* can be used as follows:
```
docker-compose run pdos help
```
or
```
docker-compose run --entrypoint='' bash
# pdos help
```

### Using *pdos*

Launch *pdos daemon* with: `docker-compose run pdos pdosd --eth_rpc
http://geth_host:8545`

Run *pdos client* commands with: `docker-compose run pdos pdos --help`

# Example setup with *infura*

This section describes how you can use `pdos` with *infura*.

## Register to *infura*

Get an API key from infura:

* go to <infura.io> and registera free account (a valid mail address is required).
* create a new project.
* write down *Project ID* inside the *KEYS* section (32 hex chars). Example: `1878a221d804c95b9f806dbbcd3e6aae`

## Get an ethereum wallet

Create an ethereum wallet. Many ways to do this:

* you can use <https://www.myetherwallet.com/> and select _Create a new wallet_ then _by keystore file_ to download the file.
* run `geth --console`, then `eth.newAccount()` and get the wallet file inside `~/.ethereum/keystore/`.

A wallet file looks like this: `UTC--2011-03-11T09-58-22.352Z--adca81daab252C666f84adb18697baaea0d68f57` and contains your password-encrypted private key. The ETH address liked to this wallet is: `0xadca81daab252C666f84adb18697baaea0d68f57`.

Using any site, purchase ethereums and transfer a small amount to this (example) address (`0xadca81daab252C666f84adb18697baaea0d68f57`). For example: **0.01 ether**.

## Run `pdosd`

On your machine, run the following commands:

```
apt-get install python3 python3-pip
git clone https://github.com/pdos-team/pdos
cd pdos
pip3 install --user .
```

Then open a terminal, run `pdosd`, and wait until GRPC server is up:

```
$ pdosd --eth_rpc wss://mainnet.infura.io/ws/<INFURA_PROJECT_ID> --eth_wallet UTC--2011-03-11T09-58-22.352Z--adca81daab252C666f84adb18697baaea0d68f57
[...]
[+] Starting GRPC server on port 7331.
```

Open another terminal and run:

```
$ pdos help
```

You are now ready to join!


# pDoS daemon (pdosd)

pDoS daemon listens for requests on a RPC interface specified by the `port`
parameter. It connects to specified ethereum node (through http, https,
websocket, or websocket over ssl) to make transactions on the blockchain.

pDos daemon can work with **local** or **hosted** ethereum private keys.

* local keys have to be provided to `pdosd` using command line parameters (see below).
* hosted keys are managed by the ethereum node to which `pdosd` connects.


```
usage: pdosd [-h] [--eth_rpc ETH_RPC] [--eth_account ETH_ACCOUNT]
             [--eth_privkey ETH_PRIVKEY] [--eth_wallet ETH_WALLET]
             [--gasprice GASPRICE] [--port PORT] [--deploy] [--testnet]
             [--reference REFERENCE] [--networktype {PoW,PoA}]

pDoS daemon

optional arguments:
  -h, --help            show this help message and exit
  --eth_rpc ETH_RPC     web3 rpc address to use [default:
                        http://127.0.0.1:8545]
  --eth_account ETH_ACCOUNT
                        ETH (checksummed) address to use (see README)
                        [default: coinbase]
  --eth_privkey ETH_PRIVKEY
                        ETH private key to use to sign transaction inside this
                        script [default: empty]
  --eth_wallet ETH_WALLET
                        path to ETH wallet file (instead of suppling
                        eth_account and eth_privkey) [default: empty]
  --gasprice GASPRICE   ETH private key to use to sign transaction inside this
                        script [default: 21 Gwei]
  --port PORT           port to listen to [default: 7331]
  --deploy              deploy new R contract. Only for dev purposes (see
                        README) [default: False]
  --testnet             use testnet reference contract address instead of
                        mainnet [default: False]
  --reference REFERENCE
                        override reference contract address (dev/testing
                        purposes)
  --networktype {PoW,PoA}
                        Network type (PoW/PoA) [default: PoW]
```

The user can propose and join DDoS operations (see below `pdos` client).
`pdosd` will launch DDoS attack (for now, only SlowLoris has been added to this
project, though a rip of
<https://github.com/gkbrk/slowloris/blob/master/slowloris.py> python code) if
(and only if) the following conditions are *all* fulfilled:

* the user has joined the operation.
* the operation has been decided (= the number of users that committed to the
  operation is above threshold).
* the epoch given by `pdosd` operating system matches the operation's
  requirements (start, stop).

At boot, `pdosd` will connect to node and ask for all past events to be
up-to-date:

```
[+] Web3 Connected through RPC
[+] Web3 api version: ______ 4.X.X
[+] Web3 node version: _____ Geth/v1.X.X-stable-XXXXXXXX/linux-amd64/go1.XX.X
[+] Web3 network version: __ 1337
[+] Reference contract address is 0x3Ba46565824Ab9fBb233E1B5455d612A37E5338e.
[+] NewOperationEvent (operation: 0xBedF71677c8d6a04F73474e1906C61d36017BC9e)
[+] NewOperationEvent (operation: 0xD9050E3CD3aEc21f0684F53edA7C3c21464E7F49)
[+] NewOperationEvent (operation: 0x9c7f897b4A486F9c0acEf8eb3A085bDC209D5a2B)
[+] NewOperationEvent (operation: 0x314994e2Bfb2D8B0e78fe3aB42476c590fbCa710)
[+] NewUserEvent (operation: 0xD9050E3CD3aEc21f0684F53edA7C3c21464E7F49, user: 0xf7825c65E62C939c8Cf928f9Bd2F94Dc864349B8)
[+] OperationDecidedEvent (operation: 0xD9050E3CD3aEc21f0684F53edA7C3c21464E7F49)
[+] Target www.site.com as port 80 open, using HTTP ATK
[+] Execution registered: www/0 www.site.com (100000000000, 100000003600)
[+] Starting GRPC server on port 7331.
```

## Examples

### You want to use a node or a client that manages private keys for you

Example setups:

* **geth** with `--syncmode "full"` or `--syncmode "fast"` arguments

```
$ pdosd
```

### ETH wallet file containing the privatekey

Example setups:

* **parity**
* **geth** with `--syncmode "light"` or if you prefer handling privatekeys yourself)
* any client that does not provide account/wallet API
* **infura.io** or any (non evil) hosted node

User will be prompted for password.

```
$ pdosd --eth_wallet /somedir/UTC--2011-01-01T10-20-40.12345Z--fedc842f2af79b53f93afd28fb098161d0fa7ce2  
Wallet file password: (unseen)
```

### Account and private key as arguments (WARNING: PRIVATE KEY WILL appear during a process listing)

```
$ pdosd --eth_account 0x6FCF1B5dE32d75bbaFF8220cE5A831e12B567740 --eth_privkey 123456789123456789123456789
```

### Use with infura.io nodes

```
pdosd --eth_rpc wss://<NETWORK>.infura.io/ws/<INFURA API KEY> --eth_wallet <WALLET FILE> 
```

_Note_: For all nodes like Infura.io free ethereum node as a service that don't
allow events (<https://github.com/INFURA/infura/issues/73>), you will have to
use a `Websocket` interface.


# pDoS client (`pdos`)

```
$ pdos help
pDoS client

  General options:
    --pdosd_rpc PDOSD_RPC pdosd RPC address [default: 127.0.0.1:7331]

  pdos help [command]
    Display help about a command or this messsage if no command is provided.
    `pdos help operation join`

  pdos operation list
    List upcoming operations.
    `pdos operation list`

  pdos operation propose <target> <threshold> <epoch_start> <duration>
    Propose a new operation.
    `pdos operation propose www.foo.bar 2000 1563888880 3600`

  pdos operation join <address>
    Commmit your participation to an operation.
    `pdos operation join 0x9E845a89AcacE3B2093A0c5c6a3fe75518758e8f`
```

## Proposing an operation

User has to provide a target, a minimum number of users (threshold), the
starting epoch of the operation, and its duration (in seconds). If you provide
an invalid epoch (like 0), the client will give you the current epoch (from the
system).

Required parameters and options are:

```
$ pdos help operation propose
pDoS client

  Propose a new operation.

  Usage:
    pdos operation propose <target> <threshold> <epoch_start> <duration>

  Arguments:
    <target> the domain name of the target.
    <threshold> the number of users required to join.
    <epoch_start> the operation start epoch.
    <duration> the operation duration in seconds.

  Options:
    --service SERVICE the service to attack (supported values: www) [default: www]
    --staking STAKE the required stake for the operation (in wei) [default: 0]
    --info INFO human readable rationale for the operation [default: ]

  Examples:
    pdos operation propose https://www.foo.bar 2000 1563888880 3600
    pdos operation propose fcbk.com 2000 1563888880 3600 --info "save the world"
```

```
$ pdos operation propose www.site.com 1000 0 0
[ERROR] `epoch_start` must be in the future, current epoch: 1011122333
$ pdos operation propose www.site.com 1000 1011130000 3600
[DONE] Operation created.
```

The client waits for the daemon to check that the transaction has been approved
in the blockchain. We can check on `pdosd` logs during the proposition of an
operation:

```
[-] Sending transaction...
[+] Transaction b'89e9df70bb81f6d1d55f9201c4d29fddef050b9f4ce8b83e24108759b8bcb565' succeeded.
[+] NewOperationEvent (operation: 0x1743f31270398B86CC592D73Fffc7eDD9C008c23)
```

Any new operation will be seen through the `NewOperationEvent` notification py
`pdosd`.

## Joining an operation

User has to provide the operation address (checksummed format) of the operation
to be joined:

```
$ pdos operation join 0x1743f31270398B86CC592D73Fffc7eDD9C008c23
[DONE] Operation joined.
```

`pdosd` logs whos the following lines (new user event):

```
[-] Sending transaction...
[+] Transaction b'eaf345908c2ec5888676434ac0bffbb45037d4ffb7172a84da44b9bda11208ca' succeeded.
[+] NewUserEvent (operation: 0x1743f31270398B86CC592D73Fffc7eDD9C008c23, user: 0x6FCF1B5dE32d75bbaFF8220cE5A831e12B567740)
```

If another user joins an operation that is joined by current `pdosd` instance,
then notifications will be showed through `NewUserEvent` logs.

## Listing operations

The following command will allow users to have a look of all pending
operations. They would be marked as 'joined' if user has joined them, and with
'decided' 

```
$ pdos operation list
- 0x1743f31270398B86CC592D73Fffc7eDD9C008c23 -- joined
    target: www.site.com [www]
    users: 1/1000 [False]
    start: 2020-05-07 11:06:20
    duration: 3600s
- 0x9527eC0507d329c4F7c83E5B645b42d0144F0Ccd -- joined & decided
    target: www.nicesite.org [www]
    users: 1250/1000 [False]
    start: 2019-11-16 10:46:40
    duration: 3600s
- 0xAa871562dBA9b45725CC5AbDB2Dc6F5191371aD7
    target: www.othersite.it [www]
    users: 0/1000 [False]
    start: 2020-01-01 11:48:44
    duration: 3600s
- 0x4F7c83E5B6dBA9b45725CC5A371aFffFff98B887 ----------  decided
    target: www.someothersite.it [www]
    users: 0/1000 [False]
    start: 2019-11-20 05:07:00
    duration: 3600s
[DONE]
```

# Development

## Code contribution rules

Below are a few guidelines for submitting contributions.


* Python3.
* You are free to submit on this github project.
* Versioning is MAJOR.MINOR. MAJOR version changes when API/command line is broken, otherwise it's a MINOR change.


## Python env setup

Example development environment based on *miniconda*:
```
conda create -n pdos python=3.7
conda activate pdos
python setup.py develop
```

## Ethereum contracts (`solidity/contracts/`)

Contracts are written in solidity.
* `O.sol` contains the source code for operations contracts.
* `R.sol` contains the source code for the (unique) reference contract.

A reference contract is submitted once and for all. As it keeps a list of
propose operations, this R contract allows users to submit new operations and
reach any existing operation.

Operations are O-type contracts. Through this contract, a user can join a
submitted operation, get details about it, and determine if one should process
with the DoS attack.

Contracts testing can be performed through `solidity/test_contracts.py`.

Reference/root R contracts can be deployed through `pdosd` and its `--deploy`
option.

For example, you can deploy a R contract using `infura` with:
```
pdosd --eth_rpc https://ropsten.infura.io/<INFURA_PROJECT_ID> --eth_account 0X<YOUR ETH ACCOUNT> --eth_privkey 0x<PRIVATE KEY CORRESPONDING TO THAT ACCOUNT> --deploy
```

_Notes_: You will need to provide a checksummed ETH account. This process is
intended to work with any node/client that does not manage wallets through web3
"personal" API endpoint, like parity and more to come.


## Compilation

`./Makefile` can be used as:
```
make
```
to build GRPC Stubs. Or:

```
make contracts
```
to build `O.sol` and `R.sol` contracts into bytecode and abi files (compiled
contracts are in `pdosd/contracts/`).

## Testing

### Contracts

See `make test` in `./solidity/Makefile`, using `./solidity/test_contracts.py`
to perform a series of tests on O and R contrats.

```
$ ./test_contracts.py 
TESTING CONTRACTS
* Testing propose_operation & enum_operations
* Testing join_operation
* Testing has_user_joined
* Testing get_user_operations
* Testing withdraw_staking
* Testing Events
Ok.
```

# Misc

* contact us at <pdos@tutanota.com>.
* donate ETH to support our research (*0xaDcA81DAab252C666f84ADB18697baaea0d68F57*).

# License

The code is licensed under the MIT License.
