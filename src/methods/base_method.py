from src.providers.base_provider import BaseProvider

class BaseMethod:
    def __init__(self, eth_df, tweets_df, provider: BaseProvider, **kwargs):
        self.eth_df = eth_df
        self.tweets_df = tweets_df
        self.provider = provider

    def match(self):
        pass