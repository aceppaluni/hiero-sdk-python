"""
Query Balance Example.

.. deprecated::
   CryptoGetAccountBalanceQuery is no longer supported. Use the Mirror Node
   REST API, for example GET /api/v1/accounts/{accountId}, to retrieve
   account balances.

...
"""

import json
import os
import sys
import time
from urllib.request import Request, urlopen

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Client,
    Hbar,
    PrivateKey,
    ResponseCode,
    TransferTransaction,
)


def setup_client():
    """
    Initialize and configure the Hiero SDK client with operator credentials.

    Returns:
        tuple: (client, operator_id, operator_key) - Configured client and operator credentials.

    Raises:
        ValueError: If OPERATOR_ID or OPERATOR_KEY environment variables are not set.
    """
    try:
        client = Client.from_env()
        operator_id = client.operator_account_id
        operator_key = client.operator_private_key

        print(f"Client set up with operator id {client.operator_account_id}")
        return client, operator_id, operator_key
    except ValueError as e:
        print(f"Error setting up client: {e}")
        sys.exit(1)


def get_mirror_node_url():
    """Return the Mirror Node URL for the configured Hedera network."""
    network = os.getenv("HEDERA_NETWORK", "testnet").lower()

    mirror_node_urls = {
        "mainnet": "https://mainnet-public.mirrornode.hedera.com",
        "testnet": "https://testnet.mirrornode.hedera.com",
        "previewnet": "https://previewnet.mirrornode.hedera.com",
    }

    if network not in mirror_node_urls:
        raise ValueError(f"Unsupported HEDERA_NETWORK: {network}. Expected mainnet, testnet, or previewnet.")

    return mirror_node_urls[network]


def create_account(client, operator_key, initial_balance=Hbar(10)):
    """
    Create a new account on the Hedera network with an initial balance.

    Args:
        client (Client): The Hiero SDK client.
        operator_key (PrivateKey): The operator's private key for signing transactions.
        initial_balance (Hbar): Initial HBAR balance for the new account. Defaults to 10 HBAR.

    Returns:
        tuple: (new_account_id, new_account_private_key) - The ID and private key of the new account.
    """
    print("Creating new account...")

    # Generate new account's cryptographic keys
    new_account_private_key = PrivateKey.generate("ed25519")
    new_account_public_key = new_account_private_key.public_key()

    # Create the account creation transaction
    transaction = AccountCreateTransaction(
        key=new_account_public_key, initial_balance=initial_balance, memo="New Account"
    ).freeze_with(client)

    # Sign and execute the transaction
    transaction.sign(operator_key)
    receipt = transaction.execute(client)
    new_account_id = receipt.account_id

    print("✓ Account created successfully")
    print(f"  Account ID: {new_account_id}")
    print(f"  Initial balance: {initial_balance.to_hbars()} hbars ({initial_balance.to_tinybars()} tinybars)\n")

    return new_account_id, new_account_private_key


def get_balance(account_id: AccountId):
    """
    Get an account balance using the Mirror Node REST API.

    Args:
        account_id (AccountId): The account whose balance should be retrieved.

    Returns:
        float: Account balance in HBAR.
    """
    print(f"Querying balance for account {account_id}...")

    mirror_node_url = get_mirror_node_url()
    url = f"{mirror_node_url}/api/v1/accounts/{account_id}"

    request = Request(
        url,
        headers={"Accept": "application/json"},
    )

    with urlopen(request, timeout=10) as response:
        data = json.load(response)

    balance_tinybars = data["balance"]
    balance_hbars = balance_tinybars / 100_000_000

    print("✓ Account balance retrieved successfully")
    print(f"  HBAR balance: {balance_hbars} hbars")

    return balance_hbars


def transfer_hbars(client, operator_id, operator_key, recipient_id, amount):
    """
    Transfer HBAR from the operator account to a recipient account.

    Args:
        client (Client): The Hiero SDK client.
        operator_id (AccountId): The sender's (operator's) account ID.
        operator_key (PrivateKey): The operator's private key for signing.
        recipient_id (AccountId): The recipient's account ID.
        amount (Hbar): The amount of HBAR to transfer.

    Returns:
        str: The status of the transfer transaction.
    """
    print(
        f"Transferring {amount.to_tinybars()} tinybars ({amount.to_hbars()} hbars) from {operator_id} to {recipient_id}..."
    )

    # Create transfer transaction
    transfer_transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -amount.to_tinybars())
        .add_hbar_transfer(recipient_id, amount.to_tinybars())
        .freeze_with(client)
    )

    # Sign and execute the transaction
    transfer_transaction.sign(operator_key)
    transfer_receipt = transfer_transaction.execute(client)

    status = ResponseCode(transfer_receipt.status).name
    print(f"✓ Transfer completed with status: {status}\n")

    return status


def main():
    """Main workflow: Set up client, create account, query balance, and transfer HBAR."""
    try:
        #  Initialize client with operator credentials
        client, operator_id, operator_key = setup_client()

        #  Create a new account with initial balance
        new_account_id, new_account_private_key = create_account(client, operator_key, initial_balance=Hbar(10))

        #  Query and display the initial balance
        print("=" * 60)
        print("INITIAL BALANCE CHECK")
        print("=" * 60)
        initial_balance = get_balance(new_account_id)
        print(f"Initial balance of new account: {initial_balance} hbars")
        print("=" * 60 + "\n")

        # Transfer additional HBAR to the new account
        print("=" * 60)
        print("EXECUTING TRANSFER")
        print("=" * 60)
        transfer_amount = Hbar(5)
        transfer_status = transfer_hbars(client, operator_id, operator_key, new_account_id, transfer_amount)
        print(f"Transfer transaction status: {transfer_status}")
        print("=" * 60 + "\n")

        # Wait briefly for the transaction to be fully processed
        print("Waiting for transfer to be processed...")
        time.sleep(2)

        #  Query and display the updated balance
        print("=" * 60)
        print("UPDATED BALANCE CHECK")
        print("=" * 60)
        updated_balance = get_balance(new_account_id)
        print(f"Updated balance of new account: {updated_balance} hbars")
        print("=" * 60 + "\n")

        print("✓ All operations completed successfully!")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
