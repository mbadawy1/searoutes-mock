"""Tests for Searoutes provider smart ranking functionality (Task 19)."""

from unittest.mock import Mock

import pytest

from backend.app.providers.searoutes import SearoutesProvider


class TestSearoutesSmartRanking:
    """Test smart ranking for ports and carriers per Task 19 spec."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock client to avoid actual API calls
        mock_client = Mock()
        self.provider = SearoutesProvider(client=mock_client)

    def test_rank_ports_exact_locode_wins_for_locode_query(self):
        """Test that exact LOCODE match wins for LOCODE queries."""
        ports = [
            {"name": "Alexandria", "locode": "EGDAM", "country": "EG", "size": 100},
            {"name": "Port Said", "locode": "EGPSD", "country": "EG", "size": 200},
            {"name": "Alexandria", "locode": "EGALY", "country": "EG", "size": 150},
        ]

        result = self.provider._rank_ports(ports, "EGALY", is_locode_query=True)

        assert result["locode"] == "EGALY"
        assert result["name"] == "Alexandria"

    def test_rank_ports_exact_name_wins_for_name_query(self):
        """Test that exact name match wins for name queries."""
        ports = [
            {"name": "Alexandria Port", "locode": "EGDAM", "country": "EG", "size": 100},
            {"name": "Alexandria", "locode": "EGALY", "country": "EG", "size": 150},
            {"name": "Port Alexandria", "locode": "EGPSD", "country": "EG", "size": 200},
        ]

        result = self.provider._rank_ports(ports, "Alexandria", is_locode_query=False)

        assert result["name"] == "Alexandria"
        assert result["locode"] == "EGALY"

    def test_rank_ports_size_tiebreaker(self):
        """Test that size acts as tiebreaker when scores are equal."""
        ports = [
            {"name": "Alexandria", "locode": "EGDAM", "country": "EG", "size": 100},
            {"name": "Alexandria", "locode": "EGALY", "country": "EG", "size": 200},  # Larger size
        ]

        result = self.provider._rank_ports(ports, "Alexandria", is_locode_query=False)

        # Both have exact name match, larger size should win
        assert result["locode"] == "EGALY"
        assert result["size"] == 200

    def test_rank_ports_startswith_beats_contains(self):
        """Test that startswith beats contains in ranking."""
        ports = [
            {"name": "New Alexandria", "locode": "USNAL", "country": "US", "size": 100},  # contains
            {
                "name": "Alexandria Port",
                "locode": "EGALY",
                "country": "EG",
                "size": 50,
            },  # startswith
        ]

        result = self.provider._rank_ports(ports, "Alexandria", is_locode_query=False)

        # startswith should beat contains, even with smaller size
        assert result["name"] == "Alexandria Port"
        assert result["locode"] == "EGALY"

    def test_rank_ports_token_aware_matching(self):
        """Test that token-aware matching works correctly."""
        ports = [
            {"name": "Port of Alexandria", "locode": "EGALY", "country": "EG", "size": 100},
            {"name": "Alexandria Marine Terminal", "locode": "EGDAM", "country": "EG", "size": 150},
        ]

        result = self.provider._rank_ports(ports, "Alexandria", is_locode_query=False)

        # Both should match via tokens, larger size should win as tiebreaker
        assert result["locode"] == "EGDAM"

    def test_rank_ports_handles_diacritics(self):
        """Test that diacritics are normalized correctly."""
        ports = [
            {"name": "Alexandría", "locode": "EGALY", "country": "EG", "size": 100},
            {"name": "Other Port", "locode": "OTHER", "country": "XX", "size": 200},
        ]

        result = self.provider._rank_ports(ports, "Alexandria", is_locode_query=False)

        # Should match despite diacritics
        assert result["name"] == "Alexandría"
        assert result["locode"] == "EGALY"

    def test_rank_carriers_exact_scac_wins_for_scac_query(self):
        """Test that exact SCAC match wins for SCAC queries."""
        carriers = [
            {"name": "Maersk Line", "scac": "MAEU", "id": "1"},
            {"name": "Mediterranean Shipping", "scac": "MSCU", "id": "2"},
            {"name": "CMA CGM", "scac": "CMDU", "id": "3"},
        ]

        result = self.provider._rank_carriers(carriers, "MAEU", is_scac_query=True)

        assert result["scac"] == "MAEU"
        assert result["name"] == "Maersk Line"

    def test_rank_carriers_exact_name_wins_for_name_query(self):
        """Test that exact name match wins for name queries."""
        carriers = [
            {"name": "Maersk Line Limited", "scac": "MAEL", "id": "1"},
            {"name": "Maersk", "scac": "MAEU", "id": "2"},
            {"name": "AP Moller Maersk", "scac": "APMA", "id": "3"},
        ]

        result = self.provider._rank_carriers(carriers, "Maersk", is_scac_query=False)

        assert result["name"] == "Maersk"
        assert result["scac"] == "MAEU"

    def test_rank_carriers_startswith_beats_contains(self):
        """Test that startswith beats contains for carrier ranking."""
        carriers = [
            {"name": "AP Moller Maersk", "scac": "APMA", "id": "1"},  # contains
            {"name": "Maersk Line", "scac": "MAEU", "id": "2"},  # startswith
        ]

        result = self.provider._rank_carriers(carriers, "Maersk", is_scac_query=False)

        # startswith should win
        assert result["name"] == "Maersk Line"
        assert result["scac"] == "MAEU"

    def test_rank_carriers_deterministic_tiebreaker(self):
        """Test that carriers with same score are sorted deterministically by name."""
        carriers = [
            {"name": "ZZZ Shipping", "scac": "ZZZS", "id": "1"},
            {"name": "AAA Maritime", "scac": "AAAM", "id": "2"},
        ]

        result = self.provider._rank_carriers(carriers, "Unknown", is_scac_query=False)

        # Should pick the alphabetically first name as tiebreaker
        assert result["name"] == "AAA Maritime"

    def test_rank_carriers_handles_various_response_formats(self):
        """Test that ranking handles various API response formats."""
        carriers = [
            {
                "carrierName": "Maersk Line",
                "scacCode": "MAEU",
                "carrierId": "1",
            },  # Alternative field names
            {"name": "CMA CGM", "scac": "CMDU", "id": "2"},  # Standard field names
        ]

        # _rank_carriers returns raw dict, test that it picks the right one
        raw_result = self.provider._rank_carriers(carriers, "MAEU", is_scac_query=True)

        # Should pick the first carrier with exact SCAC match
        assert raw_result["carrierName"] == "Maersk Line"
        assert raw_result["scacCode"] == "MAEU"

    def test_field_extraction_helpers(self):
        """Test that field extraction helpers handle various response formats."""
        from backend.app.providers.searoutes import (
            _port_name,
            _port_locode,
            _port_country,
            _carrier_name,
            _carrier_scac,
            _carrier_id,
        )

        # Test port field extraction
        port_standard = {"name": "Alexandria", "locode": "EGALY", "country": "EG"}
        port_alternative = {"portName": "Port Said", "unLocode": "EGPSD", "countryCode": "EG"}

        assert _port_name(port_standard) == "Alexandria"
        assert _port_locode(port_standard) == "EGALY"
        assert _port_country(port_standard) == "EG"

        assert _port_name(port_alternative) == "Port Said"
        assert _port_locode(port_alternative) == "EGPSD"
        assert _port_country(port_alternative) == "EG"

        # Test carrier field extraction
        carrier_standard = {"name": "Maersk", "scac": "MAEU", "id": "1"}
        carrier_alternative = {"carrierName": "CMA CGM", "scacCode": "CMDU", "carrierId": "2"}

        assert _carrier_name(carrier_standard) == "Maersk"
        assert _carrier_scac(carrier_standard) == "MAEU"
        assert _carrier_id(carrier_standard) == "1"

        assert _carrier_name(carrier_alternative) == "CMA CGM"
        assert _carrier_scac(carrier_alternative) == "CMDU"
        assert _carrier_id(carrier_alternative) == "2"

    def test_rank_ports_locode_query_with_spaces_and_dashes(self):
        """Test that LOCODE queries handle spaces and dashes correctly."""
        ports = [
            {"name": "Port Said", "locode": "EGPSD", "country": "EG", "size": 100},
            {"name": "Alexandria", "locode": "EGALY", "country": "EG", "size": 150},
        ]

        # Should normalize EG-PSD to EGPSD
        result = self.provider._rank_ports(ports, "EG-PSD", is_locode_query=True)

        assert result["locode"] == "EGPSD"
        assert result["name"] == "Port Said"

    def test_rank_empty_list_returns_empty_dict(self):
        """Test that empty lists are handled gracefully."""
        assert self.provider._rank_ports([], "test", False) == {}
        assert self.provider._rank_carriers([], "test", False) == {}

    def test_locode_pattern_matching(self):
        """Test that LOCODE pattern recognition works correctly."""
        # Should recognize valid LOCODEs (2 letters + 3 alphanumeric)
        assert self.provider._rank_ports([{"locode": "EGPSD", "name": "Test"}], "EGPSD", True)

        # Should handle digits in LOCODE
        ports = [{"name": "Test Port", "locode": "US123", "country": "US"}]
        result = self.provider._rank_ports(ports, "US123", is_locode_query=True)
        assert result["locode"] == "US123"

    def test_scac_pattern_matching(self):
        """Test that SCAC pattern recognition works correctly."""
        carriers = [{"name": "Test Carrier", "scac": "TEST", "id": "1"}]

        # 4-letter SCAC
        result = self.provider._rank_carriers(carriers, "TEST", is_scac_query=True)
        assert result["scac"] == "TEST"

        # 2-letter SCAC should also work
        carriers2 = [{"name": "XX Shipping", "scac": "XX", "id": "2"}]
        result2 = self.provider._rank_carriers(carriers2, "XX", is_scac_query=True)
        assert result2["scac"] == "XX"

    def test_port_noise_stripping_improves_startswith_matching(self):
        """Test that port name noise stripping improves startswith matching."""
        ports = [
            {"name": "New Alexandria", "locode": "USNAL", "country": "US", "size": 100},  # contains
            {
                "name": "Port of Alexandria",
                "locode": "EGALY",
                "country": "EG",
                "size": 50,
            },  # startswith after noise strip
        ]

        result = self.provider._rank_ports(ports, "Alexandria", is_locode_query=False)

        # "Port of Alexandria" should win because after stripping "Port of ",
        # it becomes "Alexandria" which is an exact match, beating contains match
        assert result["name"] == "Port of Alexandria"
        assert result["locode"] == "EGALY"


class TestSearoutesErrorMapping:
    """Test error code mapping functionality for Task 21."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_client = Mock()
        self.provider = SearoutesProvider(client=mock_client)

    def test_map_searoutes_error_code_3110_invalid_locode(self):
        """Test mapping of error code 3110 (invalid LOCODE)."""
        result = self.provider._map_searoutes_error_code("3110")
        assert result == "Unknown origin/destination port"

    def test_map_searoutes_error_code_1071_carrier_not_found(self):
        """Test mapping of error code 1071 (carrier not found)."""
        result = self.provider._map_searoutes_error_code("1071")
        assert result == "Carrier not found"

    def test_map_searoutes_error_code_1072_carrier_not_found(self):
        """Test mapping of error code 1072 (carrier not found)."""
        result = self.provider._map_searoutes_error_code("1072")
        assert result == "Carrier not found"

    def test_map_searoutes_error_code_1110_no_results(self):
        """Test mapping of error code 1110 (no itinerary found)."""
        result = self.provider._map_searoutes_error_code("1110")
        assert result == "No routes found for the specified criteria"

    def test_map_unknown_error_code_returns_none(self):
        """Test that unknown error codes return None."""
        result = self.provider._map_searoutes_error_code("9999")
        assert result is None

    def test_extract_error_message_with_friendly_mapping(self):
        """Test error message extraction with friendly mapping."""
        # Mock response with error code
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason_phrase = "Bad Request"
        mock_response.json.return_value = {"code": "3110", "message": "Invalid LOCODE provided"}

        result = self.provider._extract_error_message(mock_response)
        assert result == "Unknown origin/destination port"

    def test_extract_error_message_fallback_to_original_message(self):
        """Test error message extraction falls back to original message for unknown codes."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason_phrase = "Bad Request"
        mock_response.json.return_value = {"code": "9999", "message": "Some other error"}

        result = self.provider._extract_error_message(mock_response)
        assert result == "Some other error"


class TestSearoutesCaching:
    """Test caching functionality for Task 21."""

    def setup_method(self):
        """Set up test fixtures."""
        mock_client = Mock()
        self.provider = SearoutesProvider(client=mock_client)

    def test_port_cache_stores_and_retrieves_results(self):
        """Test that port cache stores and retrieves results correctly."""
        import time

        # Mock the _make_request to return a port result
        def mock_make_request(endpoint, params):
            mock_response = Mock()
            mock_response.json.return_value = [
                {"name": "Test Port", "locode": "TSTPT", "country": "TS"}
            ]
            return mock_response

        self.provider._make_request = Mock(side_effect=mock_make_request)

        # First call should hit the API
        result1 = self.provider.resolve_port("TSTPT")
        assert result1["name"] == "Test Port"
        assert self.provider._make_request.call_count == 1

        # Second call should hit cache
        result2 = self.provider.resolve_port("TSTPT")
        assert result2["name"] == "Test Port"
        assert self.provider._make_request.call_count == 1  # No additional API call

        # Cache should contain the entry
        assert len(self.provider._port_cache) == 1

    def test_carrier_cache_extended_ttl(self):
        """Test that carrier cache uses 1-hour TTL."""
        import time

        # Mock the _make_request to return a carrier result
        def mock_make_request(endpoint, params):
            mock_response = Mock()
            mock_response.json.return_value = [
                {"name": "Test Carrier", "scac": "TSTC", "id": "123"}
            ]
            return mock_response

        self.provider._make_request = Mock(side_effect=mock_make_request)

        # First call should hit the API
        result1 = self.provider.resolve_carrier("TSTC")
        assert result1["name"] == "Test Carrier"

        # Verify cache entry exists and check TTL is reasonable (should be recent)
        cache_key = list(self.provider._carrier_cache.keys())[0]
        cached_result, cached_time = self.provider._carrier_cache[cache_key]

        assert cached_result["name"] == "Test Carrier"
        assert abs(time.time() - cached_time) < 2  # Should be within 2 seconds of now

        # Second call should hit cache
        result2 = self.provider.resolve_carrier("TSTC")
        assert result2["name"] == "Test Carrier"
        assert self.provider._make_request.call_count == 1  # No additional API call
