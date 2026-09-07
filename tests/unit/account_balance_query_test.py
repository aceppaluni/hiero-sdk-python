"""Tests for the AccountBalanceQuery functionality."""

from __future__ import annotations

import re
import warnings

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery


pytestmark = pytest.mark.unit

DEPRECATION_MESSAGE = (
    "Deprecated: AccountBalanceQuery will stop working when the Hedera network "
    "removes the CryptoGetBalance endpoint (estimated September 2026, consensus "
    "node release 77). Use the mirror node REST API to retrieve account balances."
)

UNSUPPORTED_OPERATION_MESSAGE = (
    "Error: AccountBalanceQuery is no longer supported. Use the mirror node REST API to retrieve account balances."
)


# This test uses fixture mock_account_ids as parameter
def test_build_account_balance_query(mock_account_ids):
    """Test building a CryptoGetAccountBalanceQuery with a valid account ID."""
    account_id_sender, *_ = mock_account_ids

    with pytest.warns(
        DeprecationWarning,
        match=re.escape(DEPRECATION_MESSAGE),
    ):
        query = CryptoGetAccountBalanceQuery(account_id=account_id_sender)

    assert query.account_id == account_id_sender


def test_execute_account_balance_query_raises_unsupported_operation():
    """Test that executing the account balance query raises before network access."""
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(DEPRECATION_MESSAGE),
    ):
        query = CryptoGetAccountBalanceQuery().set_account_id(AccountId(0, 0, 1800))

    with pytest.raises(
        RuntimeError,
        match=re.escape(UNSUPPORTED_OPERATION_MESSAGE),
    ):
        query.execute(None)


def test_account_balance_query_does_not_require_payment():
    """Test that the account balance query does not require payment."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        query = CryptoGetAccountBalanceQuery()

    assert not query._is_payment_required()


def test_set_account_id_returns_self_for_chaining():
    """set_account_id should return self to enable method chaining."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        query = CryptoGetAccountBalanceQuery()

    account_id = AccountId(0, 0, 1800)

    result = query.set_account_id(account_id)

    assert result is query
    assert isinstance(result, CryptoGetAccountBalanceQuery)


def test_set_contract_id_returns_self_for_chaining():
    """set_contract_id should return self to enable method chaining."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        query = CryptoGetAccountBalanceQuery()

    contract_id = ContractId(0, 0, 1234)

    result = query.set_contract_id(contract_id)

    assert result is query
    assert isinstance(result, CryptoGetAccountBalanceQuery)


def test_set_account_id_with_invalid_type_raises():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        query = CryptoGetAccountBalanceQuery()

    with pytest.raises(TypeError, match=r"account_id must be an AccountId\."):
        query.set_account_id("ciao")


def test_set_contract_id_with_invalid_type_raises():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        query = CryptoGetAccountBalanceQuery()

    with pytest.raises(TypeError, match=r"contract_id must be a ContractId\."):
        query.set_contract_id("ciao")


def test_build_account_balance_query_with_contract_id():
    """Test building a CryptoGetAccountBalanceQuery with a valid contract ID."""
    contract_id = ContractId(0, 0, 1234)

    with pytest.warns(
        DeprecationWarning,
        match=re.escape(DEPRECATION_MESSAGE),
    ):
        query = CryptoGetAccountBalanceQuery(contract_id=contract_id)

    assert query.contract_id == contract_id
    assert query.account_id is None
    assert isinstance(query.contract_id, ContractId)
    assert hasattr(query, "contract_id")


def test_set_contract_id_method_chaining_resets_account_id(mock_account_ids):
    """set_contract_id should support chaining and reset account_id."""
    account_id_sender, *_ = mock_account_ids
    contract_id = ContractId(0, 0, 1234)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        query = CryptoGetAccountBalanceQuery()

    query.set_account_id(account_id_sender).set_contract_id(contract_id)

    assert query.contract_id == contract_id
    assert query.account_id is None


def test_last_wins_when_both_account_id_and_contract_id_are_set(
    mock_account_ids,
):
    """The last configured source should replace the previous one."""
    account_id_sender, *_ = mock_account_ids
    contract_id = ContractId(0, 0, 1234)

    with pytest.warns(
        DeprecationWarning,
        match=re.escape(DEPRECATION_MESSAGE),
    ):
        query = CryptoGetAccountBalanceQuery(
            account_id=account_id_sender,
            contract_id=contract_id,
        )

    assert query.contract_id == contract_id
    assert query.account_id is None


def test_make_request_when_neither_account_id_nor_contract_id_is_set():
    """_make_request should create request without ids when neither is set."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        query = CryptoGetAccountBalanceQuery()

    proto = query._make_request()

    assert not proto.cryptogetAccountBalance.HasField("accountID")
    assert not proto.cryptogetAccountBalance.HasField("contractID")


def test_make_request_populates_contract_id_only():
    """_make_request should populate contractID when only contract_id is set."""
    contract_id = ContractId(0, 0, 1234)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        query = CryptoGetAccountBalanceQuery().set_contract_id(contract_id)

    req = query._make_request()
    balance_query = req.cryptogetAccountBalance

    assert balance_query.contractID == contract_id._to_proto()
    assert not balance_query.HasField("accountID")


def test_make_request_populates_account_id_only(mock_account_ids):
    """_make_request should populate accountID when only account_id is set."""
    account_id_sender, *_ = mock_account_ids

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        query = CryptoGetAccountBalanceQuery().set_account_id(account_id_sender)

    req = query._make_request()
    balance_query = req.cryptogetAccountBalance

    assert balance_query.accountID == account_id_sender._to_proto()
    assert not balance_query.HasField("contractID")
