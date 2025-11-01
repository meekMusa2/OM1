# Multi-Wallet Integration for OM1

This integration adds modular support for multiple cryptocurrency wallet providers to OM1.

## Architecture

### Base Class: `WalletBase`
All wallet providers inherit from `src/inputs/plugins/wallet_base.py`, providing:
- Balance polling and change detection
- Message buffering and formatting
- Standardized interface for all blockchains

### Supported Wallets

#### 1. Coinbase CDP Wallet (`WalletCoinbase`)
- **File:** `src/inputs/plugins/wallet_coinbase.py`
- **Blockchain:** Multi-chain (Ethereum, Polygon, Base)
- **Assets:** ETH, USDC, WETH, GWEI
- **Requirements:**
```bash
  COINBASE_API_KEY=your_api_key
  COINBASE_API_SECRET=your_api_secret
  COINBASE_WALLET_ID=your_wallet_id
```

#### 2. Ethereum Wallet (`WalletEthereum`)
- **File:** `src/inputs/plugins/wallet_ethereum.py`
- **Blockchain:** Ethereum mainnet
- **Assets:** ETH
- **Requirements:**
```bash
  ETH_ADDRESS=0xYourEthereumAddress
```
- **Optional:** Custom RPC via config: `provider_url`

#### 3. Solana Wallet (`WalletSolana`) - NEW
- **File:** `src/inputs/plugins/wallet_solana.py`
- **Blockchain:** Solana
- **Assets:** SOL (extendable to SPL tokens)
- **Supports:** Phantom, Solflare, and any Solana wallet
- **Requirements:**
```bash
  SOLANA_WALLET_ADDRESS=YourSolanaPublicKey
  SOLANA_RPC_URL=https://api.mainnet-beta.solana.com  # Optional
```

## Setup Instructions

### 1. Install Dependencies
```bash
cd ~/OM1
uv pip install web3 solana solders
```

### 2. Configure Environment Variables

Create or update `.env` file:
```bash
# Coinbase Wallet (optional)
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret
COINBASE_WALLET_ID=your_wallet_id

# Ethereum Wallet (optional)
ETH_ADDRESS=0xYourEthereumAddress

# Solana Wallet (optional)
SOLANA_WALLET_ADDRESS=YourSolanaPublicKey
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### 3. Configure OM1

Add wallet inputs to your config file:
```json5
{
  "agent_inputs": [
    {
      "type": "WalletCoinbase"  // Coinbase CDP wallet
    },
    {
      "type": "WalletEthereum"  // Ethereum address monitoring
    },
    {
      "type": "WalletSolana"    // Solana address monitoring
    }
  ]
}
```

### 4. Run OM1
```bash
uv run src/run.py your_config
```

## How It Works

1. **Polling:** Each wallet polls its balance at regular intervals (default: 0.5s)
2. **Change Detection:** When balance increases, a message is generated
3. **Buffer Management:** Multiple transactions are combined into a single notification
4. **LLM Integration:** The LLM receives formatted messages like:
```
   WalletEthereum INPUT
   // START
   You just received 0.00500 ETH.
   // END
```

## Modular Architecture
```
┌─────────────────────────────────────────┐
│           WalletBase                    │
│  (Abstract Base Class)                  │
│  - Balance polling                      │
│  - Change detection                     │
│  - Message buffering                    │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┬──────────────┐
        │                   │              │
┌───────▼────────┐  ┌──────▼──────────┐ ┌─▼────────────┐
│ WalletCoinbase │  │ WalletEthereum  │ │WalletSolana  │
│  (CDP API)     │  │  (Web3/RPC)     │ │(Solana RPC)  │
└────────────────┘  └─────────────────┘ └──────────────┘
```

## Adding New Wallet Providers

To add support for a new blockchain:

### 1. Create Wallet Plugin

Create `src/inputs/plugins/wallet_yourchain.py`:
```python
from typing import List
from inputs.base import SensorConfig
from inputs.plugins.wallet_base import WalletBase

class WalletYourChain(WalletBase):
    """Your blockchain wallet integration."""
    
    def __init__(self, config: SensorConfig = SensorConfig()):
        super().__init__(config)
        # Initialize your blockchain client
    
    async def fetch_balance(self, asset: str = "token") -> float:
        """Fetch balance from your blockchain."""
        # Implement balance fetching
        return 0.0
    
    def get_wallet_address(self) -> str:
        """Return wallet address."""
        return self.wallet_address
    
    def get_supported_assets(self) -> List[str]:
        """List supported assets."""
        return ["token"]
