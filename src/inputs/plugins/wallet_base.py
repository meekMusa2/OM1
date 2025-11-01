"""
Base class for wallet integrations.
All wallet providers should inherit from this class.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import time

from inputs.base import SensorConfig
from inputs.base.loop import FuserInput
from providers.io_provider import IOProvider


@dataclass
class Message:
    timestamp: float
    message: str


class WalletBase(FuserInput[float], ABC):
    """
    Abstract base class for wallet integrations.
    
    All wallet providers must implement:
    - fetch_balance(): Get current balance
    - get_wallet_address(): Get wallet address
    - get_supported_assets(): List supported cryptocurrencies
    - transfer(): Send cryptocurrency to another address
    - sign_message(): Sign a message with the wallet
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        super().__init__(config)
        
        # Track IO
        self.io_provider = IOProvider()
        self.messages: List[Message] = []
        
        # Common configuration
        self.POLL_INTERVAL = getattr(config, 'poll_interval', 0.5)
        self.primary_asset = getattr(config, 'primary_asset', 'eth')
        
        # Balance tracking
        self.balance = 0.0
        self.balance_previous = 0.0
        
        logging.info(f"Initializing {self.__class__.__name__}")

    @abstractmethod
    async def fetch_balance(self, asset: str = "eth") -> float:
        """
        Fetch current balance for specified asset.
        
        Parameters
        ----------
        asset : str
            Asset identifier (e.g., 'eth', 'btc', 'usdc')
            
        Returns
        -------
        float
            Current balance
        """
        pass

    @abstractmethod
    def get_wallet_address(self) -> str:
        """
        Get the wallet address.
        
        Returns
        -------
        str
            Wallet address
        """
        pass

    @abstractmethod
    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported assets for this wallet.
        
        Returns
        -------
        List[str]
            List of asset identifiers
        """
        pass

    @abstractmethod
    async def transfer(
        self, 
        to_address: str, 
        amount: float, 
        asset: str = "eth"
    ) -> Dict[str, Any]:
        """
        Transfer cryptocurrency to another address.
        
        Parameters
        ----------
        to_address : str
            Recipient wallet address
        amount : float
            Amount to transfer
        asset : str
            Asset to transfer (e.g., 'eth', 'sol', 'usdc')
            
        Returns
        -------
        Dict[str, Any]
            Transaction details including:
            - transaction_hash: Transaction ID
            - status: 'pending', 'completed', or 'failed'
            - amount: Amount transferred
            - to_address: Recipient address
        """
        pass

    @abstractmethod
    async def sign_message(self, message: str) -> Dict[str, Any]:
        """
        Sign a message with the wallet's private key.
        
        Parameters
        ----------
        message : str
            Message to sign
            
        Returns
        -------
        Dict[str, Any]
            Signature details including:
            - signature: Cryptographic signature
            - message: Original message
            - address: Signer's wallet address
        """
        pass

    async def _poll(self) -> List[float]:
        """
        Poll for wallet balance updates.
        
        Returns
        -------
        List[float]
            [current_balance, balance_change]
        """
        import asyncio
        await asyncio.sleep(self.POLL_INTERVAL)
        
        # Fetch current balance
        self.balance = await self.fetch_balance(self.primary_asset)
        balance_change = self.balance - self.balance_previous
        self.balance_previous = self.balance
        
        logging.debug(
            f"{self.__class__.__name__}: Balance={self.balance}, Change={balance_change}"
        )
        
        return [self.balance, balance_change]

    async def _raw_to_text(self, raw_input: List[float]) -> Optional[Message]:
        """
        Convert balance data to human-readable message.
        
        Parameters
        ----------
        raw_input : List[float]
            [current_balance, balance_change]
            
        Returns
        -------
        Message
            Timestamped transaction notification
        """
        balance_change = raw_input[1]
        
        if balance_change > 0:
            message = f"{balance_change:.5f}"
            logging.info(f"\n\n{self.__class__.__name__} balance change: {message}")
            return Message(timestamp=time.time(), message=message)
        
        return None

    async def raw_to_text(self, raw_input: List[float]):
        """
        Process balance update and manage message buffer.
        
        Parameters
        ----------
        raw_input : List[float]
            Raw balance data
        """
        pending_message = await self._raw_to_text(raw_input)
        
        if pending_message is not None:
            self.messages.append(pending_message)

    def formatted_latest_buffer(self) -> Optional[str]:
        """
        Format and clear the buffer contents.
        
        Returns
        -------
        Optional[str]
            Formatted string of buffer contents or None if buffer is empty
        """
        if len(self.messages) == 0:
            return None
        
        transaction_sum = 0.0
        for message in self.messages:
            transaction_sum += float(message.message)
        
        last_message = self.messages[-1]
        result_message = Message(
            timestamp=last_message.timestamp,
            message=f"You just received {transaction_sum:.5f} {self.primary_asset.upper()}.",
        )
        
        result = f"""
{self.__class__.__name__} INPUT
// START
{result_message.message}
// END
"""
        
        self.io_provider.add_input(
            self.__class__.__name__, result_message.message, result_message.timestamp
        )
        self.messages = []
        return result
