function increasingSequences(seq, key = x => x) {
    let out = [];
    let currentSeq = [];
    let last = null;

    for (let elem of seq) {
        if (last === elem) {
            // fallback if something bad happens
            return [[elem]];
        }

        if (last === null || key(elem) === key(last) + 1) {
            currentSeq.push(elem);
        } else {
            out.push(currentSeq);
            currentSeq = [elem];
        }

        last = elem;
    }

    out.push(currentSeq);

    return out;
}


export class BlockConfiguration {
    /**
     * Different schools have different ways of organizing their schedules. Periods get grouped into blocks. An object of
     * this class represents these decisions. Blocks are relevant for grouping lessons, as only lessons belonging to
     * the same block can get grouped.
     *
     * Usually, a block consists of exactly two periods.
     * Some schools also mix blocks and periods, so a block can consist of just one period. If a school has such abstract
     * blocks, we always fall back to "Stunde X" when labeling.
     * @param {Object.<number, number[]>} blocks - Dictionary of logical block number to contained periods
     */
    constructor(blocks) {
        this.blocks = blocks;
    }

    /**
     * Get the block of the given period.
     * @param {number} period - Period number
     * @returns {number} - Block number
     */
    getBlockOfPeriod(period) {
        for (const [block, periods] of Object.entries(this.blocks)) {
            if (periods.includes(period)) {
                return parseInt(block);
            }
        }

        // Any period after the last block is assumed to be in its own block
        // Unfortunately, many schools just don't report their periods properly
        // This ensures that we don't crash
        const maxBlock = Math.max(...Object.keys(this.blocks).map(Number), 0);
        const minBlock = Math.min(...Object.keys(this.blocks).map(Number), 0);

        const maxPeriod = Math.max(...this.getPeriodsOfBlock(maxBlock));
        const minPeriod = Math.min(...this.getPeriodsOfBlock(minBlock));

        if (period > minPeriod) {
            return maxBlock + (period - maxPeriod);
        } else {
            return minBlock - (minPeriod - period);
        }
    }

    /**
     * Get periods of the given block.
     * @param {number} block - Block number
     * @returns {number[]} - List of period numbers
     */
    getPeriodsOfBlock(block) {
        if (Object.keys(this.blocks).length === 0) {
            return [block];
        }

        try {
            return this.blocks[block];
        } catch (error) {
            const maxBlock = Math.max(...Object.keys(this.blocks).map(Number));
            const minBlock = Math.min(...Object.keys(this.blocks).map(Number));

            if (block < minBlock) {
                const minPeriod = Math.min(...this.getPeriodsOfBlock(minBlock));
                return [block + minBlock - minPeriod];
            } else {
                const maxPeriod = Math.max(...this.getPeriodsOfBlock(maxBlock));
                return [block - maxBlock + maxPeriod];
            }
        }
    }

    /**
     * Check if there are abstract blocks.
     * @returns {boolean} - Whether there are abstract blocks
     */
    hasAbstractBlocks() {
        return Object.values(this.blocks).some(periods => periods.length === 1);
    }

    /**
     * Label periods.
     * @param {number[]} periods - List of period numbers
     * @returns {string} - Label for the periods
     */
    static labelPeriods(periods) {
        const seqs = increasingSequences(periods);
        const out = [];
        for (const seq of seqs) {
            if (seq.length === 1) {
                out.push(`${seq[0]}`);
            } else if (seq.length === 2) {
                out.push(`${seq[0]},${seq[seq.length - 1]}`);
            } else {
                out.push(`${seq[0]}-${seq[seq.length - 1]}`);
            }
        }

        if (periods.length === 1) {
            return `Stunde ${out[0]}`;
        } else {
            return `Stunden ${out.join(',')}`;
        }
    }

    /**
     * Label blocks.
     * @param {number[]} periods - List of period numbers
     * @returns {string} - Label for the blocks
     */
    labelBlocks(periods) {
        const blocks = [...new Set(periods.map(p => this.getBlockOfPeriod(p)))].sort((a, b) => a - b);
        const seqs = increasingSequences(blocks);
        const out = [];
        for (const seq of seqs) {
            if (seq.length === 1) {
                out.push(`${seq[0]}`);
            } else if (seq.length === 2) {
                out.push(`${seq[0]},${seq[seq.length - 1]}`);
            } else {
                out.push(`${seq[0]}-${seq[seq.length - 1]}`);
            }
        }

        if (blocks.length === 1) {
            return `Block ${out[0]}`;
        } else {
            return `Blöcke ${out.join(',')}`;
        }
    }

    /**
     * Get label of the given periods.
     * @param {number[]} periods - List of period numbers
     * @returns {string} - Label for the periods
     */
    getLabelOfPeriods(periods) {
        periods = [...new Set(periods)].sort((a, b) => a - b);

        if (Object.keys(this.blocks).length === 0 || this.hasAbstractBlocks()) {
            return BlockConfiguration.labelPeriods(periods);
        }

        if (periods.some(p => this.getPeriodsOfBlock(this.getBlockOfPeriod(p)).length === 1)) {
            return BlockConfiguration.labelPeriods(periods);
        }

        // Work out whether we can display as "Block X" or "Stunde X"
        const allBlockPeriods = new Set(periods.flatMap(p => this.getPeriodsOfBlock(this.getBlockOfPeriod(p))));
        if ([...allBlockPeriods].every(p => periods.includes(p))) {
            return this.labelBlocks(periods);
        } else {
            return BlockConfiguration.labelPeriods(periods);
        }
    }
}


export function getLabelOfPeriods(periods, block_config) {
    let _block_config = block_config == null ? {} : block_config;

    let block_config_instance = new BlockConfiguration(_block_config);

    return block_config_instance.getLabelOfPeriods(periods);
}

export function getLabelOfBlock(block, block_config) {
    let _block_config = block_config == null ? {} : block_config;

    let block_config_instance = new BlockConfiguration(_block_config);

    return block_config_instance.getLabelOfPeriods(block_config_instance.getPeriodsOfBlock(block));
}