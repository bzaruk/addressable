from datetime import datetime
import requests
import tweepy
import time


class TWTRService:
    def __init__(
        self,
        api_bearer_token,
        session_bearer_token,
        session_auth_token,
        session_csrf_token,
    ):
        self.session_bearer_token = session_bearer_token
        self.session_auth_token = session_auth_token
        self.session_csrf_token = session_csrf_token
        self.client = tweepy.Client(api_bearer_token)

    def __get_next_page_cursor(self, resp):
        """getting the next page id for a continous request with pagination"""
        entries = []

        for x in resp["timeline"]["instructions"]:
            if "addEntries" in x:
                entries.extend(x["addEntries"]["entries"])
            elif "replaceEntry" in x:
                entries.append(x["replaceEntry"]["entry"])

        next_cursor = None
        for e in entries:
            if e["entryId"] == "cursor-bottom-0":
                next_cursor = e["content"]["operation"]["cursor"]["value"]

        return next_cursor

    def __filter_unrelevant_tweets(self, tweets):
        """
        1. "card" key in tweet means it is an advertisement tweet
        2. we don't want to take quoted tweets in consideration (for now)
        """

        queted_tweet_ids = [
            t["quoted_status_id_str"] for t in tweets.values() if t["is_quote_status"]
        ]
        filtered_tweets = {
            t_id: t
            for t_id, t in tweets.items()
            if "card" not in t and t_id not in queted_tweet_ids
        }

        return filtered_tweets

    def __search_tweets_page(self, query, page=None):
        headers = {
            "authorization": f"Bearer {self.session_bearer_token}",
            "x-csrf-token": self.session_csrf_token,
        }
        cookies = {
            "auth_token": self.session_auth_token,
            "ct0": self.session_csrf_token,
        }
        search_url = f"https://twitter.com/i/api/2/search/adaptive.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&include_ext_has_nft_avatar=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_quote_count=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&include_ext_media_availability=true&include_ext_sensitive_media_warning=true&include_ext_trusted_friends_metadata=true&include_ext_vibe_tag=true&send_error_codes=true&simple_quoted_tweet=true&q={requests.utils.quote(query)}&count=20000&query_source=typed_query&pc=1&spelling_corrections=1&ext=mediaStats%2ChighlightedLabel%2ChasNftAvatar%2CvoiceInfo%2Cenrichments%2CsuperFollowMetadata%2CunmentionInfo"

        if page:
            search_url = f"{search_url}&cursor={page}"

        r = requests.get(search_url, headers=headers, cookies=cookies)
        resp = r.json()

        if "errors" in resp and len(resp["errors"]) > 0:
            print(f"{resp['errors'][0]['code']}")
            raise Exception(resp["errors"][0]["code"])

        tweets = resp["globalObjects"]["tweets"]
        filtered_tweets = self.__filter_unrelevant_tweets(tweets)
        tweets = list(filtered_tweets.values())

        next = self.__get_next_page_cursor(resp)

        return {"tweets": tweets, "next": next}

    def __create_full_query(self, query, from_date, to_date):
        """building a real query out of the query, from_date and to_date params"""
        return f"{query} until:{to_date} since:{from_date}"

    def __inner_search_tweets(self, query, from_date, to_date, retry_num=0):
        # when reaching the max amount of tries we'll return an empty array
        MAX_OF_RETIES = 100
        if retry_num >= MAX_OF_RETIES:
            return []

        # building a real query out of the query, from_date and to_date params
        full_query = self.__create_full_query(query, from_date, to_date)

        try:
            search_result = self.__search_tweets_page(full_query)
        except:
            # if we fail with a specific request we are going to
            # sleep from 5 seconds and try again
            time.sleep(5)
            return self.__inner_search_tweets(
                query, from_date, to_date, retry_num=retry_num + 1
            )

        tweets = search_result["tweets"]

        # if the first search didn't provide any results
        # it means that there are no result to that query
        # (in the next following execution no results doesn't mean that there are no results left -
        # it can also mean that we reach to the max results that can be provided for that query -
        # so we generate another one)
        if len(tweets) == 0:
            return []

        num_of_tries = 0
        while len(search_result["tweets"]) > 0 or (
            num_of_tries > 0 and num_of_tries < MAX_OF_RETIES
        ):
            try:
                search_result = self.__search_tweets_page(
                    full_query, search_result["next"]
                )
                tweets.extend(search_result["tweets"])
                print(f"len of tweets -> {len(tweets)}")

                num_of_tries = 0
            except:
                # if we fail with a specific request we are going to
                # sleep from 5 seconds and try again
                time.sleep(5)
                num_of_tries = num_of_tries + 1

        for t in tweets:
            t["created_at"] = datetime.strptime(
                t["created_at"], "%a %b %d %H:%M:%S %z %Y"
            )

        # in cases with reached the max capacity of results out of a query
        # here we genreating a new search query by shortening the range of search
        tweets.sort(key=lambda x: x["created_at"])
        oldest_tweet_date = tweets[0]["created_at"].strftime("%Y-%m-%d")
        tweets.extend(self.__inner_search_tweets(query, from_date, oldest_tweet_date))

        return tweets

    def search_tweets(self, query, from_date, to_date):
        tweets = self.__inner_search_tweets(query, from_date, to_date)
        tweets.sort(key=lambda x: x["created_at"])

        return tweets

    def get_users(self, ids):
        """getting the extended users data for a provided IDs of users"""

        users_data = {}

        # as API restricted to 100 users per call
        groups_of_100 = [ids[i : i + 100] for i in range(0, len(ids), 100)]

        for chunk in groups_of_100:
            res = self.client.get_users(ids=chunk, user_fields="profile_image_url")

            for u in res.data:
                users_data[str(u.id)] = {
                    "id": u.id,
                    "name": u.name,
                    "username": u.username,
                    "profile_image_url": u.profile_image_url,
                }

        return users_data