```

### 2. Add Environment Variables

Update `.env`:
```bash
YOUR_CHAIN_WALLET_ADDRESS=address
YOUR_CHAIN_RPC_URL=https://rpc.yourchain.com
```

### 3. Use in Config
```json5
{
  "agent_inputs": [
    {
      "type": "WalletYourChain"
    }
  ]
}
```

## Example: Multi-Wallet Robot Configuration
```json5
{
  "hertz": 1,
  "name": "crypto_monitor",
  "api_key": "openmind_free",
  "system_prompt_base": "You are a cryptocurrency portfolio assistant. When you receive crypto, acknowledge it and provide the current total across all wallets.",
  "agent_inputs": [
    {
      "type": "WalletCoinbase"
    },
    {
      "type": "WalletEthereum"
    },
    {
      "type": "WalletSolana"
    }
  ],
  "cortex_llm": {
    "type": "OpenAILLM",
    "config": {
      "agent_name": "CryptoBot",
      "history_length": 10
    }
  },
  "agent_actions": [
    {
      "name": "speak",
      "llm_label": "speak",
      "implementation": "passthrough",
      "connector": "elevenlabs_tts"
    }
  ]
}
```

## Testing

### Test Ethereum Wallet
```bash
ETH_ADDRESS=0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 \
uv run src/run.py your_config
```

### Test Solana Wallet
Use any public Solana address (e.g., Solana Foundation's treasury):
```bash
SOLANA_WALLET_ADDRESS=EzGfEo4qV5FnQ3p6Qr5iFkT3n6rqvWq6dZqCqP5uyPxC \
uv run src/run.py your_config
```

## Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use read-only API keys** when available
3. **Monitor public addresses only** for testing
4. **Rotate API keys** after demos
5. **Separate test/production wallets**

## Blockchain Comparison

| Wallet | Blockchain | Speed | Assets | API Type |
|--------|-----------|-------|--------|----------|
| Coinbase | Multi-chain | Fast | ETH, USDC, WETH | REST API |
| Ethereum | Ethereum | Medium | ETH | RPC |
| Solana | Solana | Very Fast | SOL | RPC |

## Files Created/Modified

- `src/inputs/plugins/wallet_base.py` - Base wallet class ✅
- `src/inputs/plugins/wallet_coinbase.py` - Refactored to use base ✅
- `src/inputs/plugins/wallet_ethereum.py` - Refactored to use base ✅
- `src/inputs/plugins/wallet_solana.py` - NEW Solana support ✅
- `MULTI_WALLET_INTEGRATION.md` - This documentation ✅

## Future Enhancements

- [ ] SPL token support (Solana)
- [ ] ERC-20 token monitoring (Ethereum)
- [ ] Bitcoin wallet support
- [ ] Polygon, BSC, Arbitrum chains
- [ ] NFT balance tracking
- [ ] Transaction history
- [ ] Price conversion (USD values)

## Troubleshooting

### "Failed to connect to Ethereum"
- Check network connectivity
- Try alternative RPC: `https://cloudflare-eth.com`
- Verify ETH_ADDRESS is set

### "SOLANA_WALLET_ADDRESS environment variable is not set"
- Add Solana address to `.env`
- Or remove `WalletSolana` from config

### "Invalid Ethereum address"
- Ensure address starts with `0x`
- Verify checksum format
- Use valid Ethereum address

## Contributing

To contribute new blockchain support:
1. Fork the repository
2. Create wallet plugin following `WalletBase` pattern
3. Add tests and documentation
4. Submit pull request

## License

Same as OM1 main repository.

## Transaction Support 🆕

All wallet providers now support **transaction signing** and **cryptocurrency transfers**.

### Transaction Methods

Each wallet implements:

1. **`transfer(to_address, amount, asset)`** - Send cryptocurrency
```python
   result = await wallet.transfer(
       to_address="0xRecipient...",
       amount=0.01,
       asset="eth"
   )
   # Returns: {transaction_hash, status, amount, to_address, from_address}
```

2. **`sign_message(message)`** - Cryptographically sign a message
```python
   result = await wallet.sign_message("Hello, Web3!")
   # Returns: {signature, message, address, status}
```

### Usage Examples

#### Coinbase Wallet Transfer
```python
from inputs.plugins.wallet_coinbase import WalletCoinbase
from inputs.base import SensorConfig

wallet = WalletCoinbase(SensorConfig())
result = await wallet.transfer(
    to_address="0xRecipient...",
    amount=0.01,
    asset="eth"
)
print(f"Transaction: {result['transaction_hash']}")
```

#### Ethereum Wallet Signing
```python
from inputs.plugins.wallet_ethereum import WalletEthereum

wallet = WalletEthereum(SensorConfig())
result = await wallet.sign_message("Verify my identity")
print(f"Signature: {result['signature']}")
```

#### Solana Wallet Transfer
```python
from inputs.plugins.wallet_solana import WalletSolana

wallet = WalletSolana(SensorConfig())
result = await wallet.transfer(
    to_address="SolanaRecipient...",
    amount=0.1,
    asset="sol"
)
print(f"Transaction: {result['transaction_hash']}")
```

### Security Requirements

For transaction signing, you need private keys:
```bash
# Ethereum
ETH_PRIVATE_KEY=0xyourprivatekeyhere

# Solana
SOLANA_PRIVATE_KEY=base58_encoded_private_key
```

⚠️ **IMPORTANT:** 
- Never commit private keys to version control
- Use separate wallets for testing
- Validate recipient addresses before transfers
- Test on testnet first (Sepolia for Ethereum, Devnet for Solana)

### Read-Only Mode

Without private keys, wallets operate in **read-only mode**:
- ✅ Balance monitoring works
- ✅ Address queries work
- ❌ Transfers will fail gracefully
- ❌ Message signing will fail gracefully

This allows safe monitoring without requiring private keys.
