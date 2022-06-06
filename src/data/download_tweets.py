# -*- coding: utf-8 -*-
import click
import logging
import json
import pandas as pd
import os
from dotenv import load_dotenv, find_dotenv
from src.third_parties.twtr_service import TWTRService


def normalize_tweet(t):
    """flattening and picking only the relevant data for us"""

    return {
        "text": " ".join(t["full_text"].split()),
        "tweet_id": t["id_str"],
        "created_at": t["created_at"],
        "user_id": t["user_id_str"],
        "urls": [u["expanded_url"] for u in t["entities"]["urls"]],
        "mentions_user_names": [
            u["screen_name"] for u in t["entities"]["user_mentions"]
        ],
        "mentions_user_ids": [u["id_str"] for u in t["entities"]["user_mentions"]],
        "hashtags": [u["text"] for u in t["entities"]["hashtags"]],
    }


def add_user_data_to_tweets(tweets, users_data):
    """joining to user data to the tweets data"""

    for t in tweets:
        u = users_data[t["user_id"]]

        t["user_username"] = u["username"]
        t["user_name"] = u["name"]
        t["user_profile_image_url"] = u["profile_image_url"]


@click.group()
@click.pass_context
def cli(ctx):
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    api_bearer_token = os.environ.get("TWTR_API_BEARER_TOKEN")
    session_bearer_token = os.environ.get("TWTR_SESSION_BEARER_TOKEN")
    session_auth_token = (os.environ.get("TWTR_SESSION_AUTH_TOKEN"),)
    session_csrf_token = (os.environ.get("TWTR_SESSION_CSRF_TOKEN"),)

    ctx.obj["twtr_client"] = TWTRService(
        api_bearer_token,
        session_bearer_token,
        session_auth_token[0],
        session_csrf_token[0],
    )


@cli.command()
@click.argument("search_config_file", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
@click.pass_context
def main(
    ctx,
    search_config_file,
    output_filepath,
):
    """
    download tweets for a provided query
    and save to a csv file
    """
    logger = logging.getLogger(__name__)

    twtr_client = ctx.obj["twtr_client"]

    # config file is an array of { query: string, fromDate: string (YYYY-MM-DD), toDate: string (YYYY-MM-DD) }
    search_conf_file = open(search_config_file)
    search_conf = json.load(search_conf_file)

    tweets = []
    for q in search_conf:
        query = q["query"]
        from_date = q["fromDate"]
        to_date = q["toDate"]

        logger.info("downloading tweets for query: %s, from date: %s, to date: %s", q, from_date, to_date)
        query_results_tweets = twtr_client.search_tweets(query, from_date, to_date)

        tweets.extend(query_results_tweets)

    tweets = [normalize_tweet(t) for t in tweets]

    df = pd.DataFrame(tweets)

    logger.info("pulling the users data of %d tweets", len(df))
    user_ids_distinct = df["user_id"].unique().tolist()
    users_data = twtr_client.get_users(user_ids_distinct)
    add_user_data_to_tweets(tweets, users_data)

    df = pd.DataFrame(tweets)

    logger.info("save %d tweets to %s", len(df), output_filepath)
    df.to_csv(output_filepath, index=False)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    load_dotenv(find_dotenv())

    cli(obj={})
