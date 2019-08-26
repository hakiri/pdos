pragma solidity >=0.5.0 <0.6.0;

/*
    This is an operation's contract.
    It will register to root contract and keep count of users that joined.
*/
contract O {

    /*
        operation's parameters
    */
    uint      public  threshold;  // requiered number of users
    string    public  target;     // target host specification (union of fqdn and ip ranges)
    string    public  service;    // targeted service
    uint      public  epochstart; // start time of operation
    uint      public  epochstop;  // end time of operation
    uint      public  staking;    // staking in wei
    string    public  info;       // optional information field

    /*
        contract own variables
    */
    mapping (address => bool) private users;    // users who joined the operation
    mapping (address => uint) private stakings; // users funds
    uint      public  nbusers = 0;              // size of mapping
    bool      public  decided = false;          // whether operation is decided

    /*
        reading primitives
    */
    function getThreshold() public view returns (uint)        { return threshold; }
    function getTarget() public view returns (string memory)  { return target;    }
    function getService() public view returns (string memory) { return service;   }
    function getEpochstart() public view returns (uint)       { return epochstart;     }
    function getEpochstop() public view returns (uint)        { return epochstop;     }
    function getStaking() public view returns (uint)          { return staking;   }
    function getInfo() public view returns (string memory)    { return info;      }
    function getNbusers() public view returns (uint)          { return nbusers;   }
    function getDecided() public view returns (bool)          { return decided;   }

   /*
        event when user joins and when operation is decided
    */
    event NewUserEvent(address _user); 
    event OperationDecidedEvent();

    /*
        constructor, copies operation parameters to storage,
        then registers to root contract
    */
    constructor (uint _threshold, 
                string memory _target,
                string memory _service,
                uint _epochstart,
                uint _epochstop,
                uint _staking,
                string memory _info
                ) public payable {
        require(_threshold > 0);
        threshold = _threshold;
        target = _target; 
        service = _service;
        epochstart = _epochstart;
        epochstop = _epochstop;
        staking = _staking;
        info = _info;
    }

    /*
        external function called by user to get operation data
    */
    function getOperationData() public view returns (uint,
                                                string memory,
                                                string memory,
                                                uint,
                                                uint,
                                                uint,
                                                string memory) {
        return (threshold, target, service, epochstart, epochstop, staking, info);
    }

    /*
        external function called by user to get operation variables
    */
    function getOperationVariables() public view returns (uint, bool) {
        return (nbusers, decided);
    }

    /*
        external function called by user to join operation
    */
    function userJoin () public payable {
        require (msg.value >= staking);
        require (users[msg.sender] == false);

        /*
            operation is not decided yet
            staking is enough
            user is not yet registered
        */
        stakings[msg.sender] = msg.value;
        users[msg.sender] = true;
        nbusers ++;
        emit NewUserEvent(msg.sender);            

        if (nbusers >= threshold) {
            decided = true;
            emit OperationDecidedEvent();
        }
    }

    /*
        tests if a given user has joined the operation
    */
    function hasUserJoined (address _user) public view returns (bool) {
        return (users[_user] == true);
    }

   /*
        external function called by user to withdraw staking fees
    */
    function withdrawStaking () public payable {
        require (decided == true);
        require (users[msg.sender] == true);

        /*
            operation has been decided
            user is registered
            => give back staking fee
        */
        uint amount = stakings[msg.sender];
        require(amount > 0);
        stakings[msg.sender] = 0;      
        require(msg.sender.send(amount));
    }

}
