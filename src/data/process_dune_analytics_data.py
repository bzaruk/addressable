# -*- coding: utf-8 -*-
import click
import logging
import json
import pandas as pd

def fix_hash_columns(df):
    """
    turns dune analytics hash value that starts with `\\x` to start with `0x`
    """
    for column in df:
        col_first_value = df[column].values[0]
        if isinstance(col_first_value, str) and col_first_value.startswith("\\x"):
            df[column] = df.apply(lambda x: x[column].replace('\\', '0'), axis=1)

@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
def main(input_filepath, output_filepath):
    """
    process dune analytics txs data into csv
    """
    logger = logging.getLogger(__name__)

    logger.info("loading txs data from %s", input_filepath)
    dune_analytics_res_file = open(input_filepath)
    dune_analytics_res = json.load(dune_analytics_res_file)

    data = [x["data"] for x in dune_analytics_res["data"]["get_result_by_job_id"]]

    df = pd.DataFrame(data)
    fix_hash_columns(df)

    logger.info("save %d processed txs to %s", len(df), output_filepath)
    df.to_csv(output_filepath, index=False)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
