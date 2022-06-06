import time
from src.extractors.base_extractor import BaseExtractor
import requests
import json
import pandas as pd
import concurrent.futures


class SuperrareExtractor(BaseExtractor):
    def __normalize_nft_obj(self, nft):
        # there are some cases where there is no tokenId and no alternative key
        # in those cases we skip that nft
        if "tokenId" not in nft:
            return None

        x = {
            "tokenId": nft["tokenId"],
            "contract_address": nft["contractAddress"],
            "name": nft["name"],
            "creator_username": nft["creator"]["username"]
            if nft["creator"]
            else None,
            "creator_eth_address": nft["creator"]["ethereumAddress"]
            if nft["creator"]
            else nft["creatorAddress"]
            if nft["creatorAddress"]
            else None,
            "owner_username": nft["owner"]["username"] if nft["owner"] else None,
            "owner_eth_address": nft["owner"]["ethereumAddress"]
            if nft["owner"]
            else nft["ownerAddress"]
            if nft["ownerAddress"]
            else None,
            "urls": [
                f"superrare.co/artwork-v2/{'-'.join(nft['name'].lower().split())}-{nft['tokenId']}",
                f"superrare.com/artwork-v2/{'-'.join(nft['name'].lower().split())}-{nft['tokenId']}",
            ],
        }

        return x

    def __get_user_collection(
        self,
        user_eth_address,
        contract_addresses,
        marketplace_contract_addresses,
        retry_num=0,
    ):
        """pulling the NFTs data from the GET-collection API
        of a provided user ethereum address"""
        MAX_OF_RETIES = 100
        nfts = []

        url = "https://superrare.com/api/v2/profile/collection"
        headers = {
            "content-type": "application/json;charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36",
        }
        body = json.dumps(
            {
                "contractAddresses": contract_addresses,
                "userAddress": user_eth_address,
                "auctionHouseContractAddresses": marketplace_contract_addresses,
                # for now I put 500 as a really bug number to cover all the NFTs of a user
                # but we need to paginate through all the NFTs of that user
                "first": 500,
            }
        )

        r = requests.post(url, body, headers=headers)
        try:
            resp = r.json()
        except:
            # if we fail with a specific request we are going to 
            # sleep from 5 seconds and try again, unless we reached 
            # the max amount of tries and then we'll return an empty DataFrame
            if retry_num >= MAX_OF_RETIES:
                return pd.DataFrame(nfts)
            time.sleep(5)
            return self.__get_user_collection(
                user_eth_address,
                contract_addresses,
                marketplace_contract_addresses,
                retry_num=retry_num + 1,
            )

        if resp["status"] == "SUCCESS":
            nfts_res = resp["result"]["nfts"]
            nfts = [self.__normalize_nft_obj(n) for n in nfts_res]
            # clear None values
            nfts = [i for i in nfts if i]

        df = pd.DataFrame(nfts)

        return df

    def __get_user_creations(
        self,
        user_eth_address,
        contract_addresses,
        marketplace_contract_addresses,
        retry_num=0,
    ):
        """pulling the NFTs data from the GET-creations API
        of a provided user ethereum address"""
        MAX_OF_RETIES = 100
        nfts = []

        url = "https://superrare.com/api/v2/profile/creations"
        headers = {
            "content-type": "application/json;charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36",
        }
        body = json.dumps(
            {
                "contractAddresses": contract_addresses,
                "userAddress": user_eth_address,
                "auctionHouseContractAddresses": marketplace_contract_addresses,
            }
        )

        r = requests.post(url, body, headers=headers)
        try:
            resp = r.json()
        except:
            # if we fail with a specific request we are going to 
            # sleep from 5 seconds and try again, unless we reached 
            # the max amount of tries and then we'll return an empty DataFrame
            if retry_num >= MAX_OF_RETIES:
                return pd.DataFrame(nfts)
            time.sleep(5)
            return self.__get_user_creations(
                user_eth_address,
                contract_addresses,
                marketplace_contract_addresses,
                retry_num=retry_num + 1,
            )

        if resp["status"] == "SUCCESS":
            nfts_res = resp["result"]["nfts"]
            nfts = [self.__normalize_nft_obj(n) for n in nfts_res]
            # clear None values
            nfts = [i for i in nfts if i]

        df = pd.DataFrame(nfts)

        return df

    def __get_user_collection_and_creations(
        self,
        user_eth_address,
        contract_addresses,
        marketplace_contract_addresses,
    ):
        """pulling the NFTs data from the GET-creations and GET-collection APIs
        of a provided user ethereum address"""

        creations = self.__get_user_creations(
            user_eth_address, contract_addresses, marketplace_contract_addresses
        )
        collection = self.__get_user_collection(
            user_eth_address, contract_addresses, marketplace_contract_addresses
        )

        return pd.concat([creations, collection])

    def extract(self, txs=None):
        """extracting SuperRare's NFTs data using a provided txs DataFrame"""

        # we will use two of the GET-profile APIs to pull the wanted data
        # so here we are building a user-unique list out of the buyers and sellers list
        user_eth_addresses = pd.concat([txs["buyer"], txs["seller"]]).unique()
        contract_addresses = txs["nft_contract_address"].unique().tolist()
        marketplace_contract_addresses = (
            txs["marketplace_contract_address"].unique().tolist()
        )

        nfts_df = pd.DataFrame()
        # extract the data with 30 threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            args = [
                [u, contract_addresses, marketplace_contract_addresses]
                for u in user_eth_addresses
            ]
            for result in executor.map(
                lambda p: self.__get_user_collection_and_creations(*p), args
            ):
                nfts_df = pd.concat([nfts_df, result])

        nfts_df.reset_index(drop=True)

        return nfts_df
