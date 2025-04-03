from hiero_sdk_python.transaction.transaction import Transaction 
from hiero_sdk_python.hapi.services import token_unfreeze_account_pb2
from hiero_sdk_python.response_code import ResponseCode

class TokenUnfreezeTransaction(Transaction):
    """
    Represents a token unfreeze transaction on the Hedera network.
    
    This transaction unfreezes specified tokens for a given account.
    
    Inherits from the base Transaction class and implements the required methods
    to build and execute a token unfreeze transaction.
    """

    def __init__(self, account_id=None, token_id=None):
        """
        Initializes a new TokenUnfreezeTransaction instance with default values.
        """
        super().__init__()
        self.token_id = token_id
        self.account_id = account_id
        self._default_transaction_fee = 3_000_000_000
        self._is_frozen = False 
    
    def set_token_id(self, token_id):
        self.__require_not_frozen()
        self.token_id = token_id
        return self
    
    def set_account_id(self, account_id):
        self.__require_not_frozen()
        self.account_id = account_id
        return self
    
    def __require_not_frozen(self): 
        if self._is_frozen:
            raise ValueError("Transaction is already frozen and cannot be modified.")

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token unfreeze.

        Returns:
            TransactionBody: The protobuf transaction body containing the token unfreeze details.
        
        Raises:
            ValueError: If account ID or token IDs are not set.
        
        """
        if not self.token_id:
            raise ValueError("Missing required TokenID.")

        if not self.account_id:
            raise ValueError("Missing required AccountID.")
        
        token_unfreeze_body = token_unfreeze_account_pb2.TokenUnfreezeAccountTransactionBody(
            account=self.account_id.to_proto(),
            token=self.token_id.to_proto()
        )

        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenUnfreeze.CopyFrom(token_unfreeze_body)

        return transaction_body
    
    def _execute_transaction(self, client, transaction_proto):
        """
        Executes the token unfreeze transaction using the provided client.
        Args:
            client (Client): The client instance to use for execution.
            transaction_proto (Transaction): The protobuf Transaction message.
        Returns:
            TransactionReceipt: The receipt from the network after transaction execution.
        Raises:
            Exception: If the transaction submission fails or receives an error response.
        """

        response = client.token_stub.unfreezeTokenAccount(transaction_proto)

        if response.nodeTransactionPrecheckCode != ResponseCode.OK:
            error_code = response.nodeTransactionPrecheckCode
            error_message = ResponseCode.get_name(error_code)
            raise Exception(f"Error during transaction submission: {error_code} ({error_message})")
        receipt = self.get_receipt(client)
        return receipt
    