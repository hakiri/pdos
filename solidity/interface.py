import os
import json

from utils.log import log
import web3

# Uses code from: https://github.com/pryce-turner/web3_python_tutorials
class ContractInterface(object):
    """A convenience interface for interacting with ethereum smart contracts
    This interface will handle a main contract and it's dependencies. All it
    requires is a path to the directory where your solidity files are stored.
    It will then compile, deploy, fetch a contract instance, and provide
    methods for transacting and calling with gas checks and event output.
    """

    default_vars_path = os.path.join(os.getcwd(), 'deployment_variables.json')
    all_compiled_contracts = dict()

    def __init__(
        self,
        web3,
        contract_to_deploy,
        contract_directory,
        max_deploy_gas = 5000000,
        max_tx_gas     = 5000000,
        deployment_vars_path = default_vars_path,
        gasprice = 21000000000,
        account=None,
        privatekey=None
        ):
        """Accepts contract, directory, and an RPC connection and sets defaults
        Parameters:
            web3 (Web3 object): the RPC node you'll make calls to (e.g. geth, ganache-cli)
            contract_to_deploy (str): name of the contract you want to interface with
            contract_directory (path): location of Solidity source files
            max_deploy_gas (int): max gas to use on deploy, see 'deploy_contract'
            max_tx_gas (int): max gas to use for transactions, see 'send'
            deployment_vars_path (path): default path for storing deployment variables
        Also sets web3.eth.defaultAccount as the coinbase account (e.g. the
        first key pair/account in ganache) for all send parameters
        """

        self.web3 = web3
        self.contract_to_deploy = contract_to_deploy
        self.contract_directory = contract_directory
        self.max_deploy_gas = max_deploy_gas
        self.max_tx_gas = max_tx_gas
        self.gasprice = gasprice
        self.deployment_vars_path = deployment_vars_path

        self.account = account
        self.privatekey = privatekey

    def add_compiled_source_file(self, contract, filepath_abi, filepath_bytecode):
        """Adds precompiled contracts to all_compiled_contracts
        """     
        deployment_compiled = dict()
        with open(filepath_abi, 'r') as fd:
            deployment_compiled['abi'] = json.load(fd)[0]

        with open(filepath_bytecode, 'r') as fd:
            deployment_compiled['bin'] = fd.read()
  
        self.all_compiled_contracts[contract] = deployment_compiled

    def deploy_contract(self, deployment_params=None):
        """Deploys contract specified by 'contract_to_deploy'
        Estimates deployment gas and compares that to max_deploy_gas before
        deploying. Also writes out variables required to create a contract
        instance to 'deployment_vars' to easily recreate it after exiting
        program.
        Parameters:
            deployment_params (dict): optional dictionary for overloading the
            default deployment transaction parameters. See web3.py's
            eth.sendTransaction for more info.
        """

        try:
            self.all_compiled_contracts is not None
        except AttributeError:
            log("Source files not compiled", "warning")
            raise

        for compiled_contract_key in self.all_compiled_contracts.keys():
            if self.contract_to_deploy in compiled_contract_key:
                deployment_compiled = self.all_compiled_contracts[compiled_contract_key]

                deployment = self.web3.eth.contract(
                    abi=deployment_compiled['abi'],
                    bytecode=deployment_compiled['bin']
                    )

                deployment_estimate = deployment.constructor().estimateGas(transaction=deployment_params)
                if deployment_estimate < self.max_deploy_gas:
                    if self.privatekey == None:
                        tx_hash = deployment.constructor().transact(transaction=deployment_params)
                    else:
                        #sign transaction here
                        #tx_object = {
                        #    "from": account,
                        #    "data": deployment_compiled['bin'],
                        #    "gas": deployment_estimate,
                        #    }
                        transaction = deployment.constructor().buildTransaction(transaction=deployment_params)
                        # Get correct transaction nonce for sender from the node
                        transaction['nonce'] = self.web3.eth.getTransactionCount(self.account)
                        transaction['gasPrice'] = self.gasprice
                        transaction['gas'] = deployment_estimate
                        log ("Deployment estimate (gas): {}".format(deployment_estimate), "warning")
                        log ("Deployment gas price: {}".format(self.gasprice), "warning")

                        signed = self.web3.eth.account.signTransaction(transaction, self.privatekey)
                        tx_hash = self.web3.eth.sendRawTransaction(signed.rawTransaction)
                else:
                    raise("Deployment estimate if higher than max_deploy_gas")

                log("Deploying contract...", "warning")
                tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
                contract_address = tx_receipt['contractAddress']

                log(
                    "Deployed {0} to: {1} using {2} gas.".format(
                        self.contract_to_deploy,
                        contract_address,
                        tx_receipt['cumulativeGasUsed']
                    ),
                    "success",
                )

                vars = {
                    'contract_address' : contract_address,
                    'contract_abi' : deployment_compiled['abi']
                }

                with open (self.deployment_vars_path, 'w') as write_file:
                    json.dump(vars, write_file, indent=4)

                #print(f"Address and interface ABI for {self.contract_to_deploy} written to {self.deployment_vars_path}")
        return contract_address

    def get_instance(self):
        """Returns a contract instance object from variables in 'deployment_vars'
        Checks there is in fact an address saved. Also does a (crude) check
        that the deployment at that address is not empty. Reads variables
        created in 'deploy_contract' and creates a contract instance
        for use with all the 'Contract' methods specified in web3.py
        Returns:
            self.contract_instance(class ContractInterface): see above
        """

        with open (self.deployment_vars_path, 'r') as read_file:
            vars = json.load(read_file)

        try:
            self.contract_address = vars['contract_address']
        except ValueError(
            f"No address found in {self.deployment_vars_path}, please call 'deploy_contract' and try again."
            ):
            raise

        contract_bytecode_length = len(self.web3.eth.getCode(self.contract_address).hex())

        try:
            assert (contract_bytecode_length > 4), f"Contract not deployed at {self.contract_address}."
        except AssertionError as e:
            print(e)
            raise e
        #else:
            #print(f"Contract deployed at {self.contract_address}. This function returns an instance object.")

        self.contract_instance = self.web3.eth.contract(
            abi = vars['contract_abi'],
            address = vars['contract_address']
        )

        return self.contract_instance

    def get_instance_from_address(self, filepath_abi, contract_address):
        """Returns a contract instance object from address
        Does a (crude) check that the deployment at that address is
        not empty. Creates a contract instance for use with all
        the 'Contract' methods specified in web3.py
        Returns:
            self.contract_instance(class ContractInterface): see above
        """

        self.contract_address = contract_address

        with open(filepath_abi, 'r') as fd:
            contract_abi = json.load(fd)

        try:
            contract_bytecode_length = len(self.web3.eth.getCode(self.contract_address).hex())
        except web3.exceptions.InvalidAddress as e:
            log("Contract address if invalid: {}".format(e), "error", errcode=-127)

        try:
            assert (contract_bytecode_length > 4), f"Contract not deployed at {self.contract_address}."
        except AssertionError as e:
            print(e)
            raise
        #else:
            #print(f"Contract deployed at {self.contract_address}. This function returns an instance object.")

        self.contract_instance = self.web3.eth.contract(
            abi = contract_abi[0],
            address = self.contract_address
        )

        return self.contract_instance
