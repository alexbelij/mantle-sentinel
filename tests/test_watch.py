"""Tests for sentinel.watch — live monitoring helpers."""
from __future__ import annotations

from sentinel.watch import _bar, _status, _to_raw


class TestProgressBar:
    def test_full_bar(self):
        assert _bar(100) == "▓" * 11

    def test_empty_bar(self):
        assert _bar(0) == "░" * 11

    def test_half_bar(self):
        bar = _bar(50)
        assert "▓" in bar
        assert "░" in bar
        assert len(bar) == 11


class TestStatus:
    def test_ok(self):
        assert _status(90) == "OK"

    def test_elevated(self):
        assert "ELEVATED" in _status(60)

    def test_alert(self):
        assert "ALERT" in _status(30)


class TestToRaw:
    def test_converts_etherscan_format(self):
        txs = [{
            "blockNumber": "100",
            "timeStamp": "1700000000",
            "hash": "0xabc",
            "from": "0xSENDER",
            "to": "0xCONTRACT",
            "input": "0xa9059cbb" + "00" * 64,
            "gasUsed": "50000",
            "value": "0",
            "isError": "0",
        }]
        raw = _to_raw(txs, "0xCONTRACT")
        assert len(raw) == 1
        assert raw[0]["block_number"] == 100
        assert raw[0]["contract"] == "0xcontract"
        assert raw[0]["selector"] == "0xa9059cbb"

    def test_filters_errors(self):
        txs = [{
            "blockNumber": "100",
            "timeStamp": "1700000000",
            "hash": "0xabc",
            "from": "0xSENDER",
            "to": "0xCONTRACT",
            "input": "0xa9059cbb" + "00" * 64,
            "gasUsed": "50000",
            "value": "0",
            "isError": "1",
        }]
        raw = _to_raw(txs, "0xCONTRACT")
        assert len(raw) == 0

    def test_filters_wrong_target(self):
        txs = [{
            "blockNumber": "100",
            "timeStamp": "1700000000",
            "hash": "0xabc",
            "from": "0xSENDER",
            "to": "0xOTHER",
            "input": "0xa9059cbb" + "00" * 64,
            "gasUsed": "50000",
            "value": "0",
            "isError": "0",
        }]
        raw = _to_raw(txs, "0xCONTRACT")
        assert len(raw) == 0
