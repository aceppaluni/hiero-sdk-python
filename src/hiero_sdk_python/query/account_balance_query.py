from __future__ import annotations

import logging
import warnings
from typing import Any

from hiero_sdk_python.account.account_balance import AccountBalance
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import crypto_get_account_balance_pb2, query_pb2
from hiero_sdk_python.query.query import Query


logger = logging.getLogger(__name__)


class CryptoGetAccountBalanceQuery(Query):
    """
    Query an account's balance.

    .. deprecated::
        The CryptoGetBalance endpoint is scheduled for removal with the
        consensus node release 77 (estimated September 2026). Use the Mirror
        Node REST API to retrieve account balances instead.
    """

    def __init__(
        self,
        account_id: AccountId | None = None,
        contract_id: ContractId | None = None,
    ) -> None:
        warnings.warn(
            "Deprecated: AccountBalanceQuery will stop working when the Hedera network removes the CryptoGetBalance endpoint (estimated September 2026, consensus node release 77). Use the mirror node REST API to retrieve account balances.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__()
        self.account_id: AccountId | None = None
        self.contract_id: ContractId | None = None

        if account_id is not None:
            self.set_account_id(account_id)
        if contract_id is not None:
            self.set_contract_id(contract_id)

    def set_account_id(self, account_id: AccountId) -> CryptoGetAccountBalanceQuery:
        """
        Sets the account ID for which to retrieve the balance.
        Resets to None the contract ID.

        Args:
            account_id (AccountId): The ID of the account.

        Returns:
            CryptoGetAccountBalanceQuery: The current instance for method chaining.
        """
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId.")
        self.contract_id = None
        self.account_id = account_id
        return self

    def set_contract_id(self, contract_id: ContractId) -> CryptoGetAccountBalanceQuery:
        """
        Sets the contract ID for which to retrieve the balance.
        Resets to None the account ID.

        Args:
            contract_id (ContractId): The ID of the contract.

        Returns:
            CryptoGetAccountBalanceQuery: The current instance for method chaining.
        """
        if not isinstance(contract_id, ContractId):
            raise TypeError("contract_id must be a ContractId.")
        self.account_id = None
        self.contract_id = contract_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the account balance query.

        Returns:
            query_pb2.Query: The protobuf Query object containing the account balance query.

        Raises:
            ValueError: If both the account ID and contract ID are not set.
            ValueError: If both the account ID and contract ID are set.
            AttributeError: If the Query protobuf structure is invalid.
            Exception: If any other error occurs during request construction.
        """
        try:
            if self.account_id and self.contract_id:
                raise ValueError("Specify either account_id or contract_id, not both.")

            query_header = self._make_request_header()
            crypto_get_balance = crypto_get_account_balance_pb2.CryptoGetAccountBalanceQuery()
            crypto_get_balance.header.CopyFrom(query_header)

            if self.account_id is not None:
                crypto_get_balance.accountID.CopyFrom(self.account_id._to_proto())

            if self.contract_id is not None:
                crypto_get_balance.contractID.CopyFrom(self.contract_id._to_proto())

            query = query_pb2.Query()
            if not hasattr(query, "cryptogetAccountBalance"):
                raise AttributeError("Query object has no attribute 'cryptogetAccountBalance'")
            query.cryptogetAccountBalance.CopyFrom(crypto_get_balance)

            return query
        except Exception as e:
            logger.error("Exception in _make_request: %s", e, exc_info=True)
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the account balance query.

        Implements the abstract method from Query to provide the specific
        gRPC method for getting account balances.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(transaction_func=None, query_func=channel.crypto.cryptoGetBalance)

    def execute(self, client: Client, timeout: int | float | None = None) -> AccountBalance:
        """
        Execute the account balance query.

        .. deprecated::
            The CryptoGetBalance endpoint is scheduled for removal with the
            consensus node release 77 (estimated September 2026). Use the Mirror
            Node REST API to retrieve account balances instead.

        Raises:
            RuntimeError: Always, because the AccountBalanceQuery is no longer
                supported.
        """
        raise RuntimeError(
            "Error: AccountBalanceQuery is no longer supported. Use the mirror node REST API to retrieve account balances."
        )
        self._before_execute(client)
        response = self._execute(client, timeout)

        return AccountBalance._from_proto(response.cryptogetAccountBalance)

    def _get_query_response(self, response: Any) -> crypto_get_account_balance_pb2.CryptoGetAccountBalanceResponse:
        """
        Extracts the account balance response from the full response.

        Implements the abstract method from Query to extract the
        specific account balance response object.

        Args:
            response: The full response from the network

        Returns:
            The crypto get account balance response object
        """
        return response.cryptogetAccountBalance

    def _is_payment_required(self) -> bool:
        """
        Account balance query does not require payment.

        Returns:
            bool: False
        """
        return False
