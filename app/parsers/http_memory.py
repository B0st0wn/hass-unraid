"""
HTTP-based memory polling for Unraid.
Polls dashboard pages to extract RAM, Flash, Log, and Docker usage percentages.
"""
import httpx
import re
from typing import Optional, Dict


async def fetch_memory_http(server, create_config: bool = False):
    """
    Fetch memory usage data by polling Unraid's dashboard page.
    This works even when WebSocket isn't sending updates.
    """
    try:
        async with httpx.AsyncClient(verify=False) as client:
            headers = {'Cookie': server.unraid_cookie}

            # Try the main dashboard first
            response = await client.get(
                f'{server.unraid_url}/Dashboard',
                headers=headers,
                timeout=30.0,
                follow_redirects=True
            )

            # Check if we got redirected to login
            if '/login' in str(response.url):
                server.logger.warning('HTTP memory fetch: Session expired, need to refresh cookie')
                return

            if response.status_code != 200:
                server.logger.error(f"HTTP memory fetch failed: HTTP {response.status_code}")
                return

            # Parse the HTML response
            content = response.text
            usage = extract_memory_from_html(server, content)

            if usage:
                # Publish sensors
                for name, percent in usage.items():
                    payload = {
                        'name': f'{name} Usage',
                        'unit_of_measurement': '%',
                        'icon': 'mdi:memory',
                        'state_class': 'measurement'
                    }
                    server.mqtt_publish(payload, 'sensor', percent, create_config=create_config, retain=True)

                server.logger.debug(f"HTTP memory: Published {len(usage)} sensors")
            else:
                server.logger.warning("HTTP memory: No memory data found in dashboard")

    except httpx.RequestError as e:
        server.logger.error(f"HTTP memory request failed: {e}")
    except Exception:
        server.logger.exception("Failed to fetch memory data via HTTP")


def extract_memory_from_html(server, html: str) -> Dict[str, int]:
    """
    Extract memory usage percentages from dashboard HTML.
    Returns dict like: {'RAM': 45, 'Flash': 12, 'Log': 5, 'Docker': 18}
    """
    usage = {}

    # Pattern 1: Look for percentage values near memory labels
    # Example: <td>RAM:</td><td>45%</td>
    # Example: <span>Memory</span><span>45 %</span>
    patterns = [
        # Direct label: percentage format
        r'(RAM|Memory|Flash|Boot|Log|Logs|Syslog|Docker|Containers)[^<>]*?[:=]?\s*(\d+(?:\.\d+)?)\s*%',

        # Separate tags format
        r'<[^>]*>(RAM|Memory|Flash|Boot|Log|Logs|Syslog|Docker|Containers)[^<>]*?</[^>]*>[\s\S]{0,100}?(\d+(?:\.\d+)?)\s*%',

        # Data attribute format
        r'data-[^=]*=(RAM|Memory|Flash|Boot|Log|Logs|Syslog|Docker|Containers)[^>]*>(\d+(?:\.\d+)?)\s*%',

        # JavaScript variable format
        r'var\s+(ram|memory|flash|log|docker)[^=]*=\s*["\']?(\d+(?:\.\d+)?)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            label, value = match[0], match[1]
            normalized_label = normalize_memory_label(label)

            if normalized_label and normalized_label not in usage:
                try:
                    percent = int(float(value))
                    if 0 <= percent <= 100:
                        usage[normalized_label] = percent
                        server.logger.debug(f"HTTP memory: Found {normalized_label}={percent}% via pattern")
                except (ValueError, IndexError):
                    continue

    return usage


def normalize_memory_label(label: str) -> Optional[str]:
    """Normalize memory type labels to standard names"""
    label = label.strip().lower()

    if label in ('ram', 'memory'):
        return 'RAM'
    if label in ('flash', 'boot'):
        return 'Flash'
    if label in ('log', 'logs', 'syslog'):
        return 'Log'
    if label in ('docker', 'containers'):
        return 'Docker'

    return None
