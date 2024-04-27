from __future__ import annotations

import dataclasses
import datetime
import typing

from . import models, vplan_utils


@dataclasses.dataclass
class BlockConfiguration:
    """
    Different schools have different ways of organizing their schedules. Periods get grouped into blocks. An object of
    this class represents these decisions. Blocks are relevant for grouping lessons, as only lessons belonging to
    the same block can get grouped.

    Usually, a block consists of exactly two periods.
    Some schools also mix blocks and periods, so a block can consist of just one period. If a school has such abstract
    blocks, we always fall back to "Stunde X" when labelling.
    """
    # dict of logical block number to contained periods
    # when empty, the schedule is assumed to consist of single periods
    blocks: dict[int, list[int]]

    TRIVIAL: typing.ClassVar[BlockConfiguration]  # with blocks = {}

    def get_block_of_period(self, period: int) -> int:
        for block, periods in self.blocks.items():
            if period in periods:
                return block

        # any period after the last block is assumed to be in its own block
        # unfortunately many schools just don't report their periods properly
        # this ensures that we don't crash

        max_block = max(self.blocks, default=0)
        min_block = min(self.blocks, default=0)

        max_period = max(self.get_periods_of_block(max_block))
        min_period = min(self.get_periods_of_block(min_block))

        if period > min_period:
            return max_block + (period - max_period)
        else:
            return min_block - (min_period - period)

    def get_periods_of_block(self, block: int) -> list[int]:
        if not self.blocks:
            return [block]

        try:
            return self.blocks[block]
        except KeyError:
            max_block = max(self.blocks)
            min_block = min(self.blocks)

            if block < min_block:
                min_period = min(self.get_periods_of_block(min_block))
                return [block + min_block - min_period]
            else:
                max_period = max(self.get_periods_of_block(max_block))
                return [block - max_block + max_period]

    def has_abstract_blocks(self) -> bool:
        return any(len(periods) == 1 for periods in self.blocks.values())

    @staticmethod
    def _label_periods(periods: list[int]) -> str:
        seqs = vplan_utils._increasing_sequences(periods)
        out = []
        for seq in seqs:
            if len(seq) == 1:
                out.append(f"{seq[0]}")
            elif len(seq) == 2:
                out.append(f"{seq[0]},{seq[-1]}")
            else:
                out.append(f"{seq[0]}-{seq[-1]}")

        if len(periods) == 1:
            return f"Stunde {out[0]}"
        else:
            return f"Stunden {','.join(out)}"

    def _label_blocks(self, periods: list[int]) -> str:
        blocks = sorted(set(self.get_block_of_period(p) for p in periods))
        seqs = vplan_utils._increasing_sequences(blocks)
        out = []
        for seq in seqs:
            if len(seq) == 1:
                out.append(f"{seq[0]}")
            elif len(seq) == 2:
                out.append(f"{seq[0]},{seq[-1]}")
            else:
                out.append(f"{seq[0]}-{seq[-1]}")

        if len(blocks) == 1:
            return f"Block {out[0]}"
        else:
            return f"Blöcke {','.join(out)}"

    def get_label_of_periods(self, periods: typing.Iterable[int]) -> str:
        periods = sorted(set(periods))

        if not self.blocks or self.has_abstract_blocks():
            return self._label_periods(periods)

        if any(len(self.get_periods_of_block(self.get_block_of_period(p))) == 1 for p in periods):
            return self._label_periods(periods)

        # work out whether we can display as "Block X" or "Stunde X"
        all_block_periods = set(sum((self.get_periods_of_block(self.get_block_of_period(p)) for p in periods), []))
        if not all_block_periods - set(periods):
            return self._label_blocks(periods)
        else:
            return self._label_periods(periods)

    @staticmethod
    def _sub_times(a: datetime.time, b: datetime.time) -> datetime.timedelta:
        return datetime.datetime.combine(datetime.date.min, a) - datetime.datetime.combine(datetime.date.min, b)

    @classmethod
    def from_default_times(cls, default_times: models.DefaultTimesInfo) -> BlockConfiguration:
        if not default_times.data:
            return cls.TRIVIAL

        if list(range(min(default_times.data), max(default_times.data) + 1)) != sorted(default_times.data.keys()):
            # I'm literally going insane, why would any school do this helpppp
            return cls.TRIVIAL

        blocks: list[list[int]] = []

        last_period_end: datetime.time | None = None

        for period, (start, end) in default_times.data.items():
            if last_period_end == start and last_period_end is not None:
                blocks[-1].append(period)
            else:
                blocks.append([period])

            last_period_end = end

        blocks2: list[list[int]] = []

        last_block_end: datetime.time | None = None

        for block_periods in blocks:
            this_block_start, this_block_end = default_times.data[block_periods[-1]]

            cond = (
                len(block_periods) == 1
                and last_block_end is not None
                and cls._sub_times(this_block_start, last_block_end) <= datetime.timedelta(minutes=5)
            )

            if cond:
                blocks2[-1] = blocks2[-1] + block_periods
            else:
                blocks2.append(block_periods)

            if len(block_periods) == 1:
                last_block_end = this_block_end
            else:
                last_block_end = None

        if any(len(block) > 2 for block in blocks2):
            # assume something went wrong
            return cls.TRIVIAL
        else:
            return cls({i: block for i, block in enumerate(blocks2, 1)})


BlockConfiguration.TRIVIAL = BlockConfiguration({})
