import json
import logging
import logging.config
from pathlib import Path

import click

from plot_combinations.calculation import calculate
from plot_combinations.plot import plot

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "short": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "short",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "formatter": "short",
        "level": "INFO",
        "handlers": ["stdout"],
    },
}
logging.config.dictConfig(LOGGING)

logger = logging.getLogger("plot_combinations")


@click.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", "-o", help="Output base filename")
@click.option(
    "--min-sub-freq",
    help="Min substitution frequency",
    type=float,
    default=0.05,
    show_default=True,
)
@click.option("--max-combi-cumfrac", help="Max combination cum fraction", type=float)
@click.option(
    "--min-combi-freq",
    help="Min combination frequency",
    type=float,
    default=0.05,
    show_default=True,
)
@click.option(
    "--max-combi-num",
    help="Max combination number",
    type=int,
    default=20,
    show_default=True,
)
@click.option("--size", help="Fig size", default="20x20", show_default=True)
@click.option("--top-font-size", type=int, default=10, show_default=True)
def run(
    file: Path,
    output: str | None,
    min_sub_freq: float,
    max_combi_cumfrac: float | None,
    min_combi_freq: float,
    max_combi_num: int,
    size: str,
    top_font_size: int,
):
    """Plot combinations of AA substitutions."""

    logger.info("Input file: %s", file)
    output_path = Path(output) if output else file
    log_path = output_path.with_suffix(".log")
    pic_path = output_path.with_suffix(".png")
    data_path = output_path.with_suffix(".json")

    logging.getLogger("aa_combi").addHandler(
        logging.FileHandler(filename=log_path, mode="w")
    )

    with open(file, "r") as fi:
        subs_freq, combi_freq = calculate(
            fi,
            aa_substitute_min_freq=min_sub_freq,
            aa_combination_max_cumfrac=max_combi_cumfrac,
            aa_combination_max_num=max_combi_num,
            aa_combination_min_freq=min_combi_freq,
        )

    x, y, *_ = size.split("x")
    fig_size = (int(x), int(y))
    plot(
        subs_freq=subs_freq,
        combi_freq=combi_freq,
        output_file=pic_path,
        fig_size=fig_size,
        top_font_size=top_font_size,
    )

    save_data(subs_freq, combi_freq, data_path)

    logger.info("Picture: %s", pic_path)
    logger.info("Data: %s", data_path)
    logger.info("Log: %s", log_path)


def save_data(
    subs_freq: list[tuple[str, float]],
    combi_freq: list[tuple[set[str], float]],
    output_file: Path,
) -> None:
    data = {
        "subs": [{"sub": sub, "freq": freq} for sub, freq in subs_freq],
        "combi": [{"subs": list(subs), "freq": freq} for subs, freq in combi_freq],
    }
    with open(output_file, "w") as fo:
        json.dump(data, fo, indent=2)


if __name__ == "__main__":
    run()
