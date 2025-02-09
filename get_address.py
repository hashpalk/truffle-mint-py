from web3 import Web3
import os
import logging
from decimal import Decimal
import json
import time

# Environment Variables
ETHEREUM_NODE = os.getenv("ETHEREUM_NODE")
INFURA_MAX_HISTORY = 120
DAI_ADDRESS = "0x6b175474e89094c44da98b954eedeac495271d0f"
DAI_DECIMALS = 18

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(ETHEREUM_NODE))

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def format_dai_amount(amount_wei):
    """Convert DAI amount from wei to human-readable format"""
    amount_decimal = Decimal(amount_wei) / Decimal(10**DAI_DECIMALS)
    return f"{amount_decimal:,.2f} DAI"

def get_address_details(address):
    """Get basic details about an address"""
    is_contract = web3.eth.get_code(address).hex() != "0x"
    balance_wei = web3.eth.get_balance(address)
    balance_eth = web3.from_wei(balance_wei, "ether")
    return {"is_contract": is_contract, "eth_balance": balance_eth, "address": address}

def get_transaction_details(tx_hash):
    """Fetch transaction details including gas price and fees"""
    tx = web3.eth.get_transaction(tx_hash)
    receipt = web3.eth.get_transaction_receipt(tx_hash)
    gas_price = web3.from_wei(tx["gasPrice"], "gwei")
    gas_used = receipt["gasUsed"]
    gas_fee = web3.from_wei(gas_price * gas_used, "ether")
    return {"gas_price": gas_price, "gas_fee": gas_fee}

def save_to_json(data, filename="dai_transfers.json"):
    """Save transfer details to a JSON file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    logging.info(f"Data saved to {filename}")

def run():
    try:
        latest_block = web3.eth.block_number
        from_block = max(0, latest_block - INFURA_MAX_HISTORY)
        
        print(f"Current block: {latest_block}")
        user_block_range = input(f"Enter block range (max {INFURA_MAX_HISTORY} blocks, press enter to use default): ")
        if user_block_range.isdigit():
            from_block = max(0, latest_block - int(user_block_range))
        
        topics = ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]
        logs = web3.eth.get_logs({"fromBlock": from_block, "address": DAI_ADDRESS, "topics": topics})
        
        if not logs:
            logging.info("No DAI transfers found in the specified block range")
            return
        
        sorted_logs = sorted(logs, key=lambda log: Web3.to_int(hexstr=log["data"]), reverse=True)[:5]
        transfer_data = []
        
        for idx, log in enumerate(sorted_logs, start=1):
            amount = Web3.to_int(hexstr=log["data"])
            from_address = f"0x{log['topics'][1].hex()[-40:]}"
            to_address = f"0x{log['topics'][2].hex()[-40:]}"
            block = web3.eth.get_block(log["blockNumber"])
            tx_details = get_transaction_details(log["transactionHash"].hex())
            
            transfer_info = {
                "rank": idx,
                "amount": format_dai_amount(amount),
                "from": from_address,
                "to": to_address,
                "block": log["blockNumber"],
                "timestamp": block["timestamp"],
                "gas_price": f"{tx_details['gas_price']} Gwei",
                "gas_fee": f"{tx_details['gas_fee']} ETH"
            }
            transfer_data.append(transfer_info)
            
            print(f"\nTop {idx} Largest DAI Transfer:")
            print(f"Amount: {format_dai_amount(amount)}")
            print(f"From: {from_address}")
            print(f"To: {to_address}")
            print(f"Block: {log['blockNumber']}")
            print(f"Timestamp: {block['timestamp']}")
            print(f"Gas Price: {tx_details['gas_price']} Gwei")
            print(f"Gas Fee: {tx_details['gas_fee']} ETH")
            
        save_to_json(transfer_data)
    
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    while True:
        run()
        print("Waiting for the next scan...")
        time.sleep(60)
