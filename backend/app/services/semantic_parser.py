import urllib.parse
import json
import hashlib
from typing import List, Dict, Any, Optional
import structlog
import re

logger = structlog.get_logger()

class SemanticParser:
    """
    Parses requests to extract semantic endpoint definitions.
    Focuses on identifying parameter types and deduplicating endpoints based on structure rather than values.
    """

    def parse_request(self, method: str, url: str, headers: Dict[str, str], body: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes a single request to produce a normalized endpoint definition.
        """
        parsed_url = urllib.parse.urlparse(url)
        # Normalize: remove query string from base URL
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        parameters = []

        # 1. Parse Query Parameters
        query_params = urllib.parse.parse_qs(parsed_url.query, keep_blank_values=True)
        for key, values in query_params.items():
            # Taking the first value for type inference primarily
            # Real-world usage might check all values, but usually they are same type
            val = values[0] if values else ""
            param_type = self._infer_type(val)
            parameters.append({
                "name": key,
                "type": param_type,
                "location": "query"
            })

        # 2. Parse Body Parameters (JSON only for now)
        if body and method in ["POST", "PUT", "PATCH"]:
            try:
                # Naive check if body is JSON
                if headers.get("content-type", "").startswith("application/json") or body.strip().startswith("{"):
                    json_body = json.loads(body)
                    if isinstance(json_body, dict):
                        for key, value in json_body.items():
                            param_type = self._infer_type(value)
                            parameters.append({
                                "name": key,
                                "type": param_type,
                                "location": "body"
                            })
            except json.JSONDecodeError:
                # Could be form-data or other formats, ignore for now or implement later
                pass

        # Sort parameters by name for consistent signature
        parameters.sort(key=lambda x: x["name"])

        # 3. Generate Deduplication Signature
        # Signature format: METHOD|PATH|Sorted(ParamNames+Types)
        # We include Types in signature so /api/search?q=abc (string) is different from /api/search?q=123 (int)??
        # User said: "/notice?id=1 ~ /notice?id=1000 parsing skip -> notice id: int, once"
        # So signature should include "id:int". If another request is "id:string", is it same endpoint? 
        # Usually yes in REST, but technically different attack surface.
        # Let's include Name+Type in signature for strictest deduplication, 
        # OR just Name if we want to merge types.
        # Plan says "Deduplicate Endpoints by Param Type". So include Type.
        
        param_sig = ",".join([f"{p['name']}:{p['type']}" for p in parameters])
        signature_raw = f"{method.upper()}|{parsed_url.path}|{param_sig}"
        spec_hash = hashlib.sha256(signature_raw.encode()).hexdigest()

        return {
            "method": method.upper(),
            "url": base_url, # Base URL without query
            "headers": headers,
            "parameters": parameters,
            "spec_hash": spec_hash
        }

    def _infer_type(self, value: Any) -> str:
        """
        Infers the semantic type of a value.
        Returns: 'int', 'float', 'bool', 'uuid', 'email', 'string', 'object', 'array', 'null'
        """
        if value is None:
            return "null"
        
        if isinstance(value, bool):
            return "bool"
        
        if isinstance(value, int):
            return "int"
            
        if isinstance(value, float):
            return "float"
            
        if isinstance(value, (dict, list)):
            return "json" # Simplified for composed types

        str_val = str(value).strip()
        
        if str_val.lower() in ["true", "false"]:
            return "bool"
            
        if str_val.isdigit():
            return "int"
            
        try:
            float(str_val)
            return "float"
        except ValueError:
            pass
            
        # UUID Regex
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', str_val, re.IGNORECASE):
            return "uuid"
            
        # Email Regex (Simple)
        if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str_val):
            return "email"

        return "string"
