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

function getBlockOfPeriod(period) {
    return Math.floor((period - 1) / 2) + 1;
}

function getPeriodsOfBlock(block) {
    return [block * 2 - 1, block * 2];
}

export function getLabelOfPeriods(periods) {
    periods = [...new Set(periods)].sort();

    // work out whether we can display as "Block X" or "Stunde X"
    let allBlockPeriods = new Set(
        [].concat(...periods.map(p => getPeriodsOfBlock(getBlockOfPeriod(p))))
    );

    if ([...allBlockPeriods].every(p => periods.includes(p))) {
        // block label
        let blocks = [...new Set(periods.map(p => getBlockOfPeriod(p)))].sort();
        let seqs = increasingSequences(blocks);
        let out = [];

        for (let seq of seqs) {
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

    } else {
        // stunde label
        let seqs = increasingSequences(periods);
        let out = [];

        for (let seq of seqs) {
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
}