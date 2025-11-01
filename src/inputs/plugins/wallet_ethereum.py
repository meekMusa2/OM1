import logging
import os
import random
from typing import List, Dict, Any

from web3 import Web3
from eth_account import Account

from inputs.base import SensorConfig
from inputs.plugins.wallet_base import WalletBase


class WalletEthereum(WalletBase):
    """
    Ethereum wallet monitor using Web3.
    Tracks ETH balance changes and supports transactions.
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        super().__init__(config)
        
        # Ethereum-specific configuration
        self.PROVIDER_URL = getattr(config, 'provider_url', "https://eth.llamarpc.com")
        self.ACCOUNT_ADDRESS = os.environ.get(
            "ETH_ADDRESS", "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        )
        
        # Optional: Private key for signing transactions (read-only mode if not provided)
        self.PRIVATE_KEY = os.environ.get("ETH_PRIVATE_KEY")
        self.account = None
        if self.PRIVATE_KEY:
            self.account = Account.from_key(self.PRIVATE_KEY)
            logging.info("WalletEthereum: Transaction signing enabled")
        else:
            logging.warning("WalletEthereum: Read-only mode (no ETH_PRIVATE_KEY)")
        
        # For debugging: simulate random incoming transfers
        self.simulate_transfers = getattr(config, 'simulate_transfers', False)
        
        logging.debug(f"Using {self.ACCOUNT_ADDRESS} as the wallet address")
        
        # Initialize Web3
        self.web3 = Web3(Web3.HTTPProvider(self.PROVIDER_URL))
        if not self.web3.is_connected():
            raise Exception(f"Failed to connect to Ethereum at {self.PROVIDER_URL}")
        
        # Initialize balance
        balance_wei = self.web3.eth.get_balance(self.ACCOUNT_ADDRESS)
        self.balance = float(self.web3.from_wei(balance_wei, "ether"))
        self.balance_previous = self.balance
        
        logging.info(f"WalletEthereum: Initialized with balance {self.balance} ETH")

    async def fetch_balance(self, asset: str = "eth") -> float:
        """
        Fetch current ETH balance from Ethereum blockchain.
        
        Parameters
        ----------
        asset : str
            Asset identifier (only 'eth' supported)
            
        Returns
        -------
        float
            Current balance in ETH
        """
        try:
            # Get latest block for logging
            block_number = self.web3.eth.block_number
            
            # Get account balance
            balance_wei = self.web3.eth.get_balance(self.ACCOUNT_ADDRESS)
            balance_eth = float(self.web3.from_wei(balance_wei, "ether"))
            
            logging.debug(
                f"WalletEthereum: Block {block_number}, Balance {balance_eth:.5f} ETH"
            )
            
            # Debug mode: randomly simulate incoming transfers
            if self.simulate_transfers:
                dice = random.randint(0, 10)
                if dice > 7:
                    logging.info("WalletEthereum: Simulating +1.0 ETH transfer")
                    balance_eth += 1.0
            
            return balance_eth
            
        except Exception as e:
            logging.error(f"Error fetching Ethereum balance: {e}")
            return self.balance

    def get_wallet_address(self) -> str:
        """
        Get the Ethereum wallet address.
        
        Returns
        -------
        str
            Ethereum address
        """
        return self.ACCOUNT_ADDRESS

    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported assets.
        
        Returns
        -------
        List[str]
            List of asset identifiers
        """
        return ["eth"]

    async def transfer(
        self, 
        to_address: str, 
        amount: float, 
        asset: str = "eth"
    ) -> Dict[str, Any]:
        """
        Transfer ETH to another address.
        
        Parameters
        ----------
        to_address : str
            Recipient Ethereum address
        amount : float
            Amount in ETH
        asset : str
            Asset to transfer (only 'eth' supported)
            
        Returns
        -------
        Dict[str, Any]
            Transaction details
        """
        if not self.account:
            logging.error("WalletEthereum: Cannot transfer - no private key configured")
            return {
                "transaction_hash": None,
                "status": "failed",
                "amount": amount,
                "asset": asset,
                "to_address": to_address,
                "error": "No private key configured (read-only mode)"
            }
        
        try:
            logging.info(f"WalletEthereum: Initiating transfer of {amount} ETH to {to_address}")
            
            # Convert to checksum address
            to_address_checksum = Web3.to_checksum_address(to_address)
            
            # Get transaction parameters
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            gas_price = self.web3.eth.gas_price
            
            # Build transaction
            transaction = {
                'nonce': nonce,
                'to': to_address_checksum,
                'value': self.web3.to_wei(amount, 'ether'),
                'gas': 21000,  # Standard ETH transfer
                'gasPrice': gas_price,
                'chainId': self.web3.eth.chain_id
            }
            
            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logging.info(f"WalletEthereum: Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt (optional, can be async)
            # receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "transaction_hash": tx_hash.hex(),
                "status": "pending",
                "amount": amount,
                "asset": asset,
                "to_address": to_address,
                "from_address": self.account.address
            }
            
        except Exception as e:
            logging.error(f"WalletEthereum: Transfer failed: {e}")
            return {
                "transaction_hash": None,
                "status": "failed",
                "amount": amount,
                "asset": asset,
                "to_address": to_address,
                "error": str(e)
            }

    async def sign_message(self, message: str) -> Dict[str, Any]:
        """
        Sign a message with the Ethereum wallet (EIP-191).
        
        Parameters
        ----------
        message : str
            Message to sign
            
        Returns
        -------
        Dict[str, Any]
            Signature details
        """
        if not self.account:
            logging.error("WalletEthereum: Cannot sign - no private key configured")
            return {
                "signature": None,
                "message": message,
                "address": self.ACCOUNT_ADDRESS,
                "status": "failed",
                "error": "No private key configured (read-only mode)"
            }
        
        try:
            logging.info(f"WalletEthereum: Signing message: {message}")
            
            # Sign message using eth_account
            signed_message = self.account.sign_message(
                Account.messages.encode_defunct(text=message)
            )
            
            logging.info(f"WalletEthereum: Message signed successfully")
            
            return {
                "signature": signed_message.signature.hex(),
                "message": message,
                "address": self.account.address,
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"WalletEthereum: Signing failed: {e}")
            return {
                "signature": None,
                "message": message,
                "address": self.ACCOUNT_ADDRESS,
                "status": "failed",
                "error": str(e)
            }
