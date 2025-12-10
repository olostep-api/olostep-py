"""
Answers endpoint contract validation tests.

This test suite validates answers endpoint contracts against the API using httpx transport directly.
"""

import pytest
import pytest_asyncio
import json
import asyncio
import time
from typing import Any, Dict, List, Optional
from itertools import product
from dataclasses import dataclass

from olostep.backend.api_endpoints import CONTRACTS
from olostep.backend.caller import EndpointCaller
from olostep.backend.transport_protocol import RawAPIRequest
from olostep.models.request import AnswersRequest, AnswersBodyParams
from olostep.models.response import AnswersResponse
from olostep.errors import OlostepClientError_RequestValidationFailed, OlostepServerError_RequestUnprocessable, OlostepServerError_NoResultInResponse, OlostepServerError_TemporaryIssue, OlostepServerError_UnknownIssue, OlostepServerError_NetworkBusy, OlostepServerError_ResourceNotFound

from tests.fixtures.api.requests.answers import (
    MINIMAL_REQUEST_BODY, TASK, JSON_FORMAT
)
from tests.conftest import extract_request_parameters, retry_request


ANSWERS_CREATE_CONTRACT = CONTRACTS[('answers', 'create')]

BASE_URL = "https://api.olostep.com/v1"


class TestAnswersCreate:
    """Test answers creation with various parameter combinations."""

    @pytest.mark.asyncio
    async def test_self_test_parameter_coverage(self):
        """Self-test: Verify that we have test methods for each parameter in the request model."""
        # Extract all parameters from the request model
        all_params = extract_request_parameters(ANSWERS_CREATE_CONTRACT.request_model)
        body_params = all_params['body']

        # Get all test methods in this class that start with 'test_parameter_'
        test_methods = [method for method in dir(self) if method.startswith('test_parameter_')]

        # Group test methods by parameter name
        param_tests = {}
        for method_name in test_methods:
            # Extract parameter name from 'test_parameter_XXX_valid', 'test_parameter_XXX_invalid', or 'test_parameter_XXX_null'
            if '_valid' in method_name:
                param_name = method_name.replace('test_parameter_', '').replace('_valid', '')
                test_type = 'valid'
            elif '_invalid' in method_name:
                param_name = method_name.replace('test_parameter_', '').replace('_invalid', '')
                test_type = 'invalid'
            elif '_null' in method_name:
                param_name = method_name.replace('test_parameter_', '').replace('_null', '')
                test_type = 'null'
            else:
                continue

            if param_name not in param_tests:
                param_tests[param_name] = set()
            param_tests[param_name].add(test_type)

        # Check coverage - each parameter must have valid, invalid, and null tests
        missing_tests = []
        incomplete_tests = []

        for param in body_params:
            if param not in param_tests:
                missing_tests.append(param)
            else:
                param_test_types = param_tests[param]
                if 'valid' not in param_test_types:
                    incomplete_tests.append(f"{param} (missing _valid test)")
                if 'invalid' not in param_test_types:
                    incomplete_tests.append(f"{param} (missing _invalid test)")
                if 'null' not in param_test_types:
                    incomplete_tests.append(f"{param} (missing _null test)")

        # Assert that we have complete tests for all parameters
        error_messages = []
        if missing_tests:
            error_messages.append(f"Missing test methods for parameters: {missing_tests}")
        if incomplete_tests:
            error_messages.append(f"Incomplete test coverage: {incomplete_tests}")

        assert len(error_messages) == 0, "; ".join(error_messages)

    @pytest.mark.asyncio
    async def test_unknown_parameter_ignored_by_api(self, endpoint_caller):
        """Test that the API ignores unknown parameters and works normally"""
        # Add a made-up parameter that should be rejected by our validation
        body_params = {
            **MINIMAL_REQUEST_BODY,
            "made_up_parameter": "this_should_be_ignored",
            "another_fake_param": {"nested": "value", "number": 123}
        }

        # Our validation should refuse this request due to the unknown parameters
        with pytest.raises(OlostepClientError_RequestValidationFailed):
            endpoint_caller.validate_request(ANSWERS_CREATE_CONTRACT, body_params=body_params)

        # But if we bypass validation and send it to the API anyway, the API should ignore the unknown parameters
        request = endpoint_caller._prepare_request(
            ANSWERS_CREATE_CONTRACT, {}, {}, body_params
        )

        # The API should accept the request and ignore the unknown parameters
        try:
            model = await retry_request(
                endpoint_caller, request, ANSWERS_CREATE_CONTRACT
            )
            assert isinstance(model, AnswersResponse)
            # Verify the response is valid despite the unknown parameters
            assert model.id is not None
            assert model.object == "answer"
        except OlostepServerError_TemporaryIssue:
            # API raised a temporary error - skip this test
            pytest.skip("API raised a temporary error")

    @pytest.mark.asyncio
    async def test_parameter_task_valid(self, endpoint_caller):
        """Test task parameter with valid values from fixtures"""
        for valid_task in TASK["param_values"]["valids"]:
            body_params = {"task": valid_task}

            validated_request = endpoint_caller.validate_request(
                ANSWERS_CREATE_CONTRACT, body_params=body_params
            )

            validated_body = validated_request["body_params"]
            assert "task" in validated_body
            assert validated_body["task"] == valid_task

            request = endpoint_caller._prepare_request(
                ANSWERS_CREATE_CONTRACT, **validated_request
            )

            # Valid requests should either succeed or have transient errors (not server errors)
            try:
                model = await retry_request(
                    endpoint_caller, request, ANSWERS_CREATE_CONTRACT
                )
                assert isinstance(model, AnswersResponse)
            except OlostepServerError_TemporaryIssue:
                # API raised a temporary error - skip this test
                pytest.skip("API raised a temporary error")

    @pytest.mark.asyncio
    async def test_parameter_task_invalid(self, endpoint_caller):
        """Test task parameter with invalid values from fixtures"""
        for invalid_task in TASK["param_values"]["invalids"]:
            body_params = {"task": invalid_task}

            with pytest.raises(OlostepClientError_RequestValidationFailed):
                endpoint_caller.validate_request(ANSWERS_CREATE_CONTRACT, body_params=body_params)

            # Test API behavior with invalid request (bypass validation)
            request = endpoint_caller._prepare_request(
                ANSWERS_CREATE_CONTRACT, {}, {}, body_params
            )
            response = await endpoint_caller._transport.request(request)

            # API may accept invalid values (our validation is stricter than API)
            try:
                model = endpoint_caller._handle_response(request, response, ANSWERS_CREATE_CONTRACT)
                # If API accepts invalid values, that's also acceptable for contract testing
                assert isinstance(model, AnswersResponse)
            except OlostepServerError_TemporaryIssue:
                # API raised a temporary error - skip this test
                pytest.skip("API raised a temporary error")
            except (OlostepServerError_RequestUnprocessable, OlostepServerError_NoResultInResponse):
                # API rejects invalid values - also acceptable
                pass

    @pytest.mark.asyncio
    async def test_parameter_task_null(self, endpoint_caller):
        """Test task parameter with null value"""
        body_params = {"task": None}

        with pytest.raises(OlostepClientError_RequestValidationFailed):
            endpoint_caller.validate_request(ANSWERS_CREATE_CONTRACT, body_params=body_params)

        # Test API behavior with null request (bypass validation)
        request = endpoint_caller._prepare_request(
            ANSWERS_CREATE_CONTRACT, {}, {}, body_params
        )
        response = await endpoint_caller._transport.request(request)

        # API returns 500 error for this null requests
        with pytest.raises(OlostepServerError_RequestUnprocessable):
            endpoint_caller._handle_response(request, response, ANSWERS_CREATE_CONTRACT)

    @pytest.mark.asyncio
    async def test_parameter_json_format_valid(self, endpoint_caller):
        """Test json_format parameter with valid values from fixtures"""
        for valid_json_format in JSON_FORMAT["param_values"]["valids"]:
            body_params = {**MINIMAL_REQUEST_BODY, "json_format": valid_json_format}

            validated_request = endpoint_caller.validate_request(
                ANSWERS_CREATE_CONTRACT, body_params=body_params
            )

            validated_body = validated_request["body_params"]
            if valid_json_format is not None:
                assert "json_format" in validated_body
            else:
                assert "json_format" not in validated_body

            request = endpoint_caller._prepare_request(
                ANSWERS_CREATE_CONTRACT, **validated_request
            )

            # Valid requests should either succeed or have transient errors (not server errors)
            try:
                model = await retry_request(
                    endpoint_caller, request, ANSWERS_CREATE_CONTRACT
                )
                assert isinstance(model, AnswersResponse)
            except OlostepServerError_TemporaryIssue:
                # API raised a temporary error - skip this test
                pytest.skip("API raised a temporary error")

    @pytest.mark.asyncio
    async def test_parameter_json_format_invalid(self, endpoint_caller):
        """Test json_format parameter with invalid values from fixtures"""
        for invalid_json_format in JSON_FORMAT["param_values"]["invalids"]:
            body_params = {**MINIMAL_REQUEST_BODY, "json_format": invalid_json_format}

            with pytest.raises(OlostepClientError_RequestValidationFailed):
                endpoint_caller.validate_request(ANSWERS_CREATE_CONTRACT, body_params=body_params)

            # Test API behavior with invalid request (bypass validation)
            request = endpoint_caller._prepare_request(
                ANSWERS_CREATE_CONTRACT, {}, {}, body_params
            )
            response = await endpoint_caller._transport.request(request)

            # API may accept invalid values (our validation is stricter than API)
            try:
                model = endpoint_caller._handle_response(request, response, ANSWERS_CREATE_CONTRACT)
                # If API accepts invalid values, that's also acceptable for contract testing
                assert isinstance(model, AnswersResponse)
            except OlostepServerError_TemporaryIssue:
                # API raised a temporary error - skip this test
                pytest.skip("API raised a temporary error")
            except (OlostepServerError_RequestUnprocessable, OlostepServerError_NoResultInResponse):
                # API rejects invalid values - also acceptable
                pass

    @pytest.mark.asyncio
    async def test_parameter_json_format_null(self, endpoint_caller):
        """Test json_format parameter with null value"""
        body_params = {**MINIMAL_REQUEST_BODY, "json_format": None}

        validated_request = endpoint_caller.validate_request(
            ANSWERS_CREATE_CONTRACT, body_params=body_params
        )

        validated_body = validated_request["body_params"]
        assert "json_format" not in validated_body

        request = endpoint_caller._prepare_request(
            ANSWERS_CREATE_CONTRACT, **validated_request
        )

        # Valid requests should either succeed or have transient errors (not server errors)
        try:
            model = await retry_request(
                endpoint_caller, request, ANSWERS_CREATE_CONTRACT
            )
            assert isinstance(model, AnswersResponse)
        except OlostepServerError_TemporaryIssue:
            # API raised a temporary error - skip this test
            pytest.skip("API raised a temporary error")

    @pytest.mark.asyncio
    async def test_basic_functionality_with_fixture_data(self, endpoint_caller):
        """Test basic functionality using the fixture data"""
        body_params = MINIMAL_REQUEST_BODY

        validated_request = endpoint_caller.validate_request(
            ANSWERS_CREATE_CONTRACT, body_params=body_params
        )

        request = endpoint_caller._prepare_request(
            ANSWERS_CREATE_CONTRACT, **validated_request
        )

        try:
            model = await retry_request(
                endpoint_caller, request, ANSWERS_CREATE_CONTRACT
            )
            assert isinstance(model, AnswersResponse)
            assert model.id is not None
            assert model.object == "answer"
            assert model.task is not None
            assert model.result is not None
            assert model.result.json_content is not None or model.result.json_hosted_url is not None
        except OlostepServerError_TemporaryIssue:
            # API raised a temporary error - skip this test
            pytest.skip("API raised a temporary error")
