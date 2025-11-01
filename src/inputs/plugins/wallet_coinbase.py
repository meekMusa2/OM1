import logging
import os
from typing import List, Dict, Any

from cdp import Cdp, Wallet

from inputs.base import SensorConfig
from inputs.plugins.wallet_base import WalletBase


class WalletCoinbase(WalletBase):
    """
    Coinbase CDP wallet integration.
    Queries current balance and supports transactions.
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        # Initialize base class first
        super().__init__(config)
        
        # Coinbase-specific configuration
        self.COINBASE_WALLET_ID = os.environ.get("COINBASE_WALLET_ID")
        logging.info(f"Using {self.COINBASE_WALLET_ID} as the coinbase wallet id")

        # Initialize Coinbase CDP
        API_KEY = os.environ.get("COINBASE_API_KEY")
        API_SECRET = os.environ.get("COINBASE_API_SECRET")
        
        if not API_KEY or not API_SECRET:
            logging.error(
                "COINBASE_API_KEY or COINBASE_API_SECRET environment variable is not set"
            )
            raise ValueError("Missing Coinbase API credentials")
        
        Cdp.configure(API_KEY, API_SECRET)

        # Fetch wallet
        try:
            if not self.COINBASE_WALLET_ID:
                raise ValueError("COINBASE_WALLET_ID environment variable is not set")

            self.wallet = Wallet.fetch(self.COINBASE_WALLET_ID)
            logging.info(f"Wallet: {self.wallet}")
        except Exception as e:
            logging.error(f"Error fetching Coinbase Wallet data: {e}")
            raise

        # Initialize balance tracking
        self.balance = float(self.wallet.balance(self.primary_asset))
        self.balance_previous = self.balance

        logging.info("WalletCoinbase: Initialized")

    async def fetch_balance(self, asset: str = "eth") -> float:
        """
        Fetch current balance from Coinbase wallet.
        
        Parameters
        ----------
        asset : str
            Asset identifier (e.g., 'eth', 'usdc')
            
        Returns
        -------
        float
            Current balance
        """
        # Refresh wallet data from blockchain
        self.wallet = Wallet.fetch(self.COINBASE_WALLET_ID)  # type: ignore
        balance = float(self.wallet.balance(asset))
        
        logging.info(
            f"WalletCoinbase: Wallet refreshed: {balance} {asset.upper()}"
        )
        
        return balance

    def get_wallet_address(self) -> str:
        """
        Get the Coinbase wallet address.
        
        Returns
        -------
        str
            Wallet address
        """
        return self.wallet.default_address.address_id

    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported assets for Coinbase CDP.
        
        Returns
        -------
        List[str]
            List of asset identifiers
        """
        return ["eth", "usdc", "weth", "gwei"]

    async def transfer(
        self, 
        to_address: str, 
        amount: float, 
        asset: str = "eth"
    ) -> Dict[str, Any]:
        """
        Transfer cryptocurrency to another address using Coinbase CDP.
        
        Parameters
        ----------
        to_address : str
            Recipient wallet address
        amount : float
            Amount to transfer
        asset : str
            Asset to transfer (default: 'eth')
            
        Returns
        -------
        Dict[str, Any]
            Transaction details
        """
        try:
            logging.info(f"WalletCoinbase: Initiating transfer of {amount} {asset} to {to_address}")
            
            # Execute transfer using CDP SDK
            transfer_result = self.wallet.transfer(
                amount=amount,
                asset_id=asset,
                destination=to_address
            )
            
            # Wait for transaction to complete
            transfer_result.wait()
            
            logging.info(f"WalletCoinbase: Transfer completed: {transfer_result.transaction_hash}")
            
            return {
                "transaction_hash": transfer_result.transaction_hash,
                "status": "completed",
                "amount": amount,
                "asset": asset,
                "to_address": to_address,
                "from_address": self.get_wallet_address()
            }
            
        except Exception as e:
            logging.error(f"WalletCoinbase: Transfer failed: {e}")
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
        Sign a message with the Coinbase wallet.
        
        Parameters
        ----------
        message : str
            Message to sign
            
        Returns
        -------
        Dict[str, Any]
            Signature details
        """
        try:
            logging.info(f"WalletCoinbase: Signing message: {message}")
            
            # Sign message using CDP SDK
            signature = self.wallet.sign_payload(
                unsigned_payload=message
            )
            
            logging.info(f"WalletCoinbase: Message signed successfully")
            
            return {
                "signature": str(signature),
                "message": message,
                "address": self.get_wallet_address(),
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"WalletCoinbase: Signing failed: {e}")
            return {
                "signature": None,
                "message": message,
                "address": self.get_wallet_address(),
                "status": "failed",
                "error": str(e)
            }
