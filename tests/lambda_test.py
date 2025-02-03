import os
import pytest

lambda_function_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lambda_function.py")

def test_lambda_contains_http_methods():
    with open(lambda_function_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert any(method in content for method in ['"GET"', "'GET'", '"POST"', "'POST'"]), "HTTP method syntax (GET/POST) is not present in lambda_function.py"

if __name__ == "__main__":
    pytest.main()
