pragma solidity >=0.5.0 <0.6.0;

/*
    O contract interface
*/
import { O } from "../contracts/O.sol";


/*
    This a reference or root contract,
    followed by users to keep track of new operations to join
*/
contract R {

    /*
        Keep address of creator of this root contract
    */
    address payable public owner;
    O[] operations;

    /*
        event will contain newly created operation's contract address
    */
    event NewOperationEvent(address _sender, O _operation); 
    event DestroyedContractEvent(); 

    /*
        constructor, simply stores sender's address
    */
    constructor() public {
        owner = msg.sender;
    }

    /*
        this is called by an operation contract when created
    */
    function newOperation(uint _threshold, 
                string memory _target,
                string memory _service,
                uint _epochstart,
                uint _epochstop,
                uint _staking,
                string memory _info
                ) public payable {

        O o = new O(_threshold, _target, _service, _epochstart, _epochstop, _staking, _info);
        operations.push(o);
        emit NewOperationEvent(msg.sender, o);            
    }

    /*
        returns operations list
    */
   function getOperations() public view returns (O[] memory) {
      return operations;
   }

    /*
        only creator can destroy this contract
    */
    modifier ownerRestricted {
        require(owner == msg.sender);
        _;
    }

    /*
        contract self-destruction
    */
    function destroyContract() public ownerRestricted {
        emit DestroyedContractEvent();
        selfdestruct(owner);
    }
}
