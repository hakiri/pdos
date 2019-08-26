#!/usr/bin/env python3

# Compiles contracts and saves compiled contracts on pdosd contracts/ directory
# Uses code from: https://github.com/pryce-turner/web3_python_tutorials

import json
import sys
import os
from solcx import set_solc_version_pragma, compile_source, compile_files

set_solc_version_pragma('>=0.5.0 <0.6.0')

CONTRACTOUTPUTDIR = "../pdosd/contracts/"

contract_dir = os.path.abspath('./contracts/')

class ContractCompilationInterface(object):
    default_vars_path = os.path.join(os.getcwd(), 'deployment_variables.json')

    def __init__(
        self,
        contract_to_deploy,
        contract_directory,
        deployment_vars_path = default_vars_path
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

        self.contract_to_deploy = contract_to_deploy
        self.contract_directory = contract_directory
        self.deployment_vars_path = deployment_vars_path

    def compile_source_files(self):
        """Compiles 'contract_to_deploy' from specified contract.
        Loops through contracts in 'contract_directory' and creates a list of
        absolute paths to be passed to the py-solc-x's 'compile_files' method.
        Returns:
            self.all_compiled_contracts (dict): all the compiler outputs (abi, bin, ast...)
            for every contract in contract_directory
        """

        deployment_list = []

        for contract in os.listdir(self.contract_directory):
            deployment_list.append(os.path.join(self.contract_directory, contract))

        self.all_compiled_contracts = compile_files(deployment_list)

        print("Compiled contract keys:\n{}".format(
            '\n'.join(self.all_compiled_contracts.keys()
            )))

def compile(contract): #TODO: параметры компилятора?
	R_interface = ContractCompilationInterface(contract, contract_dir)

	try:
		R_interface.compile_source_files()
	except Exception as e:
		print ("Could not compile. You may need to install solcx with: sudo ./install_solc.py.")
		print (e)
		sys.exit(-1)

	for compiled_contract_key in R_interface.all_compiled_contracts.keys():
		name = os.path.basename(compiled_contract_key)
		if name != ("%s.sol:%s" % (contract, contract)):
			continue

		if R_interface.contract_to_deploy in compiled_contract_key:
			deployment_compiled = R_interface.all_compiled_contracts[compiled_contract_key]

			abi=deployment_compiled['abi'],
			bytecode=deployment_compiled['bin']

			CONTRACTABI = os.path.join(CONTRACTOUTPUTDIR, "%s.abi" % contract)
			CONTRACTBYTECODE = os.path.join(CONTRACTOUTPUTDIR, "%s.bc" % contract)

			print ("Writing abi to .........: %s" % CONTRACTABI)
			with open(CONTRACTABI, 'w') as fd:
				json.dump(abi, fd)
			print ("Writing bytecode to ....: %s" % CONTRACTBYTECODE)
			with open(CONTRACTBYTECODE, 'w') as fd:
				fd.write(bytecode)


compile('R')
compile('O')
