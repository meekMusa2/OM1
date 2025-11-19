from dataclasses import dataclass
from actions.base import Interface

@dataclass
class CharityDonationInput:
    """Input interface for charity donations with real blockchain verification."""
    action: str = ""  # "browse_charities", "donate", "verify_transaction", "check_donation"
    charity_name: str = ""
    charity_id: str = ""
    amount_usd: float = 0.0
    donor_email: str = ""
    donation_id: str = ""  # Also used for transaction hash in verify_transaction

class CharityDonation(Interface):
    """Charity donation interface."""
    input: CharityDonationInput
    output: CharityDonationInput
