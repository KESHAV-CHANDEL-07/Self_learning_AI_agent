import pytest
from unittest.mock import patch, MagicMock
from agent.daemon import DaemonWatcher
import signal

def test_daemon_shutdown():
    watcher = DaemonWatcher("/tmp")
    
    with patch("agent.daemon.Observer") as MockObserver:
        mock_observer = MockObserver.return_value
        watcher.observer = mock_observer
        
        watcher.shutdown(signal.SIGINT, None)
        
        assert not watcher.running
        mock_observer.stop.assert_called_once()


def test_daemon_crash_recovery_and_exit():
    watcher = DaemonWatcher("/tmp", poll_interval=0)
    
    with patch("agent.daemon.Observer") as MockObserver, patch("time.sleep") as mock_sleep:
        mock_observer = MockObserver.return_value
        mock_observer.start.side_effect = [Exception("Crash 1"), Exception("Crash 2"), Exception("Crash 3")]
        
        watcher.start()
        
        assert watcher.crash_count == 3
        assert not watcher.running
        # It should sleep twice for backoff on crashes 1 and 2
        assert mock_sleep.call_count == 2
