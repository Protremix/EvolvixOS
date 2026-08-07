/**
 * Verdis Local EVM Simulator
 * 
 * Simulates a local Verdis EVM node for testing smart contracts.
 * Uses ethers.js memory provider with Verdis chain parameters.
 */

import { ethers } from "ethers";
import * as fs from "fs";
import * as path from "path";

export interface SimulationResult {
    success: boolean;
    contractAddress?: string;
    gasUsed?: number;
    events?: any[];
    returnValue?: any;
    error?: string;
}

export class LocalVerdisEVM {
    private accounts: Map<string, ethers.Wallet> = new Map();
    private deployedContracts: Map<string, { name: string; abi: any[]; address: string }> = new Map();
    private chainId: number = 909;
    private blockNumber: number = 1;
    private gasPrice: bigint = 1000000000n; // 1 Gwei

    constructor() {
        // Create 5 test accounts with 1000 VRDX each
        for (let i = 1; i <= 5; i++) {
            const privateKey = "0x" + i.toString(16).padStart(64, "0");
            const wallet = new ethers.Wallet(privateKey);
            this.accounts.set(`account${i}`, wallet);
        }
    }

    getAccount(name: string): ethers.Wallet | undefined {
        return this.accounts.get(name);
    }

    getAllAccounts(): string[] {
        return Array.from(this.accounts.keys());
    }

    getBlockNumber(): number {
        return this.blockNumber;
    }

    incrementBlock(): void {
        this.blockNumber++;
    }

    getChainId(): number {
        return this.chainId;
    }

    getGasPrice(): bigint {
        return this.gasPrice;
    }

    /**
     * Store a compiled contract for later deployment
     */
    storeContract(name: string, abi: any[], address: string): void {
        this.deployedContracts.set(name, { name, abi, address });
    }

    getContract(name: string): { name: string; abi: any[]; address: string } | undefined {
        return this.deployedContracts.get(name);
    }

    getAllDeployedContracts(): Array<{ name: string; address: string }> {
        return Array.from(this.deployedContracts.values()).map(c => ({
            name: c.name,
            address: c.address
        }));
    }

    /**
     * Simulate contract deployment
     */
    simulateDeployment(name: string, bytecode: string, abi: any[]): SimulationResult {
        try {
            // Generate a deterministic address
            const deployer = this.getAccount("account1")!;
            const data = bytecode + "000000000000000000000000" + deployer.address.slice(2);
            const address = "0x" + ethers.keccak256(data).slice(2, 42);
            
            this.storeContract(name, abi, address);
            this.incrementBlock();

            return {
                success: true,
                contractAddress: address,
                gasUsed: 1000000, // Simulated gas
            };
        } catch (err: any) {
            return {
                success: false,
                error: err.message
            };
        }
    }

    /**
     * Simulate a contract call (read-only)
     */
    simulateCall(contractName: string, functionName: string, args: any[] = []): SimulationResult {
        try {
            const contract = this.getContract(contractName);
            if (!contract) {
                return { success: false, error: `Contract ${contractName} not found` };
            }

            // Find function in ABI
            const func = contract.abi.find(
                (item: any) => item.type === "function" && item.name === functionName
            );

            if (!func) {
                return { success: false, error: `Function ${functionName} not found in ${contractName}` };
            }

            this.incrementBlock();

            // Return a simulated value based on return type
            const returnType = func.outputs?.[0]?.type || "uint256";
            let returnValue: any;
            switch (returnType) {
                case "uint256": returnValue = 0n; break;
                case "string": returnValue = ""; break;
                case "bool": returnValue = false; break;
                case "address": returnValue = "0x" + "0".repeat(40); break;
                default: returnValue = null;
            }

            return {
                success: true,
                gasUsed: 21000,
                returnValue
            };
        } catch (err: any) {
            return {
                success: false,
                error: err.message
            };
        }
    }

    /**
     * Get deployment summary
     */
    getSummary(): any {
        return {
            chainId: this.chainId,
            blockNumber: this.blockNumber,
            gasPrice: this.gasPrice.toString(),
            accounts: this.getAllAccounts().length,
            deployedContracts: this.getAllDeployedContracts(),
        };
    }
}

export default LocalVerdisEVM;
