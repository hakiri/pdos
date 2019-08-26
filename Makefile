# Builds GRPC Stubs & solidity contracts
#

contracts=pdosd/contracts/O.abi pdosd/contracts/O.bc pdosd/contracts/R.abi pdosd/contracts/R.bc

all: proto/pdosd_pb2.py


proto/pdosd_pb2.py : proto/pdosd.proto
	python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/pdosd.proto

contracts: ${contracts}
${contracts}: solidity/contracts/O.sol solidity/contracts/R.sol
	$(MAKE) -C solidity

contracts_clean:
	rm -rf ${contracts}

clean:
	rm -rf proto/pdosd_pb2.py
	rm -rf proto/pdosd_pb2_grpc.py
	rm -rf deployment_variables.json
