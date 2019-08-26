import os
import binascii
from attrdict import AttrDict

from solidity.interface import ContractInterface
from threading import Thread, Event
from web3 import Web3, HTTPProvider, WebsocketProvider

from utils.log import log

DEFAULT_HTTP_INSTANCE = 'http://127.0.0.1:8545'

# contract_dir = os.path.abspath('./test_contracts/')
contract_dir = os.path.join(os.path.dirname(__file__), '../solidity/contracts/')

COMPILEDCONTRACTS = os.path.join(os.path.dirname(__file__), '../pdosd/contracts/')

RCONTRACTABI = os.path.join(COMPILEDCONTRACTS, 'R.abi')
RCONTRACTBYTECODE = os.path.join(COMPILEDCONTRACTS, 'R.bc')
OCONTRACTABI = os.path.join(COMPILEDCONTRACTS, 'O.abi')
OCONTRACTBYTECODE = os.path.join(COMPILEDCONTRACTS, 'O.bc')

class EventThread(Thread):
    """Thread class with a stop() method to allow restarting when we join a new
    operation.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class ORContractsInterface(object):
    """Class used to interface with R and O contracts on the ETH blockchain
    """

    def __init__(
            self,
            HARCODED_R_ADDRESS,
            RPC_INSTANCE=DEFAULT_HTTP_INSTANCE,
            PoA=False,
            account=None,
            privatekey=None,
            max_deploy_gas = 5000000,
            max_tx_gas     = 5000000,
            gasprice = 21000000000,
    ):
        """ PoA has to be set to True on a PoA network. Otherwise False means:
        PoW network (default) HARCODED_R_ADDRESS contains the address of the
        reference R contract already deployed.  if set to None, deploy a new R
        contract (useful for dev or debug)
        """

        self.privatekey = privatekey
        self.max_tx_gas = max_tx_gas
        self.max_deploy_gas = max_deploy_gas
        self.gasprice = gasprice

        self.HARCODED_R_ADDRESS = HARCODED_R_ADDRESS
        self.eventhandler = None

        # keys are contract addresses, and item are list of w3 event filters.
        self.event_filters = dict()

        try:
            # Note that you should create only one RPCProvider per process, as
            # it recycles underlying TCP/IP network connections between your
            # process and Ethereum node
            if RPC_INSTANCE.lower().startswith('http'):
                self.w3 = Web3(HTTPProvider(RPC_INSTANCE,
                request_kwargs={'timeout': 60}))
            elif RPC_INSTANCE.lower().startswith('ws'):
                self.w3 = Web3(WebsocketProvider(RPC_INSTANCE,
                websocket_kwargs={'timeout': 60}))
            else:
                log("Unknown RPC endpoint: {}.".format(RPC_INSTANCE), "error")
                raise Exception("Unknown RPC endpoint.")
            
            if not self.w3.isConnected():
                raise Exception("Node not connected.")
            else:
                log("Web3 Connected through RPC", "success")
        except Exception as e:
            log(
                "Could not reach RPC at %s" % RPC_INSTANCE,
                "error", errcode=-1,
            )
            raise e

        log("Web3 api version: ______ %s" % self.w3.version.api, "success")
        log("Web3 node version: _____ %s" % self.w3.version.node, "success")
        log("Web3 network version: __ %s" % self.w3.version.network, "success")

        # POA chain? Otherwise PoW.
        if PoA:
            from web3.middleware import geth_poa_middleware
            self.w3.middleware_stack.inject(geth_poa_middleware, layer=0)

        if account == None or account == "coinbase":
            try:
                self.account = self.w3.eth.coinbase
            except ValueError as e:
                log("Mining client does not support wallet management, you need to provide an ethereum key pair", "error", errcode=-128)
        else:
            self.account = account

        # sanity check on account key
        if not Web3.isChecksumAddress(self.account):
            log ("Provided address {} if not a valid EIP55 checksummed ethereum address".format(self.account), "error", errcode=-126)

        if self.privatekey != None:
            transaction = dict()
            transaction['nonce'] = 0
            transaction['gasPrice'] = 0
            transaction['gas'] = 0
            try:
                signed = self.w3.eth.account.signTransaction(transaction, self.privatekey)
            except ValueError:
                log ("Provided private key {} if invalid".format(self.privatekey), "error", errcode=-125)

        self.R_interface = ContractInterface(self.w3,
            'R',
            contract_dir,
            account=self.account,
            privatekey=self.privatekey,
            max_deploy_gas=self.max_deploy_gas,
            max_tx_gas=self.max_tx_gas,
            gasprice=self.gasprice)
        self.R_interface.add_compiled_source_file(
            'R', RCONTRACTABI, RCONTRACTBYTECODE,
        )

        if self.HARCODED_R_ADDRESS is None:
            # debug / dev_test mode: deploy it
            self.HARCODED_R_ADDRESS = self.R_interface.deploy_contract({"from": self.account})

        self.R_instance = self.R_interface.get_instance_from_address(
            RCONTRACTABI, self.HARCODED_R_ADDRESS,
        )

        self.O_interface = ContractInterface(self.w3,
            'O',
            contract_dir,
            account=self.account,
            privatekey=self.privatekey,
            max_deploy_gas=self.max_deploy_gas,
            max_tx_gas=self.max_tx_gas,
            gasprice=self.gasprice)
        self.O_interface.add_compiled_source_file(
            'O', OCONTRACTABI, OCONTRACTBYTECODE,
        )

        # filter setup (some clients might not support, so we try/catch)
        try:
            event_filters = dict(self.event_filters)
            if self.HARCODED_R_ADDRESS not in event_filters:
                event_filters[self.HARCODED_R_ADDRESS] = []
            event_filters[self.HARCODED_R_ADDRESS].append(
                self.R_instance.events.NewOperationEvent.createFilter(
                    fromBlock=0,
                ),
            )
            event_filters[self.HARCODED_R_ADDRESS].append(
                self.R_instance.events.DestroyedContractEvent.createFilter(
                    fromBlock=0,
                )
            )
            self.event_filters = event_filters
        except ValueError as e:
            log("Node does not support filtering", "error")
            raise e
        except:
            log("Node timed out while setting up filters, incomplete init", "error")

    def _mktransact(self, obj, value):
        """ Make a normal transaction through node if wallet is managed by the node.
        Otherwise, create & sign a raw transaction then broadcasts it to the node.

        This is a blocking call, that waits for transaction to be performed.
        """
        tx_estimate = obj.estimateGas()
        if tx_estimate < self.max_tx_gas:
            if self.privatekey == None:
                tx_hash = obj.transact({'from': self.account, 'value': value})
            else:
                transaction = obj.buildTransaction()
                transaction['nonce'] = self.w3.eth.getTransactionCount(self.account)
                transaction['gasPrice'] = self.gasprice
                transaction['gas'] = tx_estimate
                transaction['value'] = value
                log ("Tx estimate (gas): {}".format(tx_estimate), "warning")
                log ("Tx gas price: {}".format(self.gasprice), "warning")
                log ("Tx value: {}".format(value), "warning")                

                signed = self.w3.eth.account.signTransaction(transaction, self.privatekey)
                tx_hash = self.w3.eth.sendRawTransaction(signed.rawTransaction)

            receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
            log("Sending transaction...", "warning")
            if receipt['status'] == 1:
                log("Transaction {} succeeded.".format(binascii.b2a_hex(tx_hash)), "success")
                return True
            else:
                log("Transaction {} FAILED.".format(binascii.b2a_hex(tx_hash)), "error")
                raise
        else:
            raise

    def enum_operations(self):
        """ Call the getOperations from R instance to retreive a list of
        operations contracts addresses.
        """
        return self.R_instance.functions.getOperations().call()

    def get_operation_data(self, operation):
        """ Get operations data through a call to O contract's getOperationData.
        """
        O_instance = self.O_interface.get_instance_from_address(
            OCONTRACTABI, operation,
        )
        (threshold,
         target,
         service,
         epochstart,
         epochstop,
         staking,
         info) = \
            O_instance.functions.getOperationData().call()
        (nbusers, decided) = \
            O_instance.functions.getOperationVariables().call()
        return (
            threshold,
            target,
            service,
            epochstart,
            epochstop,
            staking,
            info,
            nbusers,
            decided,
        )

    def propose_operation(
            self,
            threshold,
            target,
            service,
            epoch_start,
            epoch_stop,
            staking,
            info,
    ):
        """ Calls the newOperation function of the R contract instance with
        given parameters.
        """
        return self._mktransact(self.R_instance.functions.newOperation(
            threshold,
            target,
            service,
            epoch_start,
            epoch_stop,
            staking,
            info,
        ), 0)

    def has_user_joined(self, operation):
        """returns true if and only if user has joined the operation
        """
        O_instance = self.O_interface.get_instance_from_address(
            OCONTRACTABI, operation,
        )
        return O_instance.functions.hasUserJoined(self.account).call()

    def get_user_operations(self):
        """returns list of operations which were joined by the user
        """
        result = []
        for operation in self.enum_operations():
            if self.has_user_joined(operation):
                result.append(operation)

        return result

    def get_past_event_entries(self):
        """ Retrives all past events using the eventFitler function
        Makes a list of all events from R contract and O contracts.
        """

        eventlist = []
        for operation in self.get_user_operations():
            ( _, _, _, _, _, _, _, _, decided,
            ) = self.get_operation_data(operation)

            if decided:
                event = AttrDict()
                event.event = 'OperationDecidedEvent'
                event.address = operation

                eventlist.append(event)

        return eventlist


    def join_operation(self, operation, staking=0):
        """ Retrieves operation (O) contract instance and calls its userJoin
        function.  adds a filter on the two operation contracts events and
        restarts event handler.
        """

        O_instance = self.O_interface.get_instance_from_address(
            OCONTRACTABI, operation,
        )

        # create watch for this operation's events
        event_filters = dict(self.event_filters)

        if operation not in event_filters:
            event_filters[operation] = []

        event_filters[operation].append(
            O_instance.events.NewUserEvent.createFilter(
                fromBlock=0,
            ),
        )
        event_filters[operation].append(
            O_instance.events.OperationDecidedEvent.createFilter(
                fromBlock=0,
            ),
        )
        self.event_filters = event_filters

        # join it
        return self._mktransact(O_instance.functions.userJoin(), staking)

    def withdraw_staking(self, operation):
        """ Simple call to operation contract withdrawStaking()
        """
        O_instance = self.O_interface.get_instance_from_address(
            OCONTRACTABI, operation,
        )
        return self._mktransact(O_instance.functions.withdrawStaking(), 0)
