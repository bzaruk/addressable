from src.methods.base_method import BaseMethod
import re
import pandas as pd

class BotMethod(BaseMethod):
    def __init__(self, eth_df, tweets_df, provider, **kwargs):
        super().__init__(eth_df, tweets_df, provider)
        self.artist_pattern = kwargs["artist_pattern"]
        self.owner_pattern = kwargs["owner_pattern"]
        self.bot_tweets = self.tweets_df[self.tweets_df["user_username"] == kwargs["bot_username"]]

    def __get_artist_by_tweet(self, tweet):
        """ pulling out the artist of the NFT out of the tweet using regex """
        m = re.search(self.artist_pattern, tweet)
        return m.group(1) if m else None

    def __get_owner_by_tweet(self, tweet):
        """ pulling out the owner of the NFT out of the tweet using regex """
        m = re.search(self.owner_pattern, tweet)
        return m.group(1) if m else None

    def match(self):
        df = pd.DataFrame(columns = ["username", "eth_address"])

        for index, row in self.bot_tweets.iterrows():
            artist = self.__get_artist_by_tweet(row["text"])
            owner = self.__get_owner_by_tweet(row["text"])

            # if we don't have both artist and owner we continue to the next tweet
            if artist is None and owner is None:
                continue

            # normalize the tweet URL to the way the provider saves URLs
            url = row["urls"][0].replace("https://", "").replace("http://", "").lower()
            res = self.provider.get_nft_by_url(url)

            # if no NFT data for that URL - continue
            if res is None:
                continue

            if artist:
                new_row = {
                    "username": artist,
                    "eth_address": res["creator_eth_address"]
                }
                new_row = pd.DataFrame(new_row, index=[0])

                df = pd.concat([df, new_row])
            
            if owner:
                new_row = {
                    "username": owner,
                    "eth_address": res["owner_eth_address"]
                }
                new_row = pd.DataFrame(new_row, index=[0])

                df = pd.concat([df, new_row])

        return df.reset_index(drop=True)

                
