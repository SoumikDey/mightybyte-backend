import sys
import os
import json
import pytest
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from lambda_function import lambda_handler

def test_lambda_get_method():
    event = {"httpMethod": "GET"}
    try:
        response = lambda_handler(event, None)
        assert response["statusCode"] == 200, "GET method should return status code 200"
        assert "body" in response, "Response should contain a body"
    except AttributeError:
        pytest.fail("GET method not implemented in lambda_function.py")

def test_lambda_post_method():
    event = {"httpMethod": "POST"}
    try:
        response = lambda_handler(event, None)
        assert response["statusCode"] == 200, "POST method should return status code 200"
        assert "body" in response, "Response should contain a body"
    except AttributeError:
        pytest.fail("POST method not implemented in lambda_function.py")

if __name__ == "__main__":
    pytest.main()
