export class ParallelExecutor {
    workers: number = 4;
    stats = {
        totalTransactions: 0,
        groupsFormed: 0,
        conflictsDetected: 0,
        parallelismRatio: 1.0
    };

    analyzeConflicts(txs: any[]): any[][] {
        if (!txs || txs.length === 0) return [];

        const groups: any[][] = [];
        const writeSet = new Map<string, number>();
        const readSet = new Map<string, Set<number>>();
        let conflictsCount = 0;

        for (const tx of txs) {
            const writes: string[] = tx.writes || tx.writeAccounts || (tx.from && tx.to ? [tx.from, tx.to] : (tx.from ? [tx.from] : []));
            const reads: string[] = tx.reads || tx.readAccounts || (tx.from ? [tx.from] : []);

            const conflictingGroups = new Set<number>();

            for (const addr of writes) {
                if (writeSet.has(addr)) conflictingGroups.add(writeSet.get(addr)!);
                if (readSet.has(addr)) {
                    for (const g of readSet.get(addr)!) conflictingGroups.add(g);
                }
            }

            for (const addr of reads) {
                if (writeSet.has(addr)) conflictingGroups.add(writeSet.get(addr)!);
            }

            if (conflictingGroups.size === 0) {
                const groupIdx = groups.length;
                groups.push([tx]);
                for (const addr of writes) writeSet.set(addr, groupIdx);
                for (const addr of reads) {
                    if (!readSet.has(addr)) readSet.set(addr, new Set());
                    readSet.get(addr)!.add(groupIdx);
                }
            } else {
                conflictsCount += conflictingGroups.size;
                const sortedGroups = [...conflictingGroups].sort((a, b) => a - b);
                const targetGroup = sortedGroups[0];

                for (let i = 1; i < sortedGroups.length; i++) {
                    const g = sortedGroups[i];
                    groups[targetGroup].push(...groups[g]);
                    (groups as any)[g] = null;
                    for (const [addr, gi] of writeSet) if (gi === g) writeSet.set(addr, targetGroup);
                    for (const [addr, set] of readSet) {
                        if (set.has(g)) { set.delete(g); set.add(targetGroup); }
                    }
                }
                groups[targetGroup].push(tx);

                for (const addr of writes) writeSet.set(addr, targetGroup);
                for (const addr of reads) {
                    if (!readSet.has(addr)) readSet.set(addr, new Set());
                    readSet.get(addr)!.add(targetGroup);
                }
            }
        }

        const filteredGroups = groups.filter(g => g !== null);

        const totalTx = txs.length;
        const numGroups = filteredGroups.length;
        const ratio = numGroups > 0 ? Number((totalTx / numGroups).toFixed(2)) : 1.0;

        this.stats.totalTransactions += totalTx;
        this.stats.groupsFormed += numGroups;
        this.stats.conflictsDetected += conflictsCount;
        this.stats.parallelismRatio = ratio;

        return filteredGroups;
    }

    async executeParallel(txs: any[], processFn: (tx: any) => Promise<any> | any): Promise<any[]> {
        if (!txs || txs.length === 0) return [];
        const groups = this.analyzeConflicts(txs);
        const results = new Array(txs.length);

        const promises = groups.map(async (group) => {
            const groupResults = [];
            for (const tx of group) {
                const result = await processFn(tx);
                groupResults.push({ tx, result });
            }
            return groupResults;
        });

        const groupResults = await Promise.all(promises);

        const txIndexMap = new Map();
        txs.forEach((tx, i) => txIndexMap.set(tx, i));
        for (const group of groupResults) {
            for (const { tx, result } of group) {
                results[txIndexMap.get(tx)] = result;
            }
        }

        return results;
    }

    getStats() {
        return {
            groupsFormed: this.stats.groupsFormed,
            parallelismRatio: this.stats.parallelismRatio,
            conflictsDetected: this.stats.conflictsDetected,
            totalTransactions: this.stats.totalTransactions,
            workers: this.workers
        };
    }
}
