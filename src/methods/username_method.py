from src.methods.base_method import BaseMethod
from src.providers.base_provider import BaseProvider

class UsernameMethod(BaseMethod):
    def __init__(self, eth_df, tweets_df, provider: BaseProvider):
        super().__init__(eth_df, tweets_df, provider)

    def match(self):
        provider_usernames = self.provider.get_users()
        twitter_usernames = self.tweets_df["user_username"].unique()

        return provider_usernames[provider_usernames["username"].isin(twitter_usernames)].reset_index(drop=True)