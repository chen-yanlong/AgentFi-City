// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract TaskMarket {
    enum TaskStatus {
        Created,
        InProgress,
        Completed,
        Settled
    }

    struct Task {
        uint256 id;
        address creator;
        string description;
        uint256 reward;
        TaskStatus status;
        address[] participants;
    }

    uint256 public nextTaskId;
    mapping(uint256 => Task) public tasks;
    mapping(uint256 => mapping(address => bool)) public hasJoined;

    event TaskCreated(
        uint256 indexed taskId,
        address indexed creator,
        string description,
        uint256 reward
    );
    event TaskJoined(uint256 indexed taskId, address indexed agent);
    event TaskCompleted(uint256 indexed taskId);
    event RewardDistributed(uint256 indexed taskId, uint256 rewardPerAgent);

    function createTask(string memory description)
        external
        payable
        returns (uint256 taskId)
    {
        require(msg.value > 0, "Reward required");

        taskId = nextTaskId++;

        Task storage task = tasks[taskId];
        task.id = taskId;
        task.creator = msg.sender;
        task.description = description;
        task.reward = msg.value;
        task.status = TaskStatus.Created;

        emit TaskCreated(taskId, msg.sender, description, msg.value);
    }

    function joinTask(uint256 taskId) external {
        Task storage task = tasks[taskId];

        require(
            task.status == TaskStatus.Created ||
                task.status == TaskStatus.InProgress,
            "Task not joinable"
        );
        require(!hasJoined[taskId][msg.sender], "Already joined");

        hasJoined[taskId][msg.sender] = true;
        task.participants.push(msg.sender);
        task.status = TaskStatus.InProgress;

        emit TaskJoined(taskId, msg.sender);
    }

    function completeTask(uint256 taskId) external {
        Task storage task = tasks[taskId];

        require(msg.sender == task.creator, "Only creator can complete");
        require(task.status == TaskStatus.InProgress, "Task not in progress");
        require(task.participants.length > 0, "No participants");

        task.status = TaskStatus.Completed;

        emit TaskCompleted(taskId);
    }

    function distributeReward(uint256 taskId) external {
        Task storage task = tasks[taskId];

        require(msg.sender == task.creator, "Only creator can settle");
        require(task.status == TaskStatus.Completed, "Task not completed");
        require(task.participants.length > 0, "No participants");

        uint256 rewardPerAgent = task.reward / task.participants.length;
        task.status = TaskStatus.Settled;

        for (uint256 i = 0; i < task.participants.length; i++) {
            (bool sent, ) = payable(task.participants[i]).call{
                value: rewardPerAgent
            }("");
            require(sent, "Reward transfer failed");
        }

        emit RewardDistributed(taskId, rewardPerAgent);
    }

    function getParticipants(uint256 taskId)
        external
        view
        returns (address[] memory)
    {
        return tasks[taskId].participants;
    }
}
