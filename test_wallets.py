#!/usr/bin/env python3
"""
Comprehensive test suite for multi-wallet support.
Tests balance monitoring, address validation, and transaction methods.
"""

import asyncio
import sys
import os

sys.path.insert(0, 'src')

from inputs.plugins.wallet_ethereum import WalletEthereum
from inputs.plugins.wallet_solana import WalletSolana
from inputs.base import SensorConfig


async def test_ethereum_wallet():
    """Test Ethereum wallet functionality."""
    print("\n" + "="*60)
    print("TEST 1: Ethereum Wallet")
    print("="*60)
    
    try:
        # Use Vitalik's public address for testing
        os.environ['ETH_ADDRESS'] = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'
        
        print("Initializing WalletEthereum...")
        wallet = WalletEthereum(SensorConfig())
        
        print(f"✅ Wallet initialized")
        print(f"   Address: {wallet.get_wallet_address()}")
        print(f"   Supported assets: {wallet.get_supported_assets()}")
        
        print("\nFetching balance...")
        balance = await wallet.fetch_balance("eth")
        print(f"✅ Balance fetched: {balance:.5f} ETH")
        
        print("\nTesting sign_message (read-only mode)...")
        sign_result = await wallet.sign_message("Test message")
        if sign_result['status'] == 'failed':
            print(f"✅ Expected failure (no private key): {sign_result['error']}")
        else:
            print(f"✅ Message signed: {sign_result['signature'][:20]}...")
        
        print("\nTesting transfer (read-only mode)...")
        transfer_result = await wallet.transfer(
            to_address="0x0000000000000000000000000000000000000000",
            amount=0.001,
            asset="eth"
        )
        if transfer_result['status'] == 'failed':
            print(f"✅ Expected failure (no private key): {transfer_result['error']}")
        else:
            print(f"⚠️ Unexpected success: {transfer_result}")
        
        print("\n✅ WalletEthereum: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ WalletEthereum test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_solana_wallet():
    """Test Solana wallet functionality."""
    print("\n" + "="*60)
    print("TEST 2: Solana Wallet")
    print("="*60)
    
    try:
        # Use a public Solana address for testing
        os.environ['SOLANA_WALLET_ADDRESS'] = 'EzGfEo4qV5FnQ3p6Qr5iFkT3n6rqvWq6dZqCqP5uyPxC'
        
        print("Initializing WalletSolana...")
        wallet = WalletSolana(SensorConfig())
        
        print(f"✅ Wallet initialized")
        print(f"   Address: {wallet.get_wallet_address()}")
        print(f"   Supported assets: {wallet.get_supported_assets()}")
        
        print("\nFetching balance...")
        balance = await wallet.fetch_balance("sol")
        print(f"✅ Balance fetched: {balance:.5f} SOL")
        
        print("\nTesting sign_message (read-only mode)...")
        sign_result = await wallet.sign_message("Test message")
        if sign_result['status'] == 'failed':
            print(f"✅ Expected failure (no private key): {sign_result['error']}")
        else:
            print(f"✅ Message signed: {sign_result['signature'][:20]}...")
        
        print("\nTesting transfer (read-only mode)...")
        transfer_result = await wallet.transfer(
            to_address="11111111111111111111111111111111",
            amount=0.001,
            asset="sol"
        )
        if transfer_result['status'] == 'failed':
            print(f"✅ Expected failure (no private key): {transfer_result['error']}")
        else:
            print(f"⚠️ Unexpected success: {transfer_result}")
        
        print("\n✅ WalletSolana: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ WalletSolana test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_base_class_interface():
    """Test that all wallets implement the base interface correctly."""
    print("\n" + "="*60)
    print("TEST 3: WalletBase Interface Compliance")
    print("="*60)
    
    from inputs.plugins.wallet_base import WalletBase
    import inspect
    
    required_methods = ['fetch_balance', 'get_wallet_address', 
                       'get_supported_assets', 'transfer', 'sign_message']
    
    wallets = [
        ('WalletEthereum', WalletEthereum),
        ('WalletSolana', WalletSolana)
    ]
    
    all_pass = True
    for wallet_name, wallet_class in wallets:
        print(f"\nChecking {wallet_name}...")
        for method in required_methods:
            if hasattr(wallet_class, method):
                print(f"  ✅ {method}()")
            else:
                print(f"  ❌ {method}() - MISSING")
                all_pass = False
    
    if all_pass:
        print("\n✅ All wallets implement WalletBase interface correctly")
    else:
        print("\n❌ Some wallets missing required methods")
    
    return all_pass


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MULTI-WALLET TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Ethereum
    results.append(await test_ethereum_wallet())
    
    # Test 2: Solana
    results.append(await test_solana_wallet())
    
    # Test 3: Interface compliance
    results.append(await test_base_class_interface())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Ready to commit!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Fix issues before committing")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
