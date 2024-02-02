from pathlib import Path

import matplotlib.pyplot as plt


def plot(
    subs_freq: list[tuple[str, float]],
    combi_freq: list[tuple[set[str], float]],
    output_file: Path,
    fig_size: tuple[int, int],
    top_font_size: int,
) -> None:
    n_subs = len(subs_freq)
    n_combi = len(combi_freq)

    sub_to_index: dict[str, int] = {sub: i for i, (sub, _) in enumerate(subs_freq)}

    fig, ax = plt.subplots(
        2,
        2,
        figsize=fig_size,
        sharex="col",
        sharey="row",
        gridspec_kw={"height_ratios": [1, 2], "width_ratios": [1, 2]},
    )

    ax[0, 0].axis("off")

    axes_dots = ax[1, 1]
    axes_combis = ax[0, 1]
    axes_subs = ax[1, 0]

    # Gray dots
    scatter_points = [(i, j) for i in range(n_combi) for j in range(n_subs)]
    x = [x for x, _ in scatter_points]
    y = [y for _, y in scatter_points]
    axes_dots.scatter(x, y, c="#cfcfcf")

    # Connecting lines
    for i, (combi, _) in enumerate(combi_freq):
        y = sorted([sub_to_index[sub] for sub in combi])
        x = [i] * len(y)
        axes_dots.plot(x, y, "ko-")

    axes_dots.axis("off")

    # Combinations bars on top
    x = range(n_combi)
    y = [freq for _, freq in combi_freq]
    s = axes_combis.bar(x, y, color="b")
    for p in s.patches:
        axes_combis.text(
            p.get_x() + p.get_width() / 2,
            p.get_height() + 0.005,
            f"{p.get_height():.1%}",
            ha="center",
            va="bottom",
            size=top_font_size,
        )
    axes_combis.spines["right"].set_visible(False)
    axes_combis.spines["top"].set_visible(False)
    axes_combis.get_xaxis().set_visible(False)

    # Substitutions bars on left
    x = [-freq for _, freq in subs_freq]
    y = range(n_subs)
    labels = [sub for sub, _ in subs_freq]
    s = axes_subs.barh(y, x, color="r")
    for i, p in enumerate(s.patches):
        freq = subs_freq[i][1]
        axes_subs.text(
            p.get_x() + p.get_width() - 0.01,
            p.get_height() / 2 + p.get_y(),
            f"{freq:.02%}",
            ha="right",
            va="center",
            size=top_font_size,
        )
    axes_subs.yaxis.set_ticks_position("right")
    axes_subs.set_yticks(y)
    axes_subs.set_yticklabels(labels)
    xtick_pos = axes_subs.get_xticks()
    axes_subs.set_xticks(xtick_pos)
    axes_subs.set_xticklabels([f"{abs(x):.0%}" for x in xtick_pos])
    axes_subs.set_xlim((-1, 0))
    axes_subs.tick_params(axis="y", which="both", length=0)
    # axes_subs.spines["right"].set_visible(False)
    axes_subs.spines["top"].set_visible(False)
    axes_subs.spines["left"].set_visible(False)

    fig.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight", facecolor="white")
