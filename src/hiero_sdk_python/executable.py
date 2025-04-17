import time
import typing
import grpc
from abc import ABC, abstractmethod
from enum import IntEnum

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.exceptions import MaxAttemptsError

if typing.TYPE_CHECKING:
    from hiero_sdk_python.client.client import Client

# Default values for retry and backoff configuration in miliseconds
DEFAULT_MAX_BACKOFF: int = 8000
DEFAULT_MIN_BACKOFF: int = 250
DEFAULT_GRPC_DEADLINE: int = 10000


class _Method:
    """
    Wrapper class for gRPC methods used in transactions and queries.

    This class serves as a container for both transaction and query functions,
    allowing the execution system to handle both types uniformly.
    Each transaction or query type will provide its specific implementation
    via the _get_method() function.
    """

    def __init__(
        self,
        query_func: typing.Callable = None,
        transaction_func: typing.Callable = None,
    ):
        """
        Initialize a Method instance with the appropriate callable functions.

        Args:
            query_func (Callable): The gRPC stub method to call for queries
            transaction_func (Callable): The gRPC stub method to call for transactions
        """
        self.query = query_func
        self.transaction = transaction_func


class _ExecutionState(IntEnum):
    """
    Enum representing the possible states of transaction execution.

    These states are used to determine how to handle the response
    from a transaction execution attempt.
    """

    RETRY = 0  # The transaction should be retried
    FINISHED = 1  # The transaction completed successfully
    ERROR = 2  # The transaction failed with an error
    EXPIRED = 3  # The transaction expired before being processed


class _Executable(ABC):
    """
    Abstract base class for all executable operations (transactions and queries).
    
    This class defines the core interface for operations that can be executed on the
    Hedera network. It provides implementations for configuration properties with
    validation (max_backoff, min_backoff, grpc_deadline) and includes
    the execution flow with retry logic.
    
    Subclasses like Transaction and Query will extend this and implement the abstract methods
    to define specific behavior for different types of operations.
    """

    def __init__(self):
        self._max_backoff = DEFAULT_MAX_BACKOFF
        self._min_backoff = DEFAULT_MIN_BACKOFF
        self._grpc_deadline = DEFAULT_GRPC_DEADLINE
        self.node_account_id = None

    @abstractmethod
    def _should_retry(self, response) -> _ExecutionState:
        """
        Determine whether the operation should be retried based on the response.

        Args:
            response: The response from the network

        Returns:
            _ExecutionState: The execution state indicating what to do next
        """
        raise NotImplementedError("_should_retry must be implemented by subclasses")

    @abstractmethod
    def _map_status_error(self, response):
        """
        Maps a response status code to an appropriate error object.
    
        Args:
            response: The response from the network
        
        Returns:
            Exception: An error object representing the error status
        """
        raise NotImplementedError("_map_status_error must be implemented by subclasses")

    @abstractmethod
    def _make_request(self):
        """
        Build the request object to send to the network.

        Returns:
            The request protobuf object
        """
        raise NotImplementedError("_make_request must be implemented by subclasses")

    @abstractmethod
    def _get_method(self, channel: _Channel) -> _Method:
        """
        Get the appropriate gRPC method to call for this operation.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the appropriate callable
        """
        raise NotImplementedError("_get_method must be implemented by subclasses")

    @abstractmethod
    def _map_response(self, response, node_id, proto_request):
        """
        Map the network response to the appropriate response object.

        Args:
            response: The response from the network
            node_id: The ID of the node that processed the request
            proto_request: The protobuf request that was sent

        Returns:
            The appropriate response object for the operation
        """
        raise NotImplementedError("_map_response must be implemented by subclasses")

    def _execute(self, client: "Client"):
        """
        Execute a transaction or query with retry logic.

        Args:
            client (Client): The client instance to use for execution

        Returns:
            The response from executing the operation:
                - TransactionResponse: For transaction operations
                - Response: For query operations

        Raises:
            PrecheckError: If the operation fails with a non-retryable error
            MaxAttemptsError: If the operation fails after the maximum number of attempts
            ReceiptStatusError: If the operation fails with a receipt status error
        """
        # Determine maximum number of attempts from client or executable
        max_attempts = client.max_attempts
        current_backoff = self._min_backoff
        err_persistant = None

        for attempt in range(max_attempts):
            # Exponential backoff for retries
            if attempt > 0 and current_backoff < self._max_backoff:
                current_backoff *= 2

            # Create a channel wrapper from the client's channel
            channel = _Channel(client.channel)
            
            # Set the node account id to the client's node account id
            self.node_account_id = client.node_account_id

            # Get the appropriate gRPC method to call
            method = self._get_method(channel)

            # Build the request using the executable's _make_request method
            proto_request = self._make_request()

            try:
                # Execute the transaction method with the protobuf request
                response = _execute_method(method, proto_request)
                
                # Map the response to an error
                status_error = self._map_status_error(response)
                
                # Determine if we should retry based on the response
                execution_state = self._should_retry(response)
                
                # Handle the execution state
                match execution_state:
                    case _ExecutionState.RETRY:
                        # If we should retry, wait for the backoff period and try again
                        err_persistant = status_error
                        _delay_for_attempt(current_backoff)
                        continue
                    case _ExecutionState.EXPIRED:
                        raise status_error
                    case _ExecutionState.ERROR:
                        raise status_error
                    case _ExecutionState.FINISHED:
                        # If the transaction completed successfully, map the response and return it
                        return self._map_response(response, client.node_account_id, proto_request)
            except grpc.RpcError as e:
                # Save the error
                err_persistant = f"Status: {e.code()}, Details: {e.details()}"
                # Switch to a different node for the next attempt
                node_account_ids = client.get_node_account_ids()
                node_index = (attempt + 1) % len(node_account_ids)
                current_node_account_id = node_account_ids[node_index]
                client._switch_node(current_node_account_id)
                continue
        
        raise MaxAttemptsError("Exceeded maximum attempts for request", client.node_account_id, err_persistant)


def _delay_for_attempt(current_backoff: int):
    """
    Delay for the specified backoff period before retrying.

    Args:
        attempt (int): The current attempt number (0-based)
        current_backoff (int): The current backoff period in milliseconds
    """
    time.sleep(current_backoff * 0.001)

def _execute_method(method, proto_request):
    """
    Executes either a transaction or query method with the given protobuf request.

    Args:
        method (_Method): The method wrapper containing either a transaction or query function
        proto_request: The protobuf request object to pass to the method

    Returns:
        The response from executing the method

    Raises:
        Exception: If neither a transaction nor query method is available to execute
    """
    if method.transaction is not None:
        return method.transaction(proto_request)
    elif method.query is not None:
        return method.query(proto_request)
    raise Exception("No method to execute")