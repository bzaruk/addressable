Addressable
==============================

# Pulling and Parsing the data
==============================

## Ethereum
Using Dune Analytics to pull out the transactions data for the following contracts for the relevant methods (Sold, AcceptBid, AcceptOffer, ...):
```
0x41a322b28d0ff354040e2cbc676f0320d8c8850d - SuperRare Token - superrare."SuperRare_evt_*"
0x8c9f364bf7a56ed058fc63ef81c6cf09c833e656 - SuperRare: Auction House
0x2947F98C42597966a0ec25e92843c09ac17Fbaa7 - `no-name contract` - superrare."SuperRareMarketAuction_evt_*"
0x65b49f7aee40347f5a90b714be4ef086f3fe5e2c - SuperRare: Marketplace
0x6D7c44773C52D396F43c2D511B81aa168E9a7a42 - SuperRareBazaar - superrare."SuperRareBazaar_evt_*"
```

Manually took the JSON response from the Network tab and saved it as a JSON file in the [`data/raw`](data/raw) directory
(Note: We can do it automatic instead of manual with a request that pulls the data)

the parsed data will include - `block_time, buyer, marketplace_contract_address, nft_contract_address, seller, token_id, tx_hash`
save the parsed data into [`data/processed`](data/processed)

Output for example - [`superrare_txs_info.csv`](data/processed/superrare_txs_info.csv)

## Twitter
Using the [Twitter Service third party](src/third_parties/twtr_service.py) we will pull all the tweets for a list of provided queries (e.g.: [`superrare_search_tweets_1.json`](config/superrare_search_tweets_1.json)).
The Twitter Service third party module will use the `Advanced Search` functionality of the website's API (the official developer API is restricted to the number of requests that can be made).

Output for example - [`superrare_tweets_search.csv`](data/processed/superrare_tweets_search.csv)

## NFT Service Provider
For pulling data out of an NFT Service Provider (e.g.: SuperRare) - we will create a new Extractor class implementing the [BaseExtractor interface](src/extractors/base_extractor.py) (e.g.: [`superrare_extractor.py`](src/extractors/superrare_extractor.py)).
The extractor will use the transactions and tweets data that were pulled before to pull the relevant NFTs data

Output for example - [`superrare_nft_info.csv`](data/processed/superrare_nft_info.csv)


# Providers
==============================
Provider is a class that implement a [BaseProvider interface](src/providers/base_provider.py) and exports API to query an NFT Service Provider loaded data (e.g.: [`superrare_provider.py`](src/providers/superrare_provider.py))


# Methods
==============================
Methods are the logics of matching between Twitter accounts and Ethereum wallets addresses using a provided transactions, tweets, NFT provider instance and an additional method-specific configurable parameters
Any method is going to implement the [BaseMethod interface](src/methods/base_method.py).

Methods for example:
1. [BotMethod](src/methods/bot_method.py) - parsing all the tweets of a specific bot account that tweets about NFT transacations.
2. [UsernameMethod](src/methods/username_method.py) - match between Twitter accounts' usernames and the NFT Service Provider's (e.g.: SuperRare) usernames


# Data Analysis
==============================
Using the pulled and parsed data and the Methods that we created we can match between Twitter accounts and their Ethereum's wallet address.
The matching process uses a config file that mentions all the relevant data frame files (transactions, tweets, and NFTs) and the Methods to use with their special params (e.g.: [`superrare_matching_analysis.json`](configs/superrare_matching_analysis.json)).

Analysis for example - [`superrare_wallets_twitter_match.ipynb`](notebooks/superrare_wallets_twitter_match.ipynb)