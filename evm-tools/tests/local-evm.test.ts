/**
 * Tests for LocalVerdisEVM Simulator
 */

import { LocalVerdisEVM } from "../src/local-evm";
import { ethers } from "ethers";

describe("LocalVerdisEVM Simulator", () => {
    let evm: LocalVerdisEVM;

    beforeEach(() => {
        evm = new LocalVerdisEVM();
    });

    describe("Initialization", () => {
        it("should have chain ID 909", () => {
            expect(evm.getChainId()).toBe(909);
        });

        it("should start at block 1", () => {
            expect(evm.getBlockNumber()).toBe(1);
        });

        it("should have 1 Gwei gas price", () => {
            expect(evm.getGasPrice()).toBe(1000000000n);
        });

        it("should create 5 test accounts", () => {
            expect(evm.getAllAccounts().length).toBe(5);
            expect(evm.getAllAccounts()).toContain("account1");
            expect(evm.getAllAccounts()).toContain("account5");
        });

        it("should return valid Ethereum addresses for accounts", () => {
            const account1 = evm.getAccount("account1");
            expect(account1).toBeDefined();
            expect(account1!.address).toMatch(/^0x[a-fA-F0-9]{40}$/);
        });
    });

    describe("Block Management", () => {
        it("should increment block number", () => {
            expect(evm.getBlockNumber()).toBe(1);
            evm.incrementBlock();
            expect(evm.getBlockNumber()).toBe(2);
            evm.incrementBlock();
            expect(evm.getBlockNumber()).toBe(3);
        });
    });

    describe("Contract Deployment Simulation", () => {
        it("should simulate contract deployment", () => {
            const abi = [{ type: "function", name: "test", inputs: [], outputs: [{ type: "uint256" }] }];
            const result = evm.simulateDeployment("TestToken", "0x6080604052", abi);
            expect(result.success).toBe(true);
            expect(result.contractAddress).toMatch(/^0x[a-fA-F0-9]{40}$/);
            expect(result.gasUsed).toBeGreaterThan(0);
        });

        it("should increment block after deployment", () => {
            const blockBefore = evm.getBlockNumber();
            evm.simulateDeployment("Test", "0x", []);
            expect(evm.getBlockNumber()).toBe(blockBefore + 1);
        });

        it("should store deployed contract", () => {
            const abi = [{ type: "function", name: "balance", inputs: [], outputs: [{ type: "uint256" }] }];
            evm.simulateDeployment("MyToken", "0x", abi);
            const contract = evm.getContract("MyToken");
            expect(contract).toBeDefined();
            expect(contract!.name).toBe("MyToken");
            expect(contract!.abi).toBe(abi);
        });

        it("should list all deployed contracts", () => {
            evm.simulateDeployment("Token1", "0x", []);
            evm.simulateDeployment("Token2", "0x", []);
            const contracts = evm.getAllDeployedContracts();
            expect(contracts.length).toBe(2);
            expect(contracts.map(c => c.name)).toContain("Token1");
            expect(contracts.map(c => c.name)).toContain("Token2");
        });
    });

    describe("Contract Call Simulation", () => {
        beforeEach(() => {
            const abi = [
                { type: "function", name: "totalSupply", inputs: [], outputs: [{ type: "uint256" }], stateMutability: "view" },
                { type: "function", name: "name", inputs: [], outputs: [{ type: "string" }], stateMutability: "view" },
                { type: "function", name: "decimals", inputs: [], outputs: [{ type: "uint8" }], stateMutability: "view" },
                { type: "function", name: "owner", inputs: [], outputs: [{ type: "address" }], stateMutability: "view" },
                { type: "function", name: "paused", inputs: [], outputs: [{ type: "bool" }], stateMutability: "view" },
            ];
            evm.simulateDeployment("TestToken", "0x6080", abi);
        });

        it("should simulate uint256 call", () => {
            const result = evm.simulateCall("TestToken", "totalSupply");
            expect(result.success).toBe(true);
            expect(result.gasUsed).toBe(21000);
        });

        it("should simulate string call", () => {
            const result = evm.simulateCall("TestToken", "name");
            expect(result.success).toBe(true);
        });

        it("should fail for non-existent contract", () => {
            const result = evm.simulateCall("NonExistent", "test");
            expect(result.success).toBe(false);
            expect(result.error).toContain("not found");
        });

        it("should fail for non-existent function", () => {
            const result = evm.simulateCall("TestToken", "nonExistentFunction");
            expect(result.success).toBe(false);
            expect(result.error).toContain("not found");
        });

        it("should increment block after call", () => {
            const blockBefore = evm.getBlockNumber();
            evm.simulateCall("TestToken", "totalSupply");
            expect(evm.getBlockNumber()).toBe(blockBefore + 1);
        });
    });

    describe("Summary", () => {
        it("should return valid summary", () => {
            evm.simulateDeployment("Token", "0x", []);
            const summary = evm.getSummary();
            expect(summary.chainId).toBe(909);
            expect(summary.blockNumber).toBe(2);
            expect(summary.gasPrice).toBe("1000000000");
            expect(summary.accounts).toBe(5);
            expect(summary.deployedContracts.length).toBe(1);
        });
    });
});
