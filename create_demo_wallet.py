#!/usr/bin/env python3
"""Create a real wallet for charity donation demo"""

from eth_account import Account
import secrets

# Generate new wallet
priv = secrets.token_hex(32)
private_key = "0x" + priv
account = Account.from_key(private_key)

print("="*60)
print("🎉 DEMO CHARITY WALLET CREATED")
print("="*60)
print(f"\n📍 Ethereum Address: {account.address}")
print(f"🔐 Private Key: {private_key}")
print("\n⚠️  IMPORTANT:")
print("   - This is a REAL wallet on Ethereum blockchain")
print("   - Keep private key secret (for demo only)")
print("   - Works on Sepolia testnet AND mainnet")
print("   - Can receive real crypto donations")
print("\n💡 For Bounty Submission:")
print("   1. Use this address in connector")
print("   2. Get testnet ETH from faucet")
print("   3. Demo real transactions")
print("   4. Show on Etherscan as proof")
print("="*60)
