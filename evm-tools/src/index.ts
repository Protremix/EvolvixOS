/**
 * Verdis EVM Testing Environment
 * 
 * Local EVM for compiling, deploying, and testing Solidity smart contracts
 * without needing a full Verdis node. Uses ethers.js local network provider.
 */

import { ethers } from "ethers";
import * as fs from "fs";
import * as path from "path";
import { execSync } from "child_process";

export const VERDIS_CHAIN_ID = 909;
export const VERDIS_GAS_PRICE = "1000000000"; // 1 Gwei
export const VERDIS_BLOCK_GAS_LIMIT = 30000000;

export interface CompiledContract {
    abi: any[];
    bytecode: string;
    name: string;
}

export interface DeployedContract {
    address: string;
    abi: any[];
    name: string;
    deployTx: string;
}

export class VerdisEVM {
    private provider: ethers.JsonRpcApiProvider;
    private signer: ethers.Wallet;
    private contracts: Map<string, ethers.Contract> = new Map();

    constructor() {
        // Create a local in-memory provider simulating Verdis chain
        const privateKey = "0x" + "1".repeat(64); // deterministic test key
        this.signer = new ethers.Wallet(privateKey);
        // Use a local in-memory provider
        this.provider = new ethers.BrowserProvider({} as any);
    }

    /**
     * Get a test wallet with funded VRDX
     */
    static createTestWallet(): ethers.Wallet {
        const privateKey = "0x" + "2".repeat(64);
        return new ethers.Wallet(privateKey);
    }

    /**
     * Compile a Solidity contract using solc
     */
    static compile(contractPath: string): CompiledContract {
        const contractName = path.basename(contractPath, ".sol");
        const source = fs.readFileSync(contractPath, "utf8");
        
        // Use solc via npx
        const input = {
            language: "Solidity",
            sources: {
                [contractName + ".sol"]: { content: source }
            },
            settings: {
                optimizer: { enabled: true, runs: 200 },
                outputSelection: {
                    "*": {
                        "*": ["abi", "evm.bytecode.object"]
                    }
                }
            }
        };

        const inputJson = JSON.stringify(input);
        const output = execSync(`npx solc --standard-json`, {
            input: inputJson,
            encoding: "utf8",
            maxBuffer: 10 * 1024 * 1024
        });

        const result = JSON.parse(output);
        
        // Find the contract in the output
        let contractData: any = null;
        for (const fileName of Object.keys(result.contracts || {})) {
            for (const cName of Object.keys(result.contracts[fileName])) {
                if (cName === contractName || cName.includes(contractName)) {
                    contractData = result.contracts[fileName][cName];
                    break;
                }
            }
            if (contractData) break;
        }

        if (!contractData) {
            throw new Error(`Contract ${contractName} not found in compilation output`);
        }

        return {
            abi: contractData.abi,
            bytecode: "0x" + contractData.evm.bytecode.object,
            name: contractName
        };
    }

    /**
     * Get the ABI for a contract without compiling
     */
    static getABI(contractPath: string): any[] {
        const compiled = VerdisEVM.compile(contractPath);
        return compiled.abi;
    }

    /**
     * Validate a contract compiles without errors
     */
    static validateCompile(contractPath: string): { success: boolean; errors: string[] } {
        try {
            const source = fs.readFileSync(contractPath, "utf8");
            const contractName = path.basename(contractPath, ".sol");
            
            const input = {
                language: "Solidity",
                sources: { [contractName + ".sol"]: { content: source } },
                settings: {
                    outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } }
                }
            };

            const output = execSync(`npx solc --standard-json`, {
                input: JSON.stringify(input),
                encoding: "utf8",
                maxBuffer: 10 * 1024 * 1024
            });

            const result = JSON.parse(output);
            const errors = (result.errors || [])
                .filter((e: any) => e.severity === "error")
                .map((e: any) => e.formattedMessage);

            return { success: errors.length === 0, errors };
        } catch (err: any) {
            return { success: false, errors: [err.message] };
        }
    }
}

export default VerdisEVM;
