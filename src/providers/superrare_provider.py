from src.providers.base_provider import BaseProvider
import pandas as pd
from ast import literal_eval

class SuperrareProvider(BaseProvider):
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.df["urls"] = self.df["urls"].apply(literal_eval)

    def get_nft_by_url(self, url):
        nfts = self.df[self.df["urls"].apply(lambda x: url in x)]
        
        if len(nfts) == 0:
            return None

        return nfts.iloc[0]

    def get_users(self):
        owners_df = self.df[["owner_username", "owner_eth_address"]].rename(columns = {'owner_username': 'username', 'owner_eth_address': 'eth_address'})
        creators_df = self.df[["creator_username", "creator_eth_address"]].rename(columns = {'creator_username': 'username', 'creator_eth_address': 'eth_address'})

        users_df = pd.concat([owners_df, creators_df]).drop_duplicates().reset_index(drop=True)

        return users_df
