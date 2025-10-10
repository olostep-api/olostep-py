#!/usr/bin/env python3
"""
Simple test to verify the logging module works without requiring aiohttp.
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logging_module():
    """Test that the logging module can be imported and basic functionality works."""
    from olostep.logging import OlostepLogger, get_io_logger, setup_logger_hierarchy
    from olostep.config import IO_LOG_PATH
    import logging
    
    print("✅ Successfully imported logging module")
    print(f"✅ IO_LOG_PATH config: {IO_LOG_PATH}")
    
    # Test logger hierarchy setup
    setup_logger_hierarchy()
    root_logger = logging.getLogger("olostep")
    io_logger = logging.getLogger("olostep.io")
    print(f"✅ Root logger: {root_logger.name}")
    print(f"✅ IO logger: {io_logger.name}")
    
    # Assert logger hierarchy is correct
    assert root_logger.name == "olostep"
    assert io_logger.name == "olostep.io"
    
    # Test creating a logger
    logger = OlostepLogger("test", "tests/runtime")
    print("✅ Successfully created OlostepLogger")
    print(f"✅ Logger name: {logger._logger.name}")
    
    # Assert logger name is correct
    assert logger._logger.name == "olostep.io.test"
    
    # Test logging methods (without actual HTTP calls)
    logger.log_request(
        "req_123",
        "POST",
        "https://api.example.com/v1/scrapes",
        {"test": "data"},
        {"param": "value"},
        {"Authorization": "Bearer secret"}
    )
    print("✅ Successfully logged request")
    
    logger.log_response(
        "req_123",
        200,
        {"Content-Type": "application/json"},
        '{"result": "success"}',
        1.5,
        "POST",
        "https://api.example.com/v1/scrapes"
    )
    print("✅ Successfully logged response")
    
    logger.log_error("req_123", "Connection timeout", 2.0, "POST", "https://api.example.com/v1/scrapes")
    print("✅ Successfully logged error")
    
    print("\n🎉 All logging tests passed!")
    print("📁 Check tests/runtime/ for the generated JSON log files")

if __name__ == "__main__":
    print("Testing logging module implementation...")
    print("=" * 50)
    
    try:
        test_logging_module()
        print("\n✅ Logging implementation is working correctly!")
    except Exception as e:
        print(f"\n❌ Logging implementation has issues: {e}")
        sys.exit(1)
