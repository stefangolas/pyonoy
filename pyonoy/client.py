"""
Byonoy Absorbance 96 SiLA2 Client

A Python client for controlling the Absorbance 96 plate reader via SiLA2.

Note: The Byonoy SiLA2 server consumes the lock on each command.
Each ApplicationController call requires a fresh LockServer() call beforehand.
"""

import time
import uuid
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass
from enum import Enum

from sila2.client import SilaClient

__all__ = [
    "Absorbance96Client",
    "ConnectionConfig",
    "ExportFormat",
    "run_assay",
]


class ExportFormat(Enum):
    """Supported export formats for results."""
    CSV = "CSV-en"
    CSV_DE = "CSV-de"
    PDF = "PDF"


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

    The Byonoy server consumes the lock after each command, so a fresh
    lock is acquired automatically before every ApplicationController call.

    Example:
        >>> client = Absorbance96Client()
        >>> client.connect()
        >>> client.load_workspace("file:///C:/protocols/assay.byoa")
        >>> client.prepare_for_readout()
        >>> # Insert plate into reader
        >>> client.perform_readout()
        >>> # Remove plate
        >>> results = client.get_results(format=ExportFormat.CSV)
        >>> client.disconnect()
    """

    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self._client: Optional[SilaClient] = None
        self._lock_id: str = str(uuid.uuid4())
        self._lock_timeout: int = 100

    def connect(self, retries: int = 10, retry_delay: float = 2.0) -> None:
        """Establish connection to the SiLA2 server.

        Args:
            retries: Number of connection attempts before giving up.
            retry_delay: Seconds to wait between attempts.
        """
        root_certs = None
        if not self.config.insecure and self.config.cert_path:
            root_certs = self.config.cert_path.read_bytes()

        for attempt in range(1, retries + 1):
            try:
                self._client = SilaClient(
                    self.config.host,
                    self.config.port,
                    insecure=self.config.insecure,
                    root_certs=root_certs,
                )
                return
            except Exception:
                if attempt == retries:
                    raise
                time.sleep(retry_delay)

    def disconnect(self) -> None:
        """Close the connection to the SiLA2 server."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False

    def _ensure_connected(self) -> SilaClient:
        if self._client is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._client

    def _lock_and_metadata(self) -> list:
        """Acquire a fresh lock and return metadata for the command.

        The Byonoy server may or may not auto-release the lock after a
        command. We unlock first (ignoring errors if not locked), then
        re-lock to ensure a clean state before each command.
        """
        client = self._ensure_connected()
        try:
            client.LockController.UnlockServer(LockIdentifier=self._lock_id)
        except Exception:
            pass
        client.LockController.LockServer(
            LockIdentifier=self._lock_id,
            Timeout=self._lock_timeout,
        )
        return [client.LockController.LockIdentifier(self._lock_id)]

    # ========== ApplicationController Feature ==========

    def load_workspace(self, uri: Union[str, Path]) -> None:
        """
        Load an assay/protocol file from the given URI.

        Args:
            uri: File URI or HTTP URL to the protocol file.
                 Local files should use file:// scheme:
                 - Windows: file:///C:/Users/user/protocol.byoa
                 - macOS/Linux: file:///home/user/protocol.byoa
                 HTTP URLs are also supported.
        """
        client = self._ensure_connected()

        if isinstance(uri, Path):
            uri = uri.resolve().as_uri()
        elif not uri.startswith(('file://', 'http://', 'https://')):
            uri = Path(uri).resolve().as_uri()

        metadata = self._lock_and_metadata()
        instance = client.ApplicationController.LoadWorkspace(uri, metadata=metadata)
        instance.get_responses()

    def prepare_for_readout(self) -> None:
        """
        Prepare the reader for measurement.

        Checks connection to the reader, reader status, and compatibility
        of the loaded assay. After successful completion, the plate can be
        inserted into the reader.

        Requires: load_workspace() must be called first.
        """
        client = self._ensure_connected()
        metadata = self._lock_and_metadata()
        instance = client.ApplicationController.PrepareForReadout(metadata=metadata)
        instance.get_responses()

    def perform_readout(self) -> None:
        """
        Perform the measurement as defined by the loaded protocol.

        After successful completion, the plate can be removed from the reader.

        Requires: prepare_for_readout() must be called first.
        """
        client = self._ensure_connected()
        metadata = self._lock_and_metadata()
        instance = client.ApplicationController.PerformReadout(metadata=metadata)
        instance.get_responses()

    def export_results(
        self,
        output_path: Union[str, Path],
        format: ExportFormat = ExportFormat.CSV,
    ) -> None:
        """
        Export measurement results to a file on the server machine.

        Args:
            output_path: Path on the server where results will be saved
            format: Export format (CSV, PDF).

        Requires: perform_readout() must be called first.
        """
        client = self._ensure_connected()

        if isinstance(output_path, Path):
            output_path = str(output_path)

        metadata = self._lock_and_metadata()
        instance = client.ApplicationController.ExportResults(
            format.value, output_path, metadata=metadata
        )
        instance.get_responses()

    def get_results(self, format: ExportFormat = ExportFormat.CSV) -> bytes:
        """
        Retrieve measurement results as binary data.

        Args:
            format: Export format (CSV, PDF).

        Returns:
            Binary data of the results file

        Requires: perform_readout() must be called first.
        """
        client = self._ensure_connected()
        metadata = self._lock_and_metadata()
        return client.ApplicationController.GetResults(format.value, metadata=metadata)

    def quit_application(self) -> None:
        """
        Shut down the Absorbance 96 application.

        This is the only way to close the app when running in headless mode.
        """
        client = self._ensure_connected()
        metadata = self._lock_and_metadata()
        client.ApplicationController.QuitApplication(metadata=metadata)


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
        protocol_path: Path or URI to the protocol file
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
