"""
@date: 01/08/2022
"""

import os
import argparse
import requests
import time
import datetime
import json
import pandas as pd

from honestnft_utils import config, opensea


def get_metadata_from_aggregator(
    contract_address: str, metadata_source: str, collection_name: str = ""
):

    dt_now = datetime.datetime.utcnow()
    start_time = time.time()

    print(f"Working in directory: {os.getcwd()}")

    # Get Collection Slug
    if collection_name == "":
        collection_name = opensea.get_opensea_collection_slug(contract_address)
        print("-----------------------")
        print(collection_name)
        print("-----------------------")
        if collection_name is None:
            print("Error fetching collection name from OpenSea")
            quit()

    url = {
        "nftnerds": f"{config.NFTNERDS_BASE_URL}{contract_address}",
        "alphasharks": f"{config.ALPHASHARKS_BASE_URL}{contract_address}",
    }[metadata_source]

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code == 200:
        response_data = response.json()

        # list to make completeness checks
        token_ids = []

        # Create folder to store metadata
        folder = f"{config.ATTRIBUTES_FOLDER}/{collection_name}/"
        print(f"Saving raw attributes to {folder}")
        if not os.path.exists(folder):
            os.mkdir(folder)

        if metadata_source == "nftnerds":
            metadata = response.json()["traitsDict"]
        elif metadata_source == "alphasharks":
            metadata = response.json()["traitsObj"]

        for token in metadata:
            token_dict = dict()
            token_ids.append(int(token))
            token_dict["tokenId"] = token
            # token_dict["attributes"] = response_data["traitsDict"][token]
            token_dict["attributes"] = metadata[token]
            PATH = f"{config.ATTRIBUTES_FOLDER}/{collection_name}/{token}.json"

            with open(PATH, "w") as destination_file:
                json.dump(token_dict, destination_file)

        print(f"tokens in the list {len(token_ids)}")
        print(f"lower_id: {min(token_ids)}")
        print(f"upper_id: {max(token_ids)}")

        if min(token_ids) == 0:
            max_supply = max(token_ids) + 1
            print(f"max supply: {max(token_ids) + 1}")
        else:
            max_supply = max(token_ids)
            print(f"max supply: {max(token_ids)}")

        # warn if nftNerds doesn't have the full collection
        # TODO: print a list of missing token ids
        if len(token_ids) != max_supply:
            print(f"{max_supply - len(token_ids)} tokens with missing metadata")

        # Run pulling.py to grab missing tokens and create rarity csv
        print(
            f"Creating rarity csv with 'pulling.py' using the command: python3 pulling.py --contract {contract_address} --collection {collection_name}"
        )
        os.system(
            f"python3 pulling.py --contract {contract_address} --collection {collection_name}"
        )

        # Calculate rarity_data csv with rarity.py
        print(
            f"Calculating rarity data with 'rarity.py' using the command: python3 rarity.py --collection {collection_name}"
        )
        os.system(f"python3 rarity.py --collection {collection_name}")

        print(
            "--- %s seconds to process collection"
            % (round(time.time() - start_time, 1))
        )

    elif response.status_code == 403:
        print(
            f"NFT Nerds hasn't published metadata yet. (Error code: {response.status_code})"
        )
    else:
        print(f"Received a {response.status_code} error from the NFT Nerds API")

    print("finished.")


def _cli_parser() -> argparse.ArgumentParser:
    """
    Create the command line argument parser
    """
    parser = argparse.ArgumentParser(
        description="Download NFT metadata from https://nftnerds.ai/"
    )
    parser.add_argument(
        "-c",
        "--contract",
        type=str,
        required=True,
        default=None,
        help="Collection contract address",
    )
    parser.add_argument(
        "-col",
        "--collection",
        type=str,
        default="",
        help="Collection Opensea slug",
    )
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        default="nftnerds",
        help="Available Metadata Aggregators: nftnerds, alphasharks",
    )
    return parser


if __name__ == "__main__":
    # Parse command line arguments

    ARGS = _cli_parser().parse_args()
    print(ARGS)
    get_metadata_from_aggregator(
        contract_address=ARGS.contract,
        collection_name=ARGS.collection,
        metadata_source=ARGS.source,
    )
