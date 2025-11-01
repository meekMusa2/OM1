import logging
import os
from typing import List, Dict, Any

from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed

from inputs.base import SensorConfig
from inputs.plugins.wallet_base import WalletBase


class WalletSolana(WalletBase):
    """
    Solana wallet monitor.
    Tracks SOL balance changes and supports transactions.
    Supports Phantom, Solflare, and other Solana wallets.
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        # Override primary_asset before calling super().__init__
        if not hasattr(config, 'primary_asset'):
            setattr(config, 'primary_asset', 'sol')
        
        super().__init__(config)
        
        # Solana-specific configuration
        self.rpc_url = os.environ.get(
            "SOLANA_RPC_URL", 
            "https://api.mainnet-beta.solana.com"
        )
        self.wallet_address = os.environ.get("SOLANA_WALLET_ADDRESS")
        
        if not self.wallet_address:
            raise ValueError("SOLANA_WALLET_ADDRESS environment variable is not set")
        
        # Optional: Private key for signing transactions (read-only mode if not provided)
        self.private_key_bytes = os.environ.get("SOLANA_PRIVATE_KEY")
        self.keypair = None
        if self.private_key_bytes:
            try:
                # Parse private key (expected as base58 or bytes)
                import base58
                key_bytes = base58.b58decode(self.private_key_bytes)
                self.keypair = Keypair.from_bytes(key_bytes)
                logging.info("WalletSolana: Transaction signing enabled")
            except Exception as e:
                logging.warning(f"WalletSolana: Could not load private key: {e}")
        else:
            logging.warning("WalletSolana: Read-only mode (no SOLANA_PRIVATE_KEY)")
        
        logging.info(f"Using {self.wallet_address} as the Solana wallet address")
        logging.info(f"RPC URL: {self.rpc_url}")
        
        # Initialize Solana client
        try:
            self.client = Client(self.rpc_url)
            
            # Validate address format
            self.pubkey = Pubkey.from_string(self.wallet_address)
            
            # Test connection by getting balance
            balance_response = self.client.get_balance(self.pubkey)
            if balance_response.value is None:
                raise ConnectionError(f"Failed to get balance from Solana RPC: {self.rpc_url}")
            
            # Solana balance is in lamports (1 SOL = 1,000,000,000 lamports)
            self.balance = balance_response.value / 1_000_000_000
            self.balance_previous = self.balance
            
            logging.info(f"WalletSolana: Initialized with balance {self.balance} SOL")
            
        except Exception as e:
            logging.error(f"Error connecting to Solana: {e}")
            raise

    async def fetch_balance(self, asset: str = "sol") -> float:
        """
        Fetch current SOL balance from Solana blockchain.
        
        Parameters
        ----------
        asset : str
            Asset identifier (only 'sol' supported currently)
            
        Returns
        -------
        float
            Current balance in SOL
        """
        try:
            # Get balance in lamports
            balance_response = self.client.get_balance(self.pubkey)
            
            if balance_response.value is None:
                raise ValueError("Failed to fetch balance from Solana")
            
            # Convert lamports to SOL
            balance_sol = balance_response.value / 1_000_000_000
            
            logging.info(f"WalletSolana: Balance fetched: {balance_sol} SOL")
            
            return balance_sol
            
        except Exception as e:
            logging.error(f"Error fetching Solana balance: {e}")
            return self.balance

    def get_wallet_address(self) -> str:
        """
        Get the Solana wallet address.
        
        Returns
        -------
        str
            Solana public key (base58 encoded)
        """
        return self.wallet_address

    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported assets for Solana wallet.
        
        Returns
        -------
        List[str]
            List of asset identifiers
        """
        return ["sol"]

    async def transfer(
        self, 
        to_address: str, 
        amount: float, 
        asset: str = "sol"
    ) -> Dict[str, Any]:
        """
        Transfer SOL to another address.
        
        Parameters
        ----------
        to_address : str
            Recipient Solana address
        amount : float
            Amount in SOL
        asset : str
            Asset to transfer (only 'sol' supported)
            
        Returns
        -------
        Dict[str, Any]
            Transaction details
        """
        if not self.keypair:
            logging.error("WalletSolana: Cannot transfer - no private key configured")
            return {
                "transaction_hash": None,
                "status": "failed",
                "amount": amount,
                "asset": asset,
                "to_address": to_address,
                "error": "No private key configured (read-only mode)"
            }
        
        try:
            logging.info(f"WalletSolana: Initiating transfer of {amount} SOL to {to_address}")
            
            # Parse recipient address
            recipient_pubkey = Pubkey.from_string(to_address)
            
            # Convert SOL to lamports
            lamports = int(amount * 1_000_000_000)
            
            # Create transfer instruction
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports
                )
            )
            
            # Get recent blockhash
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            
            # Create transaction
            transaction = Transaction.new_with_payer(
                instructions=[transfer_ix],
                payer=self.keypair.pubkey(),
            )
            transaction.recent_blockhash = recent_blockhash
            
            # Sign transaction
            transaction.sign([self.keypair])
            
            # Send transaction
            tx_response = self.client.send_transaction(
                transaction,
                self.keypair
            )
            
            tx_signature = str(tx_response.value)
            logging.info(f"WalletSolana: Transaction sent: {tx_signature}")
            
            return {
                "transaction_hash": tx_signature,
                "status": "pending",
                "amount": amount,
                "asset": asset,
                "to_address": to_address,
                "from_address": str(self.keypair.pubkey())
            }
            
        except Exception as e:
            logging.error(f"WalletSolana: Transfer failed: {e}")
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
        Sign a message with the Solana wallet.
        
        Parameters
        ----------
        message : str
            Message to sign
            
        Returns
        -------
        Dict[str, Any]
            Signature details
        """
        if not self.keypair:
            logging.error("WalletSolana: Cannot sign - no private key configured")
            return {
                "signature": None,
                "message": message,
                "address": self.wallet_address,
                "status": "failed",
                "error": "No private key configured (read-only mode)"
            }
        
        try:
            logging.info(f"WalletSolana: Signing message: {message}")
            
            # Convert message to bytes
            message_bytes = message.encode('utf-8')
            
            # Sign message
            signature = self.keypair.sign_message(message_bytes)
            
            logging.info(f"WalletSolana: Message signed successfully")
            
            return {
                "signature": str(signature),
                "message": message,
                "address": str(self.keypair.pubkey()),
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"WalletSolana: Signing failed: {e}")
            return {
                "signature": None,
                "message": message,
                "address": self.wallet_address,
                "status": "failed",
                "error": str(e)
            }
