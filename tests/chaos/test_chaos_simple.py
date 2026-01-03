"""
Chaos Engineering Test Suite for AstraGuard AI

Validates chaos engine can be initialized and configured.
Detailed chaos testing is done through integration tests.

Run with: pytest tests/chaos/ -v
"""

import pytest
from backend.chaos_engine import ChaosEngine


@pytest.mark.asyncio
async def test_chaos_engine_init():
    """Test ChaosEngine initialization."""
    engine = ChaosEngine()
    assert engine.base_url == "http://localhost:8000"
    assert engine.session is None
    assert not engine.chaos_active


@pytest.mark.asyncio
async def test_chaos_engine_custom_url():
    """Test ChaosEngine with custom URL."""
    engine = ChaosEngine(base_url="http://custom:9000")
    assert engine.base_url == "http://custom:9000"


@pytest.mark.asyncio
async def test_chaos_engine_startup():
    """Test ChaosEngine startup creates session."""
    engine = ChaosEngine()
    await engine.startup()
    assert engine.session is not None
    await engine.shutdown()


@pytest.mark.asyncio
async def test_chaos_engine_unknown_fault():
    """Test unknown fault type is rejected."""
    engine = ChaosEngine()
    await engine.startup()
    try:
        result = await engine.inject_faults("unknown_fault", duration_seconds=1)
        assert result is False
    finally:
        await engine.shutdown()
