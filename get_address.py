from web3 import Web3
import os

ETHEREUM_NODE = os.getenv('ETHEREUM_NODE')
INFURA_MAX_HISTORY = 120
DAI_ADDRESS = '0x6b175474e89094c44da98b954eedeac495271d0f'

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(ETHEREUM_NODE))

def run():
    number = web3.eth.block_number
    from_block = number - INFURA_MAX_HISTORY

    topics = ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef']

    logs = web3.eth.get_logs({
        'fromBlock': from_block,
        'address': DAI_ADDRESS,
        'topics': topics
    })

    max_log = max(logs, key=lambda log: Web3.to_int(hexstr=log['data']))

    destination = max_log['topics'][2].hex()[-40:]
    print(f"0x{destination}")

if __name__ == "__main__":
    run()
