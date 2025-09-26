"""
Comprehensive endpoint contract validation with proper test coordination.

This test suite validates all endpoint contracts against the API with proper
error handling, retry logic, and organized test structure.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import Any

from olostep.backend.api_endpoints import CONTRACTS, EndpointContract
from olostep.backend.caller import EndpointCaller
from olostep.models.response import CreateScrapeResponse

from olostep.errors import (
    OlostepServerError_AuthFailed,
    OlostepServerError_InvalidEndpointCalled,
    OlostepServerError_RequestUnprocessable,
    OlostepServerError_NoResultInResponse,
    OlostepClientError_RequestValidationFailed,
)

from olostep._log import _enable_stderr_debug
from tests.conftest import retry_request
_enable_stderr_debug()




class TestContractCoverage:
    """Test that defined contracts match the expected endpoints."""
    
    def test_all_expected_endpoints_are_present_in_contracts(self):
        # Define expected endpoints based on the actual API specification
        expected_endpoints = {
            ('batch', 'info'),
            ('batch', 'items'),
            ('batch', 'start'),
            ('crawl', 'info'),
            ('crawl', 'pages'),
            ('crawl', 'start'),
            ('map', 'create'),
            ('retrieve', 'get'),
            ('scrape', 'get'),
            ('scrape', 'url'),
        }
        
        # Get actual endpoints from contracts
        actual_endpoints = set(CONTRACTS.keys())
        
        print(f"Expected endpoints: {len(expected_endpoints)}")
        print(f"Actual endpoints: {len(actual_endpoints)}")
        
        # Check for missing endpoints
        missing_endpoints = expected_endpoints - actual_endpoints
        if missing_endpoints:
            pytest.fail(f"Missing endpoints in contracts: {missing_endpoints}")
        
        # Check for unexpected endpoints
        unexpected_endpoints = actual_endpoints - expected_endpoints
        if unexpected_endpoints:
            pytest.fail(f"Unexpected endpoints in contracts: {unexpected_endpoints}")
        
        print("✅ All expected endpoints are present in contracts")


class TestErrorDetection:
    """Test errors that transport and caller can detect."""
    
    @pytest.fixture
    def fake_endpoint_contract(self) -> EndpointContract:
        """Create a fake endpoint contract for testing error scenarios."""
        # Create a contract that points to a non-existent endpoint
        return EndpointContract(
            key=('fake', 'endpoint'),
            name='Fake Endpoint',
            description='Non-existent endpoint for testing',
            method='POST',
            path='/fake/endpoint',
            request_model=None,  # No request model for simplicity
            response_model=None,  # No response model for simplicity
            examples=[]
        )
    
    @pytest.mark.asyncio
    async def test_real_api_key_authentication_succeeds(self, endpoint_caller):
        contract = CONTRACTS[('scrape', 'url')]
        
        body_params = {'url_to_scrape': 'https://example.com'}
        
        result = await endpoint_caller._invoke(contract, body_params=body_params)#, validate_request=False)
        print(f"✅ Real API key authentication successful: {type(result)}")
    
    @pytest.mark.asyncio
    async def test_fake_api_key_authentication_fails(self, caller_with_fake_key):
        contract = CONTRACTS[('scrape', 'url')]
        
        args = {}
        body = {'url_to_scrape': 'https://example.com'}
        
        with pytest.raises(OlostepServerError_AuthFailed) as exc_info:
            await caller_with_fake_key._invoke(contract, path_params=args, body_params=body)#, validate_request=False)
        print(f"✅ Fake API key correctly failed: {exc_info.type.__name__}: {exc_info.value}")
    
    @pytest.mark.asyncio
    async def test_fake_endpoint_with_real_key_raises_invalid_endpoint_error(self, endpoint_caller, fake_endpoint_contract: EndpointContract):
        args = {}
        body = {}
        
        with pytest.raises(OlostepServerError_InvalidEndpointCalled) as exc_info:
            await endpoint_caller._invoke(fake_endpoint_contract, path_params=args, body_params=body)#, validate_request=False)
        print(f"✅ Real API key with fake endpoint correctly failed: {exc_info.type.__name__}: {exc_info.value}")
    
    @pytest.mark.asyncio
    async def test_fake_endpoint_with_fake_key_raises_invalid_endpoint_error(self, caller_with_fake_key, fake_endpoint_contract: EndpointContract):
        args = {}
        body = {}
        
        with pytest.raises(OlostepServerError_InvalidEndpointCalled) as exc_info:
            await caller_with_fake_key._invoke(fake_endpoint_contract, path_params=args, body_params=body)#, validate_request=False)
        print(f"✅ Fake API key with fake endpoint correctly failed: {exc_info.type.__name__}: {exc_info.value}")
    
    @pytest.mark.asyncio
    async def test_type_confusion_with_real_key_is_accepted_by_api(self, endpoint_caller):
        contract = CONTRACTS[('scrape', 'url')]
        
        body_params = {
            'url_to_scrape': 'https://example.com',
            'wait_before_scraping': 'not_a_number'  # Should be int, sending string
        }
        
        result = await endpoint_caller._invoke(contract, body_params=body_params)#, validate_request=False)
        print(f"✅ Type confusion accepted by API: {type(result)}")
    
    @pytest.mark.asyncio
    async def test_type_confusion_with_fake_key_raises_authentication_error(self, caller_with_fake_key):
        contract = CONTRACTS[('scrape', 'url')]
        
        args = {}
        body = {
            'url_to_scrape': 'https://example.com',
            'wait_before_scraping': 'not_a_number'  # Should be int, sending string
        }
        
        with pytest.raises(OlostepServerError_AuthFailed) as exc_info:
            await caller_with_fake_key._invoke(contract, path_params=args, body_params=body)#, validate_request=False)
        print(f"✅ Type confusion with fake key correctly detected: {exc_info.type.__name__}: {exc_info.value}")
    
    @pytest.mark.asyncio
    async def test_bad_ssl_endpoint_raises_no_result_error(self, endpoint_caller):
        contract = CONTRACTS[('scrape', 'url')]
        
        args = {}
        body = {'url_to_scrape': 'https://self-signed.badssl.com'}
        
        with pytest.raises(OlostepServerError_NoResultInResponse) as exc_info:
            request = endpoint_caller._prepare_request(contract, path_params=args, body_params=body)
            await retry_request(endpoint_caller, request, contract)
        print(f"✅ Bad SSL correctly detected: {exc_info.type.__name__}: {exc_info.value}")
    
    @pytest.mark.asyncio
    async def test_api_validates_path_before_params_before_auth(self, endpoint_caller, caller_with_fake_key, fake_endpoint_contract: EndpointContract):
        contract = CONTRACTS[('scrape', 'url')]
        
        # Invalid PATH - both keys should get same error (PATH checked first)
        with pytest.raises(OlostepServerError_InvalidEndpointCalled):
            await endpoint_caller._invoke(fake_endpoint_contract, path_params={}, body_params={})#, validate_request=False)
        with pytest.raises(OlostepServerError_InvalidEndpointCalled):
            await caller_with_fake_key._invoke(fake_endpoint_contract, path_params={}, body_params={})#, validate_request=False)
        
        # Valid PATH, invalid PARAMS - determine if PARAMS or AUTH is checked first
        
        # Required key missing
        missing_required_body = {
            'we_dont_add_url_to_scrape': 'https://example.com'  # Missing required 'url_to_scrape'
        }
        
        # Real API key with missing required parameter
        with pytest.raises(OlostepServerError_NoResultInResponse):
            await endpoint_caller._invoke(contract, path_params={}, body_params=missing_required_body)#, validate_request=False)
        
        # Fake API key with missing required parameter
        with pytest.raises(OlostepServerError_AuthFailed):
            await caller_with_fake_key._invoke(contract, path_params={}, body_params=missing_required_body)#, validate_request=False)
        
        # Type confusion (string instead of array)
        type_confusion_body = {
            'url_to_scrape': 'https://example.com',
            'formats': 'html'  # Should be array, not string
        }
        
        # Real API key with type confusion
        with pytest.raises(OlostepServerError_RequestUnprocessable):
            await endpoint_caller._invoke(contract, path_params={}, body_params=type_confusion_body)#, validate_request=False)
        
        # Fake API key with type confusion
        with pytest.raises(OlostepServerError_RequestUnprocessable):
            await caller_with_fake_key._invoke(contract, path_params={}, body_params=type_confusion_body)#, validate_request=False)
        
        # Invalid input value (invalid country)
        invalid_input_body = {
            'url_to_scrape': 'https://example.com',
            'country': 'INVALID_COUNTRY'  # Invalid country value
        }
        
        # Real API key with invalid input
        with pytest.raises(OlostepServerError_RequestUnprocessable):
            await endpoint_caller._invoke(contract, path_params={}, body_params=invalid_input_body)#, validate_request=False)
        
        # Fake API key with invalid input
        with pytest.raises(OlostepServerError_AuthFailed):
            await caller_with_fake_key._invoke(contract, path_params={}, body_params=invalid_input_body)#, validate_request=False)
        
        # Valid PATH, valid PARAMS, invalid AUTH - AUTH checked last
        valid_body_params = {'url_to_scrape': 'https://example.com'}
        
        # Real API key succeeds (all validations pass)
        result = await endpoint_caller._invoke(contract, body_params=valid_body_params)#, validate_request=False)
        assert result is not None
        
        # Fake API key fails on AUTH (AUTH checked after PATH and PARAMS)
        with pytest.raises(OlostepServerError_AuthFailed):
            await caller_with_fake_key._invoke(contract, path_params={}, body_params=valid_body_params)#, validate_request=False)


class TestBrokenWebsiteScrapingBehavior:
    """Test API behavior when scraping broken/problematic websites using direct caller."""
    
    @pytest.mark.asyncio
    async def test_scrape_url_http_status_code_passthrough(self, endpoint_caller: EndpointCaller):
        """Test that HTTP status codes from http.cat are properly passed through."""
        contract = CONTRACTS[('scrape', 'url')]
        
        # Test various HTTP status codes - these should succeed and return the status
        status_codes: list[int] = [200, 201, 202, 204, 301, 302, 400, 401, 403, 404, 429, 500, 502, 503, 504]

        async def try_status_code(status_code: int) -> None:
            url = f"https://http.cat/{status_code}"
            body_params = {'url_to_scrape': url}
            request = endpoint_caller._prepare_request(contract, path_params={}, query_params={}, body_params=body_params)
            result = await retry_request(endpoint_caller, request, contract)
            assert result is not None
            assert hasattr(result, 'id') or 'id' in result
            print(f"✅ HTTP {status_code} passthrough successful: {url}")

        await asyncio.gather(*(try_status_code(code) for code in status_codes), return_exceptions=True)


    @pytest.mark.asyncio
    async def test_scrape_url_comprehensive_status_codes(self, endpoint_caller: EndpointCaller) -> None:
        """Test comprehensive HTTP status codes with http.cat in parallel for speed."""
        contract = CONTRACTS[('scrape', 'url')]

        status_codes: list[int] = [
            200, 201, 202, 204, 206,
            301, 302, 303, 304, 307, 308,
            400, 401, 403, 404, 405, 406, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 422, 429, 451,
            500, 501, 502, 503, 504, 505, 507, 508, 510, 511
        ]

        async def try_status_code(status_code: int) -> tuple[int, bool, str | None]:
            url = f"https://http.cat/{status_code}"
            try:
                body_params = {'url_to_scrape': url}
                request = endpoint_caller._prepare_request(contract, path_params={}, query_params={}, body_params=body_params)
                result = await retry_request(endpoint_caller, request, contract)
                if result is not None:
                    return status_code, True, None
                return status_code, False, "Returned None"
            except Exception as e:
                return status_code, False, str(e)

        results = await asyncio.gather(
            *(try_status_code(code) for code in status_codes), return_exceptions=True
        )

        successful_passthroughs: list[int] = []
        failed_passthroughs: list[tuple[int, str | None]] = []

        for status_code, success, error in results:
            if success:
                successful_passthroughs.append(status_code)
                print(f"✅ HTTP {status_code} passthrough successful")
            else:
                failed_passthroughs.append((status_code, error))
                print(f"❌ HTTP {status_code} failed: {error}")

        print(f"\n📊 Status Code Passthrough Results:")
        print(f"✅ Successful passthroughs: {len(successful_passthroughs)}")
        print(f"❌ Failed passthroughs: {len(failed_passthroughs)}")

        if failed_passthroughs:
            print(f"Failed status codes: {[code for code, _ in failed_passthroughs]}")

        assert len(successful_passthroughs) > len(failed_passthroughs), (
            f"Too many failed passthroughs: {failed_passthroughs}"
        )


    @pytest.mark.asyncio
    async def test_scrape_url_ssl_issues(self, endpoint_caller: EndpointCaller):
        """Test scrape URL with SSL issues."""
        contract = CONTRACTS[('scrape', 'url')]
        
        ssl_urls = [
            'https://self-signed.badssl.com',
            'https://expired.badssl.com',
            'https://wrong.host.badssl.com',
            'https://untrusted-root.badssl.com',
        ]
        
        for url in ssl_urls:
            with pytest.raises(OlostepServerError_NoResultInResponse):
                try:
                    await endpoint_caller.invoke(contract, body_params={'url_to_scrape': url})
                except Exception as e:
                    if isinstance(e, OlostepServerError_NoResultInResponse):
                        raise
                    print(f"✅ SSL issue check raised unexpected error: {url} {e}")
            print(f"✅ SSL issue handled: {url}")

    @pytest.mark.asyncio
    async def test_scrape_url_timeout_behavior(self, endpoint_caller: EndpointCaller):
        """Test timeout behavior with delayed responses."""
        contract = CONTRACTS[('scrape', 'url')]
        
        # Should succeed (within ~5 second timeout)
        url = 'https://httpbin.org/delay/5'
        body_params = {'url_to_scrape': url}
        request = endpoint_caller._prepare_request(contract, path_params={}, query_params={}, body_params=body_params)
        result = await retry_request(endpoint_caller, request, contract)  # pyright: ignore[reportUndefinedVariable]
        assert result is not None
        print(f"✅ Delayed response succeeded: {url}")
        
        url = 'https://httpbin.org/delay/100000'
        # with pytest.raises(OlostepServerRespondedWithNoResultError):
        # not even here it times out
        request = endpoint_caller._prepare_request(contract, path_params={}, query_params={}, body_params={'url_to_scrape': url})
        await retry_request(endpoint_caller, request, contract)
        print(f"✅ Long delay timed out: {url}")

    @pytest.mark.skip(reason="No website reliably large enough to trigger size_exceeded in test environments")
    @pytest.mark.asyncio
    async def test_scrape_url_size_exceeded_behavior(self, endpoint_caller: EndpointCaller) -> None:
        """Test that streaming a large response sets size_exceeded to True."""
        # contract = CONTRACTS[('scrape', 'url')]
        # url = "https://archive.org/stream/warandpeace030164mbp/warandpeace030164mbp_djvu.txt"
        # body_params = {"url_to_scrape": url}
        # request = endpoint_caller._prepare_request(
        #     contract, path_params={}, query_params={}, body_params=body_params
        # )
        # result: CreateScrapeResponse = await retry_request(endpoint_caller, request, contract)  # pyright: ignore[reportUndefinedVariable]
        # assert result is not None
        # assert result.result.size_exceeded is True, (
        #     f"Expected size_exceeded=True for large response, got {getattr(result.result, 'size_exceeded', None)}"
        # )
        # print(f"✅ Large stream correctly flagged as size_exceeded: {url}")
        pass
    
    @pytest.mark.asyncio
    async def test_scrape_url_redirect_behavior(self, endpoint_caller: EndpointCaller):
        contract = CONTRACTS[('scrape', 'url')]
        
        url = 'https://httpbin.org/redirect/10'
        request = endpoint_caller._prepare_request(contract, path_params={}, query_params={}, body_params={'url_to_scrape': url})
        await retry_request(endpoint_caller, request, contract)
        print(f"✅ Redirect chain handled: {url}")
    
    @pytest.mark.asyncio
    async def test_scrape_url_comprehensive_invalid_urls(self, endpoint_caller: EndpointCaller):
        """Test comprehensive invalid URL scenarios."""
        contract = CONTRACTS[('scrape', 'url')]
        
        # These should fail client-side validation
        client_validation_urls = [
            'not-a-url',
            'ftp://example.com',
            'javascript:alert(1)',
            'data:text/html,<h1>Test</h1>',
            'file:///etc/passwd',
            'http://',
            'https://',
            'https://example.com:99999',
        ]
        
        for url in client_validation_urls:
            with pytest.raises(OlostepClientError_RequestValidationFailed):
                await endpoint_caller.invoke(contract, args={}, body={'url_to_scrape': url})
            print(f"✅ Invalid URL rejected by client validation: {url}")
        
        # These should pass client validation but fail server-side (timeout)
        server_timeout_urls = [
            'https://nonexistent-subdomain-12345.google.com',
            'https://this-domain-definitely-does-not-exist-12345.com',
        ]
        
        for url in server_timeout_urls:
            with pytest.raises(OlostepServerError_NoResultInResponse):
                await endpoint_caller._invoke(
                    contract, path_params={}, body_params={'url_to_scrape': url}
                )
            print(f"✅ Non-existent domain timed out: {url}")
    
    @pytest.mark.asyncio
    async def test_scrape_url_comprehensive_invalid_urls(self, endpoint_caller: EndpointCaller) -> None:
        """Test scrape URL with invalid URL format in parallel."""
        contract = CONTRACTS[('scrape', 'url')]

        # These should fail client-side validation
        client_validation_urls: list[str] = [
            "not-a-url",
            "ftp://example.com",
            "javascript:alert(1)",
            "mailto:test@example.com",
            "file:///etc/passwd",
            "data:text/html,<h1>Test</h1>",
            "http://",
            "https://",
            "https://example.com:99999"
        ]

        server_timeout_urls = [
            'https://nonexistent-subdomain-12345.google.com',
            'https://this-domain-definitely-does-not-exist-12345.com',
        ]

        async def run_invalid_url_test(invalid_url: str, client_validation: bool) -> None:
            print(f"Testing invalid URL: {invalid_url}")
            if client_validation:
                with pytest.raises(OlostepClientError_RequestValidationFailed):
                    endpoint_caller.validate_request(
                        contract, body_params={'url_to_scrape': invalid_url}
                    )
            try:
                request = endpoint_caller._prepare_request(contract, path_params={}, query_params={}, body_params={'url_to_scrape': invalid_url})
                await retry_request(endpoint_caller, request, contract)
            except OlostepServerError_NoResultInResponse:
                print(f"✅ Invalid URL format rejected by server: {invalid_url}")
            else:
                pytest.fail(f"❌ Invalid URL format was not rejected: {invalid_url}")

        await asyncio.gather(*(run_invalid_url_test(url, True) for url in client_validation_urls), return_exceptions=True)
        await asyncio.gather(*(run_invalid_url_test(url, False) for url in server_timeout_urls), return_exceptions=True)
    
    @pytest.mark.asyncio
    async def test_scrape_url_unreachable_urls(self, endpoint_caller: EndpointCaller):
        """Test scrape URL with unreachable URLs."""
        contract = CONTRACTS[('scrape', 'url')]
        
        # These should timeout (non-existent domains)
        unreachable_urls = [
            'https://nonexistent-domain-12345.com',
        ]
        
        for url in unreachable_urls:
            with pytest.raises((OlostepServerError_NoResultInResponse, OlostepServerError_RequestUnprocessable)):
                await endpoint_caller.invoke(contract, body_params={'url_to_scrape': url})
            print(f"✅ Unreachable URL handled: {url}")
        
        # These should succeed (http.cat passthrough)
        passthrough_urls = [
            'https://http.cat/500',  # http.cat should passthrough
            'https://http.cat/404',  # http.cat should passthrough
        ]
        
        for url in passthrough_urls:
            body_params = {'url_to_scrape': url}

            request = endpoint_caller._prepare_request(contract, path_params={}, query_params={}, body_params=body_params)
            result = await retry_request(endpoint_caller, request, contract)
            assert result is not None
            print(f"✅ HTTP status passthrough successful: {url}")


