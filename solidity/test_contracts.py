#!/usr/bin/env python3

from solidity.primitives import ORContractsInterface
from solcx import set_solc_version_pragma
from threading import Thread, Event
import sys
import os
import time


from utils.log import log, mute

def main():

	print ("TESTING CONTRACTS")

	mute()

	OR_iface = ORContractsInterface(None, PoA = True)
	operations = OR_iface.enum_operations()

	###############################################
	print ("* Testing propose_operation & enum_operations")

	assert len(operations) == 0, "operations list should be empty at startup"

	OR_iface.propose_operation(1, "site1.com", "www", 10000, 20000, 0, "hello world")
	operations = OR_iface.enum_operations()
	assert len(operations) == 1, "operations list error"

	first_op_addr = operations[0]

	OR_iface.propose_operation(1, "site2.com", "www", 10000, 20000, 10, "hello universe")
	operations = OR_iface.enum_operations()
	assert len(operations) == 2, "operations list error"

	second_op_addr = operations[1]

	(threshold, target, service,
		epochstart, epochstop, staking,
		info, nbusers, decided) = OR_iface.get_operation_data(operations[0])
	assert decided == False, "new operation is already decided?"

	assert threshold == 1, "error in propose_operation"
	assert target == "site1.com", "error in propose_operation"
	assert service == "www", "error in propose_operation"
	assert epochstart == 10000, "error in propose_operation"
	assert epochstop == 20000, "error in propose_operation"
	assert staking == 0, "error in propose_operation"
	assert info == "hello world", "error in propose_operation"

	###############################################
	print ("* Testing join_operation")

	OR_iface.join_operation(operations[0], 50)
	(threshold, target, service,
		epochstart, epochstop, staking,
		info, nbusers, decided) = OR_iface.get_operation_data(operations[0])

	assert nbusers == 1, "join_operation failed"
	assert decided == True, "join_operation failed"

	###############################################
	print ("* Testing has_user_joined")

	join_op0 = OR_iface.has_user_joined(operations[0])
	join_op1 = OR_iface.has_user_joined(operations[1])

	assert join_op0 and not join_op1, "has_user_joined failed"

	###############################################
	print ("* Testing get_user_operations")
	user_ops = OR_iface.get_user_operations()

	assert user_ops == [operations[0]], "get_user_operations failed"

	###############################################
	print ("* Testing withdraw_staking")

	OR_iface.withdraw_staking(operations[0])
	
	try:
		OR_iface.withdraw_staking(operations[0])
		print ("Should only be allowed to withdraw once")
		raise
	except ValueError:
		pass

	###############################################
	print ("* Testing Events")
	events = OR_iface.get_past_event_entries()

	assert len(events) == 4, "should have 4 events"

	assert events[0].event == 'NewOperationEvent', "incorrect event"
	assert events[0].args["_operation"] == first_op_addr, "wrong operation address"

	assert events[1].event == 'NewOperationEvent', "incorrect event"
	assert events[1].args["_operation"] == second_op_addr, "wrong operation address"

	assert events[2].event == 'NewUserEvent', "incorrect event"
	assert events[2].address == first_op_addr, "wrong operation address"

	assert events[3].event == 'OperationDecidedEvent', "incorrect event"
	assert events[3].address == first_op_addr, "wrong operation address"


	print ("Ok.")
	

if __name__ == '__main__':
	main()
