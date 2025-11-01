# Testnet Setup Guide for Demo Video

This guide helps you set up testnet wallets to demonstrate actual transaction signing.

## Ethereum Sepolia Testnet

### Step 1: Create Wallet
1. Install MetaMask: https://metamask.io
2. Create new wallet or use existing
3. Switch network to "Sepolia Test Network"

### Step 2: Get Testnet ETH
1. Visit https://sepoliafaucet.com
2. Enter your wallet address
3. Request testnet ETH (usually 0.5 ETH)

### Step 3: Export Private Key
1. Open MetaMask
2. Click account menu → Account details
3. Click "Show private key"
4. Enter password
5. Copy private key

### Step 4: Set Environment Variables
```bash
export ETH_PRIVATE_KEY="0x_your_private_key_here"
export ETH_ADDRESS="0x_your_address_here"
```

## Solana Devnet

### Step 1: Install Solana CLI
```bash
# macOS/Linux
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Verify installation
solana --version
```

### Step 2: Generate Wallet
```bash
# Generate new wallet
solana-keygen new --outfile ~/solana-demo-wallet.json

# Set config to use devnet
solana config set --url devnet

# View your address
solana address -k ~/solana-demo-wallet.json
```

### Step 3: Get Devnet SOL
```bash
# Request airdrop (2 SOL)
solana airdrop 2 $(solana address -k ~/solana-demo-wallet.json)

# Check balance
solana balance -k ~/solana-demo-wallet.json
```

### Step 4: Export Private Key
```bash
# View private key
cat ~/solana-demo-wallet.json

# Convert to base58 (you'll need to use a converter or Python)
python3 << 'PYEOF'
import json
import base58

with open('/path/to/solana-demo-wallet.json') as f:
    keypair = json.load(f)
    private_key = bytes(keypair[:32])
    print(base58.b58encode(private_key).decode())
PYEOF
```

### Step 5: Set Environment Variables
```bash
export SOLANA_PRIVATE_KEY="base58_encoded_key_here"
export SOLANA_WALLET_ADDRESS="your_solana_address_here"
```

## Running the Demo
```bash
# Run transaction demo
uv run python3 demo_transactions.py
```

## Recording the Demo Video

### What to Show:
1. **Introduction** (30 sec)
   - Explain multi-wallet support
   - Show the three wallets: Coinbase, Ethereum, Solana

2. **Code Walkthrough** (1 min)
   - Show WalletBase abstract class
   - Show one wallet implementation
   - Highlight modular architecture

3. **Live Demo** (2-3 min)
   - Run `demo_transactions.py`
   - Show Ethereum transaction on Sepolia
   - Show Solana transaction on Devnet
   - Show transaction on block explorer
   - Show message signing

4. **Read-Only Mode** (30 sec)
   - Show balance monitoring without private keys
   - Security feature explanation

5. **Conclusion** (30 sec)
   - Summary of features
   - Link to PR and documentation

### Recording Tools:
- **Screen recording**: OBS Studio (free), Loom, or built-in OS tools
- **Length**: 4-5 minutes ideal
- **Upload**: YouTube (unlisted) or Google Drive

## Safety Notes

⚠️ **IMPORTANT:**
- Only use testnet funds (no real money)
- Never share mainnet private keys
- Delete testnet wallets after demo
- These are throwaway wallets for demonstration only

## Troubleshooting

### "Insufficient balance"
- Get more testnet tokens from faucets
- Wait a few minutes and try again

### "Connection failed"
- Check internet connection
- RPC endpoints might be rate-limited
- Try alternative RPC URLs

### "Invalid private key"
- Ensure proper format (0x prefix for Ethereum)
- Check for extra spaces or quotes
- Regenerate wallet if needed
