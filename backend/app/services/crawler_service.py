from app.services.semantic_parser import SemanticParser
from typing import Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import structlog
import urllib.parse
import re

logger = structlog.get_logger()

class CrawlerService:
    """
    Service for active crawling using Playwright.
    Handles browser lifecycle, navigation, and DOM extraction.
    """

    def __init__(self):
        from app.core.crawler_config import crawler_config
        self.parser = SemanticParser()
        self.config = crawler_config
        self.blacklist = self.config.blacklist

    async def crawl(self, start_url: str, max_depth: int = 2, max_pages: int = 50, 
                   target_id: int = None, scan_job_id: int = None,
                   progress_callback=None, result_callback=None) -> Dict[str, Any]:
        """
        Recursively crawls a target URL using BFS with safety restrictions.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            
            try:
                settings = self.config.settings
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent=settings.get("user_agent", "EAZY-Crawler")
                )
                
                # BFS Queue: (url, depth)
                queue = []
                queue.append({"url": start_url, "depth": 0})
                
                visited = set()
                results = []
                
                # Domain Scope Locking
                base_domain = urllib.parse.urlparse(start_url).netloc

                while queue and len(visited) < max_pages:
                    # Check cancellation or stop signal if possible (Not implemented deep yet, but loop checks)
                    
                    # Update Progress BEFORE popping to show "pending work" includes current job
                    if progress_callback:
                        await progress_callback(len(visited), len(queue))

                    job = queue.pop(0)
                    current_url = job["url"]
                    depth = job["depth"]
                    
                    if current_url in visited: continue
                    
                    if self._is_blacklisted(current_url):
                        logger.warning("crawler.skip_blacklist", url=current_url)
                        continue
                        
                    visited.add(current_url)
                    
                    # Update Progress (Visited count changed)
                    # if progress_callback:
                    #    await progress_callback(len(visited), len(queue))
                    
                    # Visit Page
                    page_result = await self._process_page(context, current_url, target_id=target_id, scan_job_id=scan_job_id)
                    results.append(page_result)
                    
                    # Send endpoints if found
                    if result_callback and page_result.get('endpoints'):
                        for ep in page_result['endpoints']:
                            await result_callback(ep)
                    
                    # Enqueue Children
                    if depth < max_depth:
                        for link in page_result.get('links', []):
                            if self._is_allowed_scope(link, base_domain) and link not in visited:
                                queue.append({"url": link, "depth": depth + 1})
                        
                        # Update Progress immediately after finding new links
                        if progress_callback:
                            await progress_callback(len(visited), len(queue))
                                
                return {
                    "root_url": start_url,
                    "pages_crawled": len(results),
                    "results": results
                }

            except Exception as e:
                logger.error("crawler.error", start_url=start_url, error=str(e))
                raise e
            finally:
                await browser.close()

    async def _process_page(self, context: BrowserContext, url: str, target_id: int = None, scan_job_id: int = None) -> Dict[str, Any]:
        """
        Internal method to visit and parse a single page.
        """
        page = await context.new_page()
        captured_requests = []
        
        async def handle_request(request):
            try:
                if request.resource_type in ["image", "stylesheet", "font", "media"]: return
                # We can store raw requests if we want, but response listener is better for full pair
                pass
            except: pass

        async def handle_response(response):
            try:
                 request = response.request
                 if request.resource_type in ["image", "stylesheet", "font", "media"]: return
                 
                 # Prepare data for TrafficService
                 from app.services.traffic_service import traffic_service
                 from app.models.traffic_log import TrafficSource
                 import urllib.parse
                 
                 parsed_url = urllib.parse.urlparse(request.url)
                 
                 # Get headers/body (be careful with body size or availability)
                 # req_body = request.post_data # Already handled by TrafficService NUL clean
                 
                 res_body = ""
                 try:
                     res_body = await response.text()
                 except: 
                     pass

                 if target_id:
                     await traffic_service.save_traffic(
                        target_id=target_id, 
                        scan_job_id=scan_job_id,
                        method=request.method,
                        url=request.url,
                        host=parsed_url.netloc,
                        path=parsed_url.path,
                        request_headers=request.headers,
                        request_body=request.post_data,
                        response_headers=response.headers,
                        response_body=res_body,
                        status_code=response.status,
                        source=TrafficSource.ACTIVE
                     )

            except Exception as e:
                # logger.warning("crawler.traffic_save_failed", error=str(e))
                pass

        page.on("response", handle_response)
        
        try:
            logger.info("crawler.visiting", url=url)
            response = await page.goto(url, wait_until="networkidle", timeout=15000)
            
            # Rendering Buffer: Wait for client-side rendering (e.g. mapping API data to DOM)
            await page.wait_for_timeout(2000)
            
            if not response: return {"url": url, "error": "No response"}
            
            # DOM Parsing (Enhanced to capture Event Handlers)
            dom_data = await page.evaluate("""
                () => {
                    const forms = Array.from(document.forms).map(form => {
                        const inputs = Array.from(form.elements).filter(el => el.name).map(el => ({
                            name: el.name, type: el.type || 'text', value: el.value || ''
                        }));
                        return { action: form.action || window.location.href, method: form.method || 'GET', inputs: inputs };
                    });
                    const uniqueLinks = Array.from(new Set(
                        Array.from(document.querySelectorAll('a'))
                            .map(a => a.href)
                            .filter(href => href && !href.startsWith('javascript:') && !href.startsWith('mailto:'))
                    ));
                    const inputs = Array.from(document.querySelectorAll('input, textarea, select'))
                        .filter(el => !el.form && el.name)
                        .map(el => ({ name: el.name, type: el.type || 'text', value: el.value || '' }));
                    
                    // Usage-Based Inference: Extract function calls from event handlers
                    const eventHandlers = [];
                    document.querySelectorAll('*').forEach(el => {
                        Array.from(el.attributes).forEach(attr => {
                            if (attr.name.startsWith('on')) { 
                                eventHandlers.push(attr.value);
                            }
                        });
                    });

                    return { forms, links: uniqueLinks, inputs, eventHandlers };
                }
            """)
            
            # Semantic Parsing & Source Analysis
            endpoints = []
            seen_hashes = set()
            
            # 1. Process Network Requests (Dynamic)
            for req in captured_requests:
                parsed = self.parser.parse_request(req['method'], req['url'], req['headers'], req['body'])
                parsed['source'] = 'network'
                if parsed['spec_hash'] not in seen_hashes:
                    seen_hashes.add(parsed['spec_hash'])
                    endpoints.append(parsed)
            
            # 2. Advanced Usage-Based Inference
            # Step A: Parse Function Calls from DOM Events
            function_usage_map = {} 
            handlers = dom_data.get('eventHandlers', [])
            
            for handler in handlers:
                matches = re.findall(r"(\w+)\s*\(([^)]+)\)", handler)
                for func_name, args_str in matches:
                    arg = args_str.split(',')[0].strip()
                    
                    # Infer type from the Argument Value
                    inferred_type = 'string'
                    if arg.isdigit(): inferred_type = 'int'
                    elif re.match(r"^['\"].*['\"]$", arg): inferred_type = 'string' # Quoted string
                    elif arg == 'true' or arg == 'false': inferred_type = 'bool'
                    
                    if func_name not in function_usage_map:
                        function_usage_map[func_name] = inferred_type
            
            # Step B: Get Function Source via Playwright (Reliable)
            if function_usage_map:
                # Prepare a script to get source for all found functions
                funcs_to_check = list(function_usage_map.keys())
                # Create a safe JS snippet
                js_check = f"""
                    () => {{
                        const results = {{}};
                        const targetFuncs = {str(funcs_to_check)};
                        targetFuncs.forEach(name => {{
                            try {{
                                if (typeof window[name] === 'function') {{
                                    results[name] = window[name].toString();
                                }}
                            }} catch(e) {{}}
                        }});
                        return results;
                    }}
                """
                function_sources = await page.evaluate(js_check)
                
                # Step C: Analyze Function Source
                for func_name, source in function_sources.items():
                    usage_type = function_usage_map[func_name]
                    
                    # Regex to find parameter name: function openDocument(id) {
                    # or openDocument(id) { 
                    param_match = re.search(r"function\s+\w+\s*\(([^)]+)\)|^\w+\s*\(([^)]+)\)", source)
                    if not param_match: continue
                    
                    # Group 1 or 2
                    params_str = param_match.group(1) or param_match.group(2)
                    if not params_str: continue
                    
                    param_name = params_str.split(',')[0].strip()
                    
                    # Look for URL patterns using this parameter in the source
                    template_matches = re.findall(r"['\"`](\/[a-zA-Z0-9_\-\/{}$]+)['\"`]", source)
                    for path in template_matches:
                        if f"${{{param_name}}}" in path:
                             # Found correlation!
                             final_type = usage_type
                             normalized_path = path.replace(f"${{{param_name}}}", f"{{{final_type}}}")
                             
                             full_url = f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}{normalized_path}"
                             parsed = self.parser.parse_request("GET", full_url, {}, "")
                             parsed['source'] = 'js_inference'
                             if parsed['spec_hash'] not in seen_hashes:
                                seen_hashes.add(parsed['spec_hash'])
                                endpoints.append(parsed)

            # 3. Fallback: Generic Static Analysis (Regex)
            # Find patterns like: fetch('/api/...') or url = '/doc/...' or `/doc/${id}`
            content = await page.content()
            potential_paths = set(re.findall(r"['\"`](/[a-zA-Z0-9_\-\/{}$]+)['\"`]", content))
            
            for path in potential_paths:
                if len(path) > 1 and not path.startswith('//') and not path.startswith('/ '):
                    full_url = f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}{path}"
                    parsed = self.parser.parse_request("GET", full_url, {}, "")
                    parsed['source'] = 'static_analysis'
                    if parsed['spec_hash'] not in seen_hashes:
                        seen_hashes.add(parsed['spec_hash'])
                        endpoints.append(parsed)

            # 4. Process Forms (HTML Forms)
            for form in dom_data.get('forms', []):
                # Construct form endpoint
                target_url = urllib.parse.urljoin(url, form['action'])
                # Inputs to params
                body = None
                if form['method'].upper() == 'POST':
                    # Rough representation for parser, JSON not strictly correct but works for scraping
                    body = "{" + ",".join([f'"{inp["name"]}": "value"' for inp in form['inputs']]) + "}"
                
                # For GET, add to URL? 
                # Let's just use parser logic with a dummy body or header to trigger param inference
                # Or create custom parsed dict
                
                # Use parser for consistency
                parsed = self.parser.parse_request(form['method'].upper(), target_url, {}, body)
                
                # Manually fix up types based on input type if simple
                for inp in form['inputs']:
                   # Find param and update type if input type is specific
                   pass # Let inference handle for now or refine later
                
                parsed['source'] = 'html_form'
                if parsed['spec_hash'] not in seen_hashes:
                    seen_hashes.add(parsed['spec_hash'])
                    endpoints.append(parsed)

            # 5. Process Links with Params (HTML Anchors)
            for link in dom_data.get('links', []):
                parsed = self.parser.parse_request("GET", link, {}, "")
                if parsed['parameters']: # Only consider links with params as interesting endpoints for scan?
                     parsed['source'] = 'html_anchor'
                     if parsed['spec_hash'] not in seen_hashes:
                        seen_hashes.add(parsed['spec_hash'])
                        endpoints.append(parsed)

            # Deduplication: Prefer specific types over generic 'string'
            # e.g. /doc/{int} > /doc/{string}
            endpoints = self._deduplicate_endpoints(endpoints)

            return {
                "url": url,
                "title": await page.title(),
                "status": response.status,
                "links": dom_data['links'],
                "forms": dom_data['forms'],
                "endpoints": endpoints
            }

            
        except Exception as e:
            logger.error("crawler.page_failed", url=url, error=str(e))
            return {"url": url, "error": str(e), "links": []}
        finally:
            await page.close()

    def _deduplicate_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Refines the list of endpoints by removing generic variants if a specific one exists.
        e.g. If both /doc/{int} and /doc/{string} exist, keep /doc/{int}.
        """
        # Group by "Method + Abstract Path"
        # Abstract Path: Replace {int}, {string}, {uuid} -> {param}
        grouped = {}
        
        for ep in endpoints:
            # Create abstract signature
            abstract_path = ep['url'] # It already has {type} in it from SemanticParser
            for t in ['int', 'string', 'uuid', 'bool', 'float', 'email']:
                abstract_path = abstract_path.replace(f"{{{t}}}", "{param}")
            
            signature = f"{ep['method']}|{abstract_path}"
            if signature not in grouped:
                grouped[signature] = []
            grouped[signature].append(ep)
            
        final_list = []
        
        # Priority: uuid > int > bool > float > email > string
        type_priority = {'uuid': 5, 'int': 4, 'bool': 3, 'float': 2, 'email': 2, 'string': 1, 'json': 1}

        for sig, variants in grouped.items():
            if len(variants) == 1:
                final_list.append(variants[0])
                continue
            
            # Select best variant
            # We score each variant based on its parameters' types
            best_variant = None
            max_score = -1
            
            for var in variants:
                score = 0
                for param in var['parameters']:
                    ptype = param['type']
                    score += type_priority.get(ptype, 1)
                
                if score > max_score:
                    max_score = score
                    best_variant = var
                elif score == max_score:
                    # Tie-breaker? Just keep current or first.
                    # Maybe prefer the one that is NOT string if possible?
                    pass
            
            if best_variant:
                final_list.append(best_variant)
                
        return final_list

    def _is_allowed_scope(self, url: str, base_domain: str) -> bool:
        try:
            return urllib.parse.urlparse(url).netloc == base_domain
        except: return False

    def _is_blacklisted(self, url: str) -> bool:
        for pattern in self.blacklist:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
