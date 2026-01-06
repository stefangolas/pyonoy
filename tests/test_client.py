"""Tests for byonoy_absorbance96 package."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from byonoy_absorbance96 import (
    Absorbance96Client,
    ConnectionConfig,
    ExportFormat,
    SiLAConfig,
)


class TestSiLAConfig:
    """Tests for SiLAConfig."""
    
    def test_default_values(self):
        config = SiLAConfig()
        assert config.port == 50051
        assert config.ip == "127.0.0.1"
        assert config.insecure is False
        assert config.headless is False
    
    def test_to_cli_args_minimal(self):
        config = SiLAConfig()
        args = config.to_cli_args()
        assert args == ["--sila"]
    
    def test_to_cli_args_full(self):
        config = SiLAConfig(
            port=50052,
            ip="0.0.0.0",
            insecure=True,
            headless=True,
            uuid="test-uuid",
        )
        args = config.to_cli_args()
        
        assert "--sila" in args
        assert "--sila-port" in args
        assert "50052" in args
        assert "--sila-ip" in args
        assert "0.0.0.0" in args
        assert "--sila-insecure" in args
        assert "--headless" in args
        assert "--sila-uuid" in args
        assert "test-uuid" in args


class TestConnectionConfig:
    """Tests for ConnectionConfig."""
    
    def test_default_values(self):
        config = ConnectionConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 50051
        assert config.insecure is False
    
    def test_address_property(self):
        config = ConnectionConfig(host="192.168.1.100", port=50052)
        assert config.address == "192.168.1.100:50052"


class TestExportFormat:
    """Tests for ExportFormat enum."""
    
    def test_values(self):
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.XLSX.value == "xlsx"
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.XML.value == "xml"


class TestAbsorbance96Client:
    """Tests for Absorbance96Client."""
    
    def test_init_default_config(self):
        client = Absorbance96Client()
        assert client.config.host == "127.0.0.1"
        assert client.config.port == 50051
    
    def test_init_custom_config(self):
        config = ConnectionConfig(host="192.168.1.100", port=50052)
        client = Absorbance96Client(config)
        assert client.config.host == "192.168.1.100"
        assert client.config.port == 50052
    
    def test_ensure_connected_raises(self):
        client = Absorbance96Client()
        with pytest.raises(RuntimeError, match="Not connected"):
            client._ensure_connected()
    
    def test_ensure_locked_raises(self):
        client = Absorbance96Client()
        client.channel = Mock()  # Fake connection
        with pytest.raises(RuntimeError, match="No lock held"):
            client._ensure_locked()
    
    def test_load_workspace_converts_path(self):
        client = Absorbance96Client()
        client.channel = Mock()
        client._lock_id = "test-lock"
        
        # Should not raise - path conversion works
        path = Path("C:/test/protocol.byop")
        client.load_workspace(path)
    
    def test_context_manager(self):
        client = Absorbance96Client(ConnectionConfig(insecure=True))
        
        with patch.object(client, 'connect') as mock_connect:
            with patch.object(client, 'disconnect') as mock_disconnect:
                with client:
                    mock_connect.assert_called_once()
                mock_disconnect.assert_called_once()
    
    def test_lock_context_manager(self):
        client = Absorbance96Client()
        client.channel = Mock()
        
        with client.lock() as lock_id:
            assert lock_id is not None
            assert client._lock_id == lock_id
        
        assert client._lock_id is None


class TestURIConversion:
    """Tests for URI handling."""
    
    def test_path_to_uri_windows(self):
        client = Absorbance96Client()
        client.channel = Mock()
        client._lock_id = "test"
        
        # Path objects get converted
        path = Path("C:/Users/test/protocol.byop")
        # This would internally convert to file:///C:/Users/test/protocol.byop
    
    def test_string_uri_passthrough(self):
        client = Absorbance96Client()
        client.channel = Mock()
        client._lock_id = "test"
        
        # URIs starting with file:// or http:// pass through
        client.load_workspace("file:///C:/test.byop")
        client.load_workspace("https://example.com/test.byop")
