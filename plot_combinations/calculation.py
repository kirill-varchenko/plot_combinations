import logging
from collections import Counter
from typing import Generic, Iterable, TypeVar

from tqdm import tqdm

logger = logging.getLogger("aa_combi")

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self) -> None:
        self._index = 0
        self._register: dict[T, int] = {}
        self._back_register: dict[int, T] = {}
        self._counter = Counter[T]()
        self._count = 0

    def add(self, item: T) -> int:
        if item not in self._register:
            idx = self._index
            self._register[item] = idx
            self._back_register[self._index] = item
            self._index += 1
        else:
            idx = self._register[item]

        self._counter[item] += 1
        self._count += 1
        return idx

    @property
    def count(self) -> int:
        return self._count

    @property
    def total(self) -> int:
        return self._counter.total()

    def index_to_value(self, idx: int) -> T:
        return self._back_register[idx]

    def get_count_for_index(self, idx: int) -> int:
        return self._counter[self._back_register[idx]]

    def most_common(self, n: int | None) -> list[tuple[T, int]]:
        return self._counter.most_common(n)


class AASubstituteRegistry(Registry[str]):
    def __init__(self) -> None:
        super().__init__()

    def filter_by_count(self, cutoff: int) -> set[int]:
        subs: set[int] = set()
        for sub, count in tqdm(
            self._counter.items(), desc="Filtering substitutes by count"
        ):
            if count >= cutoff:
                subs.add(self._register[sub])
        return subs


class AACombinationRegistry(Registry[frozenset[int]]):
    def __init__(self) -> None:
        super().__init__()

    def recount_with_intersection(self, aa_subs: set[int]) -> Counter[frozenset[int]]:
        new_combi_counter = Counter[frozenset[int]]()
        for combi, count in tqdm(self._counter.items(), desc="Recount combinations"):
            new_combi = frozenset(combi & aa_subs)
            new_combi_counter[new_combi] += count
        return new_combi_counter

    def filter_by_count(
        self,
        counter: Counter[frozenset[int]],
        cumcount_frac: float | None,
        min_freq: float | None,
        max_num: int | None,
    ) -> Counter[frozenset[int]]:
        new_combi_counter = Counter[frozenset[int]]()
        cumcount = 0
        i = 0
        max_cumcount = cumcount_frac * self._count if cumcount_frac else None
        total = counter.total()
        for combi, count in tqdm(
            counter.most_common(), desc="Filter combinations by count"
        ):
            new_combi_counter[combi] = count
            cumcount += count
            i += 1
            frequency = count / total
            if max_cumcount and cumcount >= max_cumcount:
                logger.info(
                    "Stop filtering by max cum count: %0.2f (%d)",
                    cumcount_frac,
                    max_cumcount,
                )
                break
            if min_freq and frequency < min_freq:
                logger.info("Stop filtering by min frequency: %0.2f", min_freq)
                break
            if max_num and i >= 20:
                logger.info("Stop filtering by max number: %d", max_num)
                break
        logger.info(
            "Filtered AA combinations cum count: %d (%0.2f)",
            cumcount,
            cumcount / total,
        )
        return new_combi_counter


def calculate(
    source: Iterable[str],
    aa_substitute_min_freq: float,
    aa_combination_max_cumfrac: float | None,
    aa_combination_min_freq: float | None,
    aa_combination_max_num: int | None,
) -> tuple[list[tuple[str, float]], list[tuple[set[str], float]]]:
    aa_substitute_registry = AASubstituteRegistry()
    aa_combination_registry = AACombinationRegistry()

    for line in tqdm(source, desc="Reading and counting"):
        line = line.strip()
        if not (line.startswith("(") and line.endswith(")")):
            continue
        subs = line.removeprefix("(").removesuffix(")").replace("_", ":").split(",")
        aa_set = frozenset(aa_substitute_registry.add(sub) for sub in subs)
        aa_combination_registry.add(aa_set)

    logger.info("Total: %d", aa_combination_registry.total)
    logger.info(
        "AA substitutes: unique %d, total %d",
        aa_substitute_registry.count,
        aa_substitute_registry.total,
    )
    logger.info(
        "AA combinations: unique %d, total %d",
        aa_combination_registry.count,
        aa_combination_registry.total,
    )

    aa_substitute_cutoff_abs = round(
        aa_substitute_min_freq * aa_combination_registry.total
    )
    good_subs = aa_substitute_registry.filter_by_count(aa_substitute_cutoff_abs)

    logger.info(
        "Filtered unique AA substitutions with cutoff %0.2f (%d): %d",
        aa_substitute_min_freq,
        aa_substitute_cutoff_abs,
        len(good_subs),
    )

    new_combi_counter = aa_combination_registry.recount_with_intersection(good_subs)
    logger.info("Recounted unique AA combinations: %d", len(new_combi_counter))

    good_combi = aa_combination_registry.filter_by_count(
        new_combi_counter,
        cumcount_frac=aa_combination_max_cumfrac,
        min_freq=aa_combination_min_freq,
        max_num=aa_combination_max_num,
    )
    logger.info("Filtered unique AA combinations: %d", len(good_combi))

    res_subs: list[tuple[str, float]] = [
        (
            aa_substitute_registry.index_to_value(sub),
            aa_substitute_registry.get_count_for_index(sub)
            / aa_combination_registry.total,
        )
        for sub in good_subs
    ]
    res_subs.sort(key=lambda item: item[1], reverse=True)
    res_combi: list[tuple[set[str], float]] = [
        (
            {aa_substitute_registry.index_to_value(sub) for sub in combi},
            count / aa_combination_registry.total,
        )
        for combi, count in good_combi.most_common()
    ]

    return res_subs, res_combi
