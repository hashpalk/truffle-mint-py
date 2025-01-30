import pytest
from unittest.mock import Mock, patch
from web3 import Web3
from decimal import Decimal
from get_address import format_dai_amount, get_address_details, run


@pytest.fixture
def mock_web3():
    with patch("get_address.web3") as mock:
        # Mock basic Web3 setup
        mock.eth.block_number = 1000
        mock.from_wei.return_value = 1.5
        yield mock


@pytest.fixture
def mock_transfer_logs():
    return [
        {
            "data": "0x00000000000000000000000000000000000000000000000d8d726b7177a80000",  # 1000 DAI
            "topics": [
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                "0x000000000000000000000000123456789abcdef123456789abcdef123456789a",
                "0x000000000000000000000000987654321abcdef987654321abcdef987654321a",
            ],
            "blockNumber": 990,
        },
        {
            "data": "0x0000000000000000000000000000000000000000000001158e460913d00000000",  # 5000 DAI
            "topics": [
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                "0x000000000000000000000000aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "0x000000000000000000000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            ],
            "blockNumber": 995,
        },
    ]


def test_format_dai_amount():
    """Test DAI amount formatting"""
    # Test with 1 DAI (1e18 wei)
    amount_wei = 1000000000000000000
    assert format_dai_amount(amount_wei) == "1.00 DAI"

    # Test with 1000.5 DAI
    amount_wei = 1000500000000000000000
    assert format_dai_amount(amount_wei) == "1,000.50 DAI"


def test_get_address_details(mock_web3):
    """Test getting address details"""
    test_address = "0x123456789abcdef123456789abcdef123456789a"

    # Mock contract check
    mock_web3.eth.get_code.return_value.hex.return_value = "0x"
    mock_web3.eth.get_balance.return_value = 1500000000000000000  # 1.5 ETH

    details = get_address_details(test_address)

    assert details["is_contract"] == False
    assert details["eth_balance"] == 1.5
    assert details["address"] == test_address


@pytest.mark.parametrize(
    "code_hex,expected_type",
    [
        ("0x", False),  # EOA
        ("0x123456", True),  # Contract
    ],
)
def test_address_type_detection(mock_web3, code_hex, expected_type):
    """Test contract detection logic"""
    test_address = "0x123456789abcdef123456789abcdef123456789a"
    mock_web3.eth.get_code.return_value.hex.return_value = code_hex

    details = get_address_details(test_address)
    assert details["is_contract"] == expected_type


@patch("builtins.print")
def test_run_with_transfers(mock_print, mock_web3, mock_transfer_logs):
    """Test run function with mock transfer logs"""
    mock_web3.eth.get_logs.return_value = mock_transfer_logs
    mock_web3.eth.get_block.return_value = {"timestamp": 1234567890}
    mock_web3.eth.get_code.return_value.hex.return_value = "0x"

    # Run the main function
    run()

    # Verify the largest transfer was found
    mock_print.assert_any_call("Amount: 5,000.00 DAI")
    mock_print.assert_any_call("Block: 995")


@patch("builtins.print")
def test_run_with_no_transfers(mock_print, mock_web3):
    """Test run function with no transfer logs"""
    mock_web3.eth.get_logs.return_value = []

    run()

    mock_print.assert_called_with("No DAI transfers found in the specified block range")


@patch("builtins.print")
def test_run_with_error(mock_print, mock_web3):
    """Test run function error handling"""
    mock_web3.eth.get_logs.side_effect = Exception("Test error")

    run()

    mock_print.assert_called_with("An error occurred: Test error")
