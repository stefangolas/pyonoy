"""
Byonoy Absorbance 96 SiLA2 Client

A Python client for controlling the Absorbance 96 plate reader via SiLA2.
"""

import grpc
import uuid
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "Absorbance96Client",
    "ConnectionConfig",
    "ExportFormat",
    "run_assay",
]


class ExportFormat(Enum):
    """Supported export formats for results."""
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"
    XML = "xml"


@dataclass
class ConnectionConfig:
    """Configuration for connecting to the SiLA2 server."""
    
    host: str = "127.0.0.1"
    port: int = 50051
    insecure: bool = False
    cert_path: Optional[Path] = None
    
    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


class Absorbance96Client:
    """
    Client for controlling Byonoy Absorbance 96 via SiLA2.
    
    The Absorbance 96 exposes two SiLA2 features:
    - LockController (standard SiLA2 feature for exclusive access)
    - ApplicationController (device-specific commands)
    
    All ApplicationController commands require a valid lock ID.
    
    Example:
        >>> client = Absorbance96Client()
        >>> client.connect()
        >>> 
        >>> with client.lock():
        ...     client.load_workspace("file:///C:/protocols/assay.byop")
        ...     client.prepare_for_readout()
        ...     # Insert plate into reader
        ...     client.perform_readout()
        ...     # Remove plate
        ...     results = client.get_results(format=ExportFormat.CSV)
        >>> 
        >>> client.disconnect()
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self.channel: Optional[grpc.Channel] = None
        self._lock_id: Optional[str] = None
    
    def connect(self) -> None:
        """Establish connection to the SiLA2 server."""
        if self.config.insecure:
            self.channel = grpc.insecure_channel(self.config.address)
        else:
            if self.config.cert_path:
                with open(self.config.cert_path, 'rb') as f:
                    credentials = grpc.ssl_channel_credentials(f.read())
            else:
                credentials = grpc.ssl_channel_credentials()
            self.channel = grpc.secure_channel(self.config.address, credentials)
        
        try:
            grpc.channel_ready_future(self.channel).result(timeout=10)
        except grpc.FutureTimeoutError:
            raise ConnectionError(
                f"Could not connect to SiLA2 server at {self.config.address}"
            )
    
    def disconnect(self) -> None:
        """Close the connection to the SiLA2 server."""
        if self.channel:
            self.channel.close()
            self.channel = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
    
    def _ensure_connected(self) -> None:
        if self.channel is None:
            raise RuntimeError("Not connected. Call connect() first.")
    
    def _ensure_locked(self) -> str:
        if self._lock_id is None:
            raise RuntimeError("No lock held. Use lock() context manager or acquire_lock().")
        return self._lock_id
    
    # ========== LockController Feature ==========
    
    def acquire_lock(self, timeout_seconds: float = 30.0) -> str:
        """
        Acquire exclusive lock on the device.
        
        Returns:
            Lock ID string to use with subsequent commands
        """
        self._ensure_connected()
        # TODO: Call LockController/Lock via gRPC
        self._lock_id = str(uuid.uuid4())
        return self._lock_id
    
    def release_lock(self) -> None:
        """Release the exclusive lock on the device."""
        self._ensure_connected()
        if self._lock_id:
            # TODO: Call LockController/Unlock via gRPC
            self._lock_id = None
    
    def lock(self) -> "_LockContext":
        """Context manager for automatic lock acquisition and release."""
        return _LockContext(self)
    
    # ========== ApplicationController Feature ==========
    
    def load_workspace(self, uri: Union[str, Path]) -> None:
        """
        Load an assay/protocol file from the given URI.
        
        Args:
            uri: File URI or HTTP URL to the .byop protocol file.
                 Local files should use file:// scheme:
                 - Windows: file:///C:/Users/user/protocol.byop
                 - macOS/Linux: file:///home/user/protocol.byop
                 HTTP URLs are also supported.
        """
        self._ensure_connected()
        lock_id = self._ensure_locked()
        
        if isinstance(uri, Path):
            uri = uri.resolve().as_uri()
        elif not uri.startswith(('file://', 'http://', 'https://')):
            uri = Path(uri).resolve().as_uri()
        
        # TODO: Call ApplicationController/LoadWorkspace via gRPC
        # Metadata: lock_id
    
    def prepare_for_readout(self) -> None:
        """
        Prepare the reader for measurement.
        
        Checks connection to the reader, reader status, and compatibility
        of the loaded assay. After successful completion, the plate can be
        inserted into the reader.
        
        Requires: load_workspace() must be called first.
        """
        self._ensure_connected()
        lock_id = self._ensure_locked()
        # TODO: Call ApplicationController/PrepareForReadout via gRPC
    
    def perform_readout(self) -> None:
        """
        Perform the measurement as defined by the loaded protocol.
        
        After successful completion, the plate can be removed from the reader.
        
        Requires: prepare_for_readout() must be called first.
        """
        self._ensure_connected()
        lock_id = self._ensure_locked()
        # TODO: Call ApplicationController/PerformReadout via gRPC
    
    def export_results(
        self,
        output_path: Union[str, Path],
        format: ExportFormat = ExportFormat.CSV,
    ) -> None:
        """
        Export measurement results to a file on the server machine.
        
        Args:
            output_path: Path on the server where results will be saved
            format: Export format (CSV, XLSX, JSON, XML). Note: PDF not available.
            
        Requires: perform_readout() must be called first.
        """
        self._ensure_connected()
        lock_id = self._ensure_locked()
        
        if isinstance(output_path, str):
            output_path = Path(output_path)
        
        # TODO: Call ApplicationController/ExportResults via gRPC
    
    def get_results(self, format: ExportFormat = ExportFormat.CSV) -> bytes:
        """
        Retrieve measurement results as binary data.
        
        Args:
            format: Export format (CSV, XLSX, JSON, XML). Note: PDF not available.
            
        Returns:
            Binary data of the results file
            
        Requires: perform_readout() must be called first.
        """
        self._ensure_connected()
        lock_id = self._ensure_locked()
        # TODO: Call ApplicationController/GetResults via gRPC
        return b""
    
    def quit_application(self) -> None:
        """
        Shut down the Absorbance 96 application.
        
        This is the only way to close the app when running in headless mode.
        """
        self._ensure_connected()
        lock_id = self._ensure_locked()
        # TODO: Call ApplicationController/QuitApplication via gRPC


class _LockContext:
    """Context manager for SiLA2 lock acquisition."""
    
    def __init__(self, client: Absorbance96Client):
        self.client = client
        self.lock_id: Optional[str] = None
    
    def __enter__(self) -> str:
        self.lock_id = self.client.acquire_lock()
        return self.lock_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.release_lock()
        return False


def run_assay(
    protocol_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    output_format: ExportFormat = ExportFormat.CSV,
    host: str = "127.0.0.1",
    port: int = 50051,
    insecure: bool = False,
    interactive: bool = True,
) -> Optional[bytes]:
    """
    High-level function to run a complete assay workflow.
    
    Args:
        protocol_path: Path or URI to the .byop protocol file
        output_path: If provided, export results to this path on the server
        output_format: Format for results export
        host: SiLA2 server host
        port: SiLA2 server port
        insecure: Whether to use insecure connection
        interactive: If True, prompt user for plate insertion/removal
        
    Returns:
        If output_path is None, returns the results as bytes.
        Otherwise returns None (results are saved to file).
    """
    config = ConnectionConfig(host=host, port=port, insecure=insecure)
    
    with Absorbance96Client(config) as client:
        with client.lock():
            client.load_workspace(protocol_path)
            client.prepare_for_readout()
            
            if interactive:
                input("Press Enter when plate is inserted...")
            
            client.perform_readout()
            
            if interactive:
                input("Press Enter when plate is removed...")
            
            if output_path:
                client.export_results(output_path, output_format)
                return None
            else:
                return client.get_results(output_format)
