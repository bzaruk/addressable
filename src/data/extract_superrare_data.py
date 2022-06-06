# -*- coding: utf-8 -*-
import click
import logging
import pandas as pd
from src.extractors.superrare_extractor import SuperrareExtractor


@click.command()
@click.argument("txs_file", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
def main(
    txs_file,
    output_filepath,
):
    """
    extract SuperRare NFTs data from the txs data
    """
    logger = logging.getLogger(__name__)
    df = pd.read_csv(txs_file)

    extractor = SuperrareExtractor()
    logger.info("extracting SuperRare's NFTs data for %d txs", len(df))
    logger.info("txs source file: %s", txs_file)
    nfts_df = extractor.extract(txs=df)

    nfts_df.to_csv(output_filepath, index=False)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
