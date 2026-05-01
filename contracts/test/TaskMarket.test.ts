import { expect } from "chai";
import { ethers } from "hardhat";
import { TaskMarket } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("TaskMarket", () => {
  let taskMarket: TaskMarket;
  let creator: HardhatEthersSigner;
  let researcher: HardhatEthersSigner;
  let executor: HardhatEthersSigner;
  let outsider: HardhatEthersSigner;

  const REWARD = ethers.parseEther("0.01");
  const DESCRIPTION = "Analyze ETH market trend";

  beforeEach(async () => {
    [creator, researcher, executor, outsider] = await ethers.getSigners();
    const TaskMarketFactory = await ethers.getContractFactory("TaskMarket");
    taskMarket = await TaskMarketFactory.deploy();
    await taskMarket.waitForDeployment();
  });

  describe("createTask", () => {
    it("creates a task with native token reward", async () => {
      const tx = await taskMarket.createTask(DESCRIPTION, { value: REWARD });

      await expect(tx)
        .to.emit(taskMarket, "TaskCreated")
        .withArgs(0, creator.address, DESCRIPTION, REWARD);

      const task = await taskMarket.tasks(0);
      expect(task.id).to.equal(0);
      expect(task.creator).to.equal(creator.address);
      expect(task.description).to.equal(DESCRIPTION);
      expect(task.reward).to.equal(REWARD);
      expect(task.status).to.equal(0); // Created
    });

    it("reverts when reward is zero", async () => {
      await expect(
        taskMarket.createTask(DESCRIPTION, { value: 0 })
      ).to.be.revertedWith("Reward required");
    });

    it("increments taskId on each creation", async () => {
      await taskMarket.createTask("task A", { value: REWARD });
      await taskMarket.createTask("task B", { value: REWARD });

      expect(await taskMarket.nextTaskId()).to.equal(2);
    });
  });

  describe("joinTask", () => {
    beforeEach(async () => {
      await taskMarket.createTask(DESCRIPTION, { value: REWARD });
    });

    it("allows an agent to join", async () => {
      await expect(taskMarket.connect(researcher).joinTask(0))
        .to.emit(taskMarket, "TaskJoined")
        .withArgs(0, researcher.address);

      expect(await taskMarket.hasJoined(0, researcher.address)).to.be.true;
      const participants = await taskMarket.getParticipants(0);
      expect(participants).to.deep.equal([researcher.address]);
    });

    it("transitions status to InProgress on first join", async () => {
      await taskMarket.connect(researcher).joinTask(0);
      const task = await taskMarket.tasks(0);
      expect(task.status).to.equal(1); // InProgress
    });

    it("allows multiple agents to join", async () => {
      await taskMarket.connect(researcher).joinTask(0);
      await taskMarket.connect(executor).joinTask(0);

      const participants = await taskMarket.getParticipants(0);
      expect(participants).to.deep.equal([researcher.address, executor.address]);
    });

    it("reverts on double join", async () => {
      await taskMarket.connect(researcher).joinTask(0);
      await expect(
        taskMarket.connect(researcher).joinTask(0)
      ).to.be.revertedWith("Already joined");
    });
  });

  describe("completeTask", () => {
    beforeEach(async () => {
      await taskMarket.createTask(DESCRIPTION, { value: REWARD });
      await taskMarket.connect(researcher).joinTask(0);
      await taskMarket.connect(executor).joinTask(0);
    });

    it("only creator can complete", async () => {
      await expect(
        taskMarket.connect(outsider).completeTask(0)
      ).to.be.revertedWith("Only creator can complete");
    });

    it("reverts if task is not in progress", async () => {
      await taskMarket.completeTask(0);
      await expect(taskMarket.completeTask(0)).to.be.revertedWith(
        "Task not in progress"
      );
    });

    it("emits TaskCompleted and updates status", async () => {
      await expect(taskMarket.completeTask(0))
        .to.emit(taskMarket, "TaskCompleted")
        .withArgs(0);

      const task = await taskMarket.tasks(0);
      expect(task.status).to.equal(2); // Completed
    });
  });

  describe("distributeReward", () => {
    beforeEach(async () => {
      await taskMarket.createTask(DESCRIPTION, { value: REWARD });
      await taskMarket.connect(researcher).joinTask(0);
      await taskMarket.connect(executor).joinTask(0);
      await taskMarket.completeTask(0);
    });

    it("only creator can distribute", async () => {
      await expect(
        taskMarket.connect(outsider).distributeReward(0)
      ).to.be.revertedWith("Only creator can settle");
    });

    it("reverts if task not completed", async () => {
      await taskMarket.createTask("task B", { value: REWARD });
      await taskMarket.connect(researcher).joinTask(1);
      await expect(taskMarket.distributeReward(1)).to.be.revertedWith(
        "Task not completed"
      );
    });

    it("splits reward equally among participants", async () => {
      const expectedShare = REWARD / 2n;

      await expect(taskMarket.distributeReward(0)).to.changeEtherBalances(
        [researcher, executor],
        [expectedShare, expectedShare]
      );
    });

    it("emits RewardDistributed with per-agent share", async () => {
      const expectedShare = REWARD / 2n;
      await expect(taskMarket.distributeReward(0))
        .to.emit(taskMarket, "RewardDistributed")
        .withArgs(0, expectedShare);
    });

    it("transitions status to Settled", async () => {
      await taskMarket.distributeReward(0);
      const task = await taskMarket.tasks(0);
      expect(task.status).to.equal(3); // Settled
    });
  });

  describe("full lifecycle", () => {
    it("runs the complete task flow end-to-end", async () => {
      // Create
      await taskMarket.createTask(DESCRIPTION, { value: REWARD });

      // Join
      await taskMarket.connect(researcher).joinTask(0);
      await taskMarket.connect(executor).joinTask(0);

      // Complete
      await taskMarket.completeTask(0);

      // Distribute
      const expectedShare = REWARD / 2n;
      await expect(taskMarket.distributeReward(0)).to.changeEtherBalances(
        [researcher, executor],
        [expectedShare, expectedShare]
      );

      const task = await taskMarket.tasks(0);
      expect(task.status).to.equal(3); // Settled
    });
  });
});
