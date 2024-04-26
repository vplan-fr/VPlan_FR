import {arraysEqual} from "./utils.js";

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


function periods_to_periods_label(periods) {
    // stunde label
    let seqs = increasingSequences(periods);
    let out = [];

    for (let seq of seqs) {
        if (seq.length === 1) {
            out.push(`${seq[0]}`);
        // } else if (seq.length === 2) {
        //     out.push(`${seq[0]},${seq[seq.length - 1]}`);
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

function periods_to_block_label_no_single_periods(periods) {
    // block label
    let blocks = [...new Set(periods.map(p => getBlockOfPeriod(p)))].sort();
    let seqs = increasingSequences(blocks);
    let out = [];

    for (let seq of seqs) {
        if (seq.length === 1) {
            out.push(`${seq[0]}`);
        // } else if (seq.length === 2) {
        //     out.push(`${seq[0]},${seq[seq.length - 1]}`);
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


export function getLabelOfPeriods(periods, block_config) {
    if (block_config == null) {
        console.log("Warning: block_config is null in getLabelOfPeriods");
        return periods_to_periods_label(periods);
    }
    // find key of block_config that contains periods
    let block = Object.keys(block_config).find(key => block_config[key].periods.includes(periods[0]));
    if (block == null) {
        return periods_to_periods_label(periods);
    }
    let block_periods = block_config[block].periods;
    if (arraysEqual(block_periods, periods)) {
        return block_config[block].label;
    }

    return periods_to_periods_label(periods);
}

export function getLabelOfBlock(block, block_config) {
    if (block_config == null) {
        console.log("Warning: block_config is null in getLabelOfBlock");
        return `Block ${block}`;
    }

    if (block_config[block] != null) {
        return block_config[block].label;
    } else {
        return `Block ${block}`;
    }
}