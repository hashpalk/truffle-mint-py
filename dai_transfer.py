from web3 import Web3
import os
from eth_typing import HexStr
from decimal import Decimal

# Get Ethereum node URL from environment variables
ETHEREUM_NODE = os.getenv("ETHEREUM_NODE")

INFURA_MAX_HISTORY = 120
DAI_ADDRESS = "0x6b175474e89094c44da98b954eedeac495271d0f"

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(ETHEREUM_NODE))


async def run():
    # Get current block number
    number = await web3.eth.block_number
    from_block = number - INFURA_MAX_HISTORY

    # Topic for Transfer(address,address,uint256)
    topics = [
        HexStr("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef")
    ]

    # Get past transfer events
    logs = await web3.eth.get_logs(
        {"fromBlock": from_block, "address": DAI_ADDRESS, "topics": topics}
    )

    # Find transfer with maximum value
    max_transfer = max(logs, key=lambda x: int(x["data"], 16))

    # Extract destination address from topics
    destination = max_transfer["topics"][2][-40:]
    print(f"0x{destination}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
