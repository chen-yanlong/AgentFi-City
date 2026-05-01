import { ethers, network, artifacts } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const [deployer] = await ethers.getSigners();
  const balance = await ethers.provider.getBalance(deployer.address);

  console.log(`Network:    ${network.name}`);
  console.log(`Deployer:   ${deployer.address}`);
  console.log(`Balance:    ${ethers.formatEther(balance)} ETH`);
  console.log("");

  const TaskMarket = await ethers.getContractFactory("TaskMarket");
  const taskMarket = await TaskMarket.deploy();
  await taskMarket.waitForDeployment();

  const address = await taskMarket.getAddress();
  const tx = taskMarket.deploymentTransaction();
  const receipt = tx ? await tx.wait() : null;

  console.log(`✓ TaskMarket deployed`);
  console.log(`  address:      ${address}`);
  console.log(`  tx hash:      ${tx?.hash}`);
  console.log(`  block:        ${receipt?.blockNumber}`);

  // Write deployment record
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  const artifact = await artifacts.readArtifact("TaskMarket");

  const record = {
    network: network.name,
    chainId: Number((await ethers.provider.getNetwork()).chainId),
    address,
    deployer: deployer.address,
    txHash: tx?.hash,
    blockNumber: receipt?.blockNumber,
    deployedAt: new Date().toISOString(),
    abi: artifact.abi,
  };

  const outPath = path.join(deploymentsDir, `${network.name}.json`);
  fs.writeFileSync(outPath, JSON.stringify(record, null, 2));
  console.log(`  written:      ${outPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
