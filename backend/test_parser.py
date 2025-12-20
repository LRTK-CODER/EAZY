
import sys
import os

# Ensure app is in path
sys.path.append(os.getcwd())

from app.services.semantic_parser import SemanticParser

def test_semantic_parser():
    parser = SemanticParser()
    
    # Test Case 1: Path parameter inference
    url = "http://example.com/doc/1"
    headers = {}
    method = "GET"
    
    result = parser.parse_request(method, url, headers)
    
    print(f"URL Normalized: {result['url']}")
    print(f"Parameters: {result['parameters']}")
    
    # Verification Logic
    path_param_found = any(p['location'] == 'path' for p in result['parameters'])
    
    if path_param_found:
        print("FAIL: Path parameter was found in parameters list!")
        sys.exit(1)
    
    if result['url'].endswith("/doc/{int}"):
        print("PASS: URL was correctly normalized.")
    else:
        print(f"FAIL: URL normalization failed. Got {result['url']}")
        sys.exit(1)
        
    print("SUCCESS: Path parameters are excluded from params list as requested.")

if __name__ == "__main__":
    test_semantic_parser()
