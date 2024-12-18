import pytest
from eth_typing import HexStr
from unittest.mock import Mock, patch
from dai_transfer import run

@pytest.fixture
def mock_web3(mocker):
    """Fixture to mock Web3 interactions"""
    mock = Mock()
    
    # Mock block number
    mock.eth.block_number = 15000000
    
    # Mock logs with sample transfer data
    sample_logs = [
        {
            'data': '0x00000000000000000000000000000000000000000000000006f05b59d3b20000',  # 8 DAI
            'topics': [
                HexStr('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
                HexStr('0x000000000000000000000000123456789abcdef123456789abcdef123456789a'),
                HexStr('0x000000000000000000000000abcdef123456789abcdef123456789abcdef1234')
            ]
        },
        {
            'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',  # 1 DAI
            'topics': [
                HexStr('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
                HexStr('0x0000000000000000000000002222222222222222222222222222222222222222'),
                HexStr('0x0000000000000000000000003333333333333333333333333333333333333333')
            ]
        }
    ]
    
    mock.eth.get_logs.return_value = sample_logs
    
    with patch('dai_transfer.web3', mock):
        yield mock

@pytest.mark.asyncio
async def test_run_finds_largest_transfer(mock_web3, capsys):
    """Test that run() correctly identifies and prints the largest transfer destination"""
    await run()
    captured = capsys.readouterr()
    
    # Should print the destination address of the transfer with 8 DAI (the larger amount)
    assert captured.out.strip() == "0xabcdef123456789abcdef123456789abcdef1234"

@pytest.mark.asyncio
async def test_run_queries_correct_block_range(mock_web3):
    """Test that the correct block range is queried"""
    await run()
    
    # Check if get_logs was called with correct parameters
    mock_web3.eth.get_logs.assert_called_once()
    call_args = mock_web3.eth.get_logs.call_args[0][0]
    
    assert call_args['fromBlock'] == 15000000 - 120  # Current block - INFURA_MAX_HISTORY
    assert call_args['address'] == '0x6b175474e89094c44da98b954eedeac495271d0f'
    assert len(call_args['topics']) == 1
    assert call_args['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

@pytest.mark.asyncio
async def test_run_with_empty_logs(mock_web3):
    """Test handling of empty logs"""
    mock_web3.eth.get_logs.return_value = []
    
    with pytest.raises(ValueError) as exc_info:
        await run()
    
    assert "max() arg is an empty sequence" in str(exc_info.value) 