"""
Byonoy Absorbance 96 SiLA2 Server Launcher

Utility to start the Absorbance 96 App with SiLA2 server enabled.
"""

import subprocess
import platform
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

__all__ = ["SiLAConfig", "launch_sila_server", "find_absorbance96_app"]


@dataclass
class SiLAConfig:
    """Configuration for SiLA2 server startup."""
    
    port: int = 50051
    ip: str = "127.0.0.1"
    insecure: bool = False
    headless: bool = False
    uuid: Optional[str] = None
    ca_cert: Optional[Path] = None
    cert: Optional[Path] = None
    key: Optional[Path] = None
    out_cert: Optional[Path] = None

    def to_cli_args(self) -> list[str]:
        """Convert config to CLI arguments."""
        args = ["--sila"]
        
        if self.port != 50051:
            args.extend(["--sila-port", str(self.port)])
        if self.ip != "127.0.0.1":
            args.extend(["--sila-ip", self.ip])
        if self.insecure:
            args.append("--sila-insecure")
        if self.headless:
            args.append("--headless")
        if self.uuid:
            args.extend(["--sila-uuid", self.uuid])
        if self.ca_cert:
            args.extend(["--sila-ca-cert", str(self.ca_cert)])
        if self.cert:
            args.extend(["--sila-cert", str(self.cert)])
        if self.key:
            args.extend(["--sila-key", str(self.key)])
        if self.out_cert:
            args.extend(["--sila-out-cert", str(self.out_cert)])
        
        return args


def find_absorbance96_app() -> Optional[Path]:
    """
    Attempt to locate the Absorbance 96 App installation.
    
    Returns:
        Path to the executable if found, None otherwise.
    """
    system = platform.system()
    
    if system == "Windows":
        candidates = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Byonoy" / "Absorbance 96 App" / "app" / "absorbance96app.exe",
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Byonoy" / "Absorbance 96 App" / "app" / "absorbance96app.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Byonoy" / "Absorbance 96 App" / "app" / "absorbance96app.exe",
        ]
    elif system == "Darwin":
        candidates = [
            Path("/Applications/Absorbance 96 App.app"),
            Path.home() / "Applications" / "Absorbance 96 App.app",
        ]
    else:
        return None
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def launch_sila_server(
    config: Optional[SiLAConfig] = None,
    app_path: Optional[Path] = None,
    wait: bool = False,
) -> subprocess.Popen:
    """
    Launch the Absorbance 96 App with SiLA2 server enabled.
    
    Args:
        config: SiLA server configuration (uses defaults if None)
        app_path: Path to the application (auto-detected if None)
        wait: If True, wait for the process to complete
        
    Returns:
        The subprocess.Popen object for the launched application
        
    Raises:
        FileNotFoundError: If the application cannot be found
        OSError: If running on an unsupported operating system
    """
    if config is None:
        config = SiLAConfig()
    
    if app_path is None:
        app_path = find_absorbance96_app()
        if app_path is None:
            raise FileNotFoundError(
                "Could not find Absorbance 96 App. Please specify the path manually."
            )
    
    system = platform.system()
    cli_args = config.to_cli_args()
    
    if system == "Windows":
        cmd = [str(app_path)] + cli_args
    elif system == "Darwin":
        cmd = ["open", str(app_path), "--args"] + cli_args
    else:
        raise OSError(f"Unsupported operating system: {system}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    if wait:
        process.wait()
    
    return process
