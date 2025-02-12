from web3 import Web3
import os
from decimal import Decimal

ETHEREUM_NODE = os.getenv("ETHEREUM_NODE")
INFURA_MAX_HISTORY = 120
DAI_ADDRESS = "0x6b175474e89094c44da98b954eedeac495271d0f"
DAI_DECIMALS = 18

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(ETHEREUM_NODE))


def format_dai_amount(amount_wei):
    """Convert DAI amount from wei to human readable format"""
    amount_decimal = Decimal(amount_wei) / Decimal(10**DAI_DECIMALS)
    return f"{amount_decimal:,.2f} DAI"


def get_address_details(address):
    """Get basic details about an address"""
    is_contract = web3.eth.get_code(address).hex() != "0x"
    balance_wei = web3.eth.get_balance(address)
    balance_eth = web3.from_wei(balance_wei, "ether")
    return {"is_contract": is_contract, "eth_balance": balance_eth, "address": address}


def get_gas_price():
    """Fetch current gas price in Gwei"""
    gas_price_wei = web3.eth.gas_price
    gas_price_gwei = web3.from_wei(gas_price_wei, "gwei")
    return gas_price_gwei


def get_transaction_details(tx_hash):
    """Fetch transaction details by hash"""
    try:
        tx = web3.eth.get_transaction(tx_hash)
        receipt = web3.eth.get_transaction_receipt(tx_hash)
        return {
            "from": tx["from"],
            "to": tx["to"],
            "value": web3.from_wei(tx["value"], "ether"),
            "gas_used": receipt["gasUsed"],
            "gas_price": web3.from_wei(tx["gasPrice"], "gwei"),
            "status": "Success" if receipt["status"] == 1 else "Failed",
        }
    except Exception as e:
        return {"error": str(e)}


def get_transfer_stats(from_block, to_block=None):
    """Get statistics about DAI transfers in a block range"""
    if to_block is None:
        to_block = web3.eth.block_number

    topics = ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]

    try:
        logs = web3.eth.get_logs(
            {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": DAI_ADDRESS,
                "topics": topics,
            }
        )

        transfers = []
        for log in logs:
            amount = Web3.to_int(hexstr=log["data"])
            transfers.append(
                {
                    "from": f"0x{log['topics'][1].hex()[-40:]}",
                    "to": f"0x{log['topics'][2].hex()[-40:]}",
                    "amount": amount,
                    "block": log["blockNumber"],
                }
            )

        total_volume = sum(t["amount"] for t in transfers)
        unique_senders = len(set(t["from"] for t in transfers))
        unique_receivers = len(set(t["to"] for t in transfers))

        return {
            "total_transfers": len(transfers),
            "total_volume": format_dai_amount(total_volume),
            "unique_senders": unique_senders,
            "unique_receivers": unique_receivers,
            "avg_transfer": (
                format_dai_amount(total_volume // len(transfers))
                if transfers
                else "0 DAI"
            ),
        }

    except Exception as e:
        return {"error": str(e)}


def check_suspicious_activity(address, blocks_to_check=1000):
    """Check for suspicious DAI transfer patterns for an address"""
    current_block = web3.eth.block_number
    from_block = current_block - blocks_to_check

    topics = ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]
    address_topic = "0x" + "0" * 24 + address[2:]

    try:
        # Get transfers from the address
        sent_logs = web3.eth.get_logs(
            {
                "fromBlock": from_block,
                "address": DAI_ADDRESS,
                "topics": [topics[0], address_topic],
            }
        )

        # Get transfers to the address
        received_logs = web3.eth.get_logs(
            {
                "fromBlock": from_block,
                "address": DAI_ADDRESS,
                "topics": [topics[0], None, address_topic],
            }
        )

        # Analyze patterns
        sent_amounts = [Web3.to_int(hexstr=log["data"]) for log in sent_logs]
        received_amounts = [Web3.to_int(hexstr=log["data"]) for log in received_logs]

        results = {
            "total_sent": (
                format_dai_amount(sum(sent_amounts)) if sent_amounts else "0 DAI"
            ),
            "total_received": (
                format_dai_amount(sum(received_amounts))
                if received_amounts
                else "0 DAI"
            ),
            "num_transactions": len(sent_logs) + len(received_logs),
            "suspicious_patterns": [],
        }

        # Check for potential suspicious patterns
        if len(sent_logs) > 50 and len(set(log["topics"][2] for log in sent_logs)) == 1:
            results["suspicious_patterns"].append("Multiple transfers to same address")

        if (
            len(received_logs) > 50
            and len(set(log["topics"][1] for log in received_logs)) == 1
        ):
            results["suspicious_patterns"].append(
                "Multiple transfers from same address"
            )

        return results

    except Exception as e:
        return {"error": str(e)}


