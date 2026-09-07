from __future__ import annotations

import re

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery


pytestmark = pytest.mark.integration

DEPRECATION_MESSAGE = (
    "Deprecated: AccountBalanceQuery will stop working when the Hedera network "
    "removes the CryptoGetBalance endpoint (estimated September 2026, consensus "
    "node release 77). Use the mirror node REST API to retrieve account balances."
)

UNSUPPORTED_OPERATION_MESSAGE = (
    "Error: AccountBalanceQuery is no longer supported. Use the mirror node REST API to retrieve account balances."
)


def test_integration_account_balance_query_raises_unsupported_operation():
    """Account balance query should warn on construction and fail before networking."""
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(DEPRECATION_MESSAGE),
    ):
        query = CryptoGetAccountBalanceQuery(account_id=AccountId(0, 0, 2))

    with pytest.raises(
        RuntimeError,
        match=re.escape(UNSUPPORTED_OPERATION_MESSAGE),
    ):
        query.execute(None)


def test_integration_contract_balance_query_raises_unsupported_operation():
    """Contract balance query should warn on construction and fail before networking."""
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(DEPRECATION_MESSAGE),
    ):
        query = CryptoGetAccountBalanceQuery(contract_id=ContractId(0, 0, 1234))

    with pytest.raises(
        RuntimeError,
        match=re.escape(UNSUPPORTED_OPERATION_MESSAGE),
    ):
        query.execute(None)


def test_integration_balance_query_raises_unsupported_operation_when_neither_source_set():
    """Execution should fail before validating account/contract source."""
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(DEPRECATION_MESSAGE),
    ):
        query = CryptoGetAccountBalanceQuery()

    with pytest.raises(
        RuntimeError,
        match=re.escape(UNSUPPORTED_OPERATION_MESSAGE),
    ):
        query.execute(None)


def test_integration_balance_query_invalid_account_id_still_raises_type_error():
    """Setter validation should still happen before execution."""
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(DEPRECATION_MESSAGE),
    ):
        query = CryptoGetAccountBalanceQuery()

    with pytest.raises(TypeError, match=r"account_id must be an AccountId\."):
        query.set_account_id("0.0.12345")


def test_integration_balance_query_invalid_contract_id_still_raises_type_error():
    """Setter validation should still happen before execution."""
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(DEPRECATION_MESSAGE),
    ):
        query = CryptoGetAccountBalanceQuery()

    with pytest.raises(TypeError, match=r"contract_id must be a ContractId\."):
        query.set_contract_id("0.0.12345")
