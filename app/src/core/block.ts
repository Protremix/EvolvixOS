import { Block, BlockHeader, Transaction } from '../types';
import { sha256, doubleSha256 } from '../crypto';

export class MerkleTree {
  private levels: string[][] = [];

  constructor(transactions: Transaction[]) {
    this.buildTree(transactions);
  }

  private buildTree(transactions: Transaction[]): void {
    if (!transactions || transactions.length === 0) {
      this.levels = [[sha256('')]];
      return;
    }

    let currentLevel: string[] = transactions.map((tx) => sha256(tx.id));
    this.levels = [currentLevel];

    while (currentLevel.length > 1) {
      if (currentLevel.length % 2 !== 0) {
        currentLevel.push(currentLevel[currentLevel.length - 1]);
      }

      const nextLevel: string[] = [];
      for (let i = 0; i < currentLevel.length; i += 2) {
        const combined = currentLevel[i] + currentLevel[i + 1];
        nextLevel.push(sha256(combined));
      }

      this.levels.push(nextLevel);
      currentLevel = nextLevel;
    }
  }

  getRoot(): string {
    if (this.levels.length === 0 || this.levels[this.levels.length - 1].length === 0) {
      return sha256('');
    }
    return this.levels[this.levels.length - 1][0];
  }

  getProof(txHash: string): { hash: string; direction: 'left' | 'right' }[] {
    if (!txHash || this.levels.length === 0 || this.levels[0].length === 0) {
      return [];
    }

    const hashedTarget = sha256(txHash);
    let index = this.levels[0].indexOf(hashedTarget);
    if (index === -1) {
      index = this.levels[0].indexOf(txHash);
    }
    if (index === -1) {
      return [];
    }

    const proof: { hash: string; direction: 'left' | 'right' }[] = [];

    for (let l = 0; l < this.levels.length - 1; l++) {
      const currentLevel = this.levels[l];
      const isEven = index % 2 === 0;
      const pairIndex = isEven ? index + 1 : index - 1;

      let siblingHash: string;
      if (pairIndex < currentLevel.length) {
        siblingHash = currentLevel[pairIndex];
      } else {
        siblingHash = currentLevel[index];
      }

      proof.push({
        hash: siblingHash,
        direction: isEven ? 'right' : 'left',
      });

      index = Math.floor(index / 2);
    }

    return proof;
  }

  static verifyProof(
    txHash: string,
    proof: { hash: string; direction: 'left' | 'right' }[],
    root: string
  ): boolean {
    if (!txHash || !root) return false;

    let currentHash = sha256(txHash);
    for (const step of proof) {
      if (step.direction === 'left') {
        currentHash = sha256(step.hash + currentHash);
      } else {
        currentHash = sha256(currentHash + step.hash);
      }
    }
    if (currentHash === root) {
      return true;
    }

    currentHash = txHash;
    for (const step of proof) {
      if (step.direction === 'left') {
        currentHash = sha256(step.hash + currentHash);
      } else {
        currentHash = sha256(currentHash + step.hash);
      }
    }

    return currentHash === root;
  }
}

export export function calculateBlockHash(header: BlockHeader): string {
  let data = `${header.index}${header.previousHash}${header.merkleRoot}${header.timestamp}${header.validator}${header.difficulty}${header.nonce}`;
  if (header.gasUsed !== undefined) {
    const withdrawalsStr = Array.isArray(header.withdrawals) ? JSON.stringify(header.withdrawals) : (header.withdrawals || "");
    data += `${header.gasUsed}${header.gasLimit}${header.baseFeePerGas || 0}${header.extraData || ""}${header.withdrawalsRoot || ""}${withdrawalsStr}${header.blobGasUsed || 0}${header.excessBlobGas || 0}${header.parentBeaconBlockRoot || ""}`;
  }
  return doubleSha256(data);
}

export function createBlock(
  index: number,
  previousHash: string,
  transactions: Transaction[],
  validator: string,
  validatorSignature: string,
  difficulty: number,
  nonce: number,
  timestamp: number = Date.now(),
  gasUsed: number = 0,
  gasLimit: number = 30000000,
  baseFee: number = 1000000000,
  extraData: string = '0x',
  withdrawalsRoot: string | null = null,
  withdrawals: any[] = [],
  blobGasUsed: number = 0,
  excessBlobGas: number = 0,
  parentBeaconBlockRoot: string | null = null
): Block {
  const merkleTree = new MerkleTree(transactions);
  const merkleRoot = merkleTree.getRoot();

  const header: BlockHeader = {
    index,
    previousHash,
    timestamp,
    merkleRoot,
    validator,
    validatorSignature,
    difficulty,
    nonce,
    gasUsed,
    gasLimit,
    baseFee,
    extraData,
    withdrawalsRoot,
    withdrawals,
    blobGasUsed,
    excessBlobGas,
    parentBeaconBlockRoot,
  };

  const hash = calculateBlockHash(header);

  return {
    header,
    transactions,
    hash,
  };
}

export function validateBlock(block: Block, previousBlock: Block): boolean {
  if (!block || !previousBlock || !block.header || !previousBlock.header) {
    return false;
  }

  if (block.header.index !== previousBlock.header.index + 1) {
    return false;
  }

  if (block.header.previousHash !== previousBlock.hash) {
    return false;
  }

  const expectedMerkleRoot = new MerkleTree(block.transactions).getRoot();
  if (block.header.merkleRoot !== expectedMerkleRoot) {
    return false;
  }

  const expectedHash = calculateBlockHash(block.header);
  if (block.hash !== expectedHash) {
    return false;
  }

  if (!block.header.validatorSignature || block.header.validatorSignature.trim() === '') {
    return false;
  }

  if (!block.header.validator || block.header.validator.trim() === '') {
    return false;
  }

  return true;
}

export function isChainValid(chain: Block[]): boolean {
  if (!Array.isArray(chain) || chain.length === 0) {
    return false;
  }

  const genesisBlock = chain[0];

  if (genesisBlock.header.index !== 0) {
    return false;
  }

  const computedGenesisMerkle = new MerkleTree(genesisBlock.transactions).getRoot();
  if (genesisBlock.header.merkleRoot !== computedGenesisMerkle) {
    return false;
  }

  if (genesisBlock.hash !== calculateBlockHash(genesisBlock.header)) {
    return false;
  }

  if (!genesisBlock.header.validatorSignature || genesisBlock.header.validatorSignature.trim() === '') {
    return false;
  }

  for (let i = 1; i < chain.length; i++) {
    const currentBlock = chain[i];
    const previousBlock = chain[i - 1];

    if (!validateBlock(currentBlock, previousBlock)) {
      return false;
    }
  }

  return true;
}

export function createGenesisBlock(): Block {
  const transactions: Transaction[] = [];
  const merkleRoot = new MerkleTree(transactions).getRoot();

  const genesisHeader: BlockHeader = {
    index: 0,
    previousHash: '0'.repeat(64),
    timestamp: 0,
    merkleRoot,
    validator: 'genesis',
    validatorSignature: 'genesis',
    difficulty: 0,
    nonce: 0,
    gasUsed: 0,
    gasLimit: 30000000,
    baseFee: 1000000000,
    extraData: '0x',
    withdrawalsRoot: null,
    withdrawals: [],
    blobGasUsed: 0,
    excessBlobGas: 0,
    parentBeaconBlockRoot: null,
  };

  const hash = calculateBlockHash(genesisHeader);

  return {
    header: genesisHeader,
    transactions,
    hash,
  };
}