def run():
    number = web3.eth.block_number
    from_block = number - INFURA_MAX_HISTORY
    topics = ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]

    try:
        logs = web3.eth.get_logs(
            {"fromBlock": from_block, "address": DAI_ADDRESS, "topics": topics}
        )
        if not logs:
            print("No DAI transfers found in the specified block range")
            return

        max_log = max(logs, key=lambda log: Web3.to_int(hexstr=log["data"]))
        amount = Web3.to_int(hexstr=max_log["data"])
        from_address = f"0x{max_log['topics'][1].hex()[-40:]}"
        to_address = f"0x{max_log['topics'][2].hex()[-40:]}"
        block = web3.eth.get_block(max_log["blockNumber"])

        print("\nLargest DAI Transfer Details:")
        print(f"Amount: {format_dai_amount(amount)}")
        print(f"From: {from_address}")
        print(f"To: {to_address}")
        print(f"Block: {max_log['blockNumber']}")
        print(f"Timestamp: {block['timestamp']}")

        recipient_details = get_address_details(to_address)
        print("\nRecipient Details:")
        print(
            f"Address Type: {'Contract' if recipient_details['is_contract'] else 'EOA'}"
        )
        print(f"ETH Balance: {recipient_details['eth_balance']:.4f} ETH")

        # Fetch gas price
        gas_price = get_gas_price()
        print(f"\nCurrent Gas Price: {gas_price:.2f} Gwei")

        # Fetch transaction details
        tx_details = get_transaction_details(max_log["transactionHash"].hex())
        print("\nTransaction Details:")
        if "error" in tx_details:
            print(f"Error: {tx_details['error']}")
        else:
            print(f"From: {tx_details['from']}")
            print(f"To: {tx_details['to']}")
            print(f"Value: {tx_details['value']} ETH")
            print(f"Gas Used: {tx_details['gas_used']}")
            print(f"Gas Price: {tx_details['gas_price']} Gwei")
            print(f"Status: {tx_details['status']}")

        # Add new analysis after existing transaction details
        print("\nTransfer Statistics (last 100 blocks):")
        current_block = web3.eth.block_number
        stats = get_transfer_stats(current_block - 100, current_block)
        if "error" not in stats:
            print(f"Total Transfers: {stats['total_transfers']}")
            print(f"Total Volume: {stats['total_volume']}")
            print(f"Unique Senders: {stats['unique_senders']}")
            print(f"Unique Receivers: {stats['unique_receivers']}")
            print(f"Average Transfer: {stats['avg_transfer']}")

        print("\nChecking for Suspicious Activity:")
        suspicious = check_suspicious_activity(to_address)
        if "error" not in suspicious:
            print(f"Total Sent: {suspicious['total_sent']}")
            print(f"Total Received: {suspicious['total_received']}")
            print(f"Number of Transactions: {suspicious['num_transactions']}")
            if suspicious["suspicious_patterns"]:
                print("Suspicious Patterns Found:")
                for pattern in suspicious["suspicious_patterns"]:
                    print(f"- {pattern}")
            else:
                print("No suspicious patterns detected")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    run()
