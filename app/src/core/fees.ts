export interface FeeCalculationResult {
    burned: number;
    tip: number;
    effectiveGasPrice: number;
    totalFee: number;
}

export class FeeManager {
    public baseFee: number = 1000000000;
    public gasLimit: number = 30000000;
    public targetGas: number = 15000000;
    public baseFeeMaxChangeDenominator: number = 8;
    public totalBurned: number = 0;

    constructor() {}

    public calculateBaseFee(parentGasUsed: number = 0, parentBaseFee: number = this.baseFee): number {
        if (parentBaseFee === undefined || parentBaseFee === null) {
            parentBaseFee = this.baseFee;
        }
        if (parentGasUsed === undefined || parentGasUsed === null) {
            parentGasUsed = 0;
        }

        if (parentGasUsed === this.targetGas) {
            return parentBaseFee;
        }

        if (parentGasUsed > this.targetGas) {
            const gasUsedDelta = parentGasUsed - this.targetGas;
            const baseFeeDelta = Math.floor((parentBaseFee * gasUsedDelta) / (this.targetGas * this.baseFeeMaxChangeDenominator));
            return parentBaseFee + Math.max(1, baseFeeDelta);
        } else {
            const gasUsedDelta = this.targetGas - parentGasUsed;
            const baseFeeDelta = Math.floor((parentBaseFee * gasUsedDelta) / (this.targetGas * this.baseFeeMaxChangeDenominator));
            return Math.max(1, parentBaseFee - baseFeeDelta);
        }
    }

    public calculateFee(
        gasUsed: number = 21000,
        maxFeePerGas?: number,
        maxPriorityFeePerGas: number = 0,
        baseFee?: number
    ): FeeCalculationResult {
        const currentBaseFee = (baseFee !== undefined && baseFee !== null) ? baseFee : this.baseFee;
        const priorityFee = (maxPriorityFeePerGas !== undefined && maxPriorityFeePerGas !== null) ? maxPriorityFeePerGas : 0;

        let maxFee: number;
        if (maxFeePerGas !== undefined && maxFeePerGas !== null) {
            maxFee = maxFeePerGas;
        } else {
            maxFee = currentBaseFee + priorityFee;
        }

        const effectiveGasPrice = Math.min(maxFee, currentBaseFee + priorityFee);
        const tipPerGas = Math.max(0, effectiveGasPrice - currentBaseFee);
        const burnedPerGas = Math.min(effectiveGasPrice, currentBaseFee);

        const burned = burnedPerGas * gasUsed;
        const tip = tipPerGas * gasUsed;
        const totalFee = effectiveGasPrice * gasUsed;

        return {
            burned,
            tip,
            effectiveGasPrice,
            totalFee
        };
    }

    public getBaseFee(): number {
        return this.baseFee;
    }

    public updateBaseFee(gasUsed: number): number {
        const newBaseFee = this.calculateBaseFee(gasUsed, this.baseFee);
        this.baseFee = newBaseFee;
        return this.baseFee;
    }

    public addBurned(amount: number): void {
        if (amount > 0) {
            this.totalBurned += amount;
        }
    }

    public getTotalBurned(): number {
        return this.totalBurned;
    }
}

export const feeManager = new FeeManager();
