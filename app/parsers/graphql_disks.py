"""
GraphQL disk data fetcher for Unraid 7.2+
Fetches disk usage information from Unraid's GraphQL API
"""
import json
import httpx


async def fetch_disk_data_graphql(server):
    """
    Fetch disk data from Unraid GraphQL API
    Returns INI-formatted string compatible with existing disk parser
    """
    graphql_query = {
        "query": """
            query {
              array {
                disks {
                  name
                  device
                  size
                  status
                  temp
                  fsType
                  fsSize
                  fsUsed
                  fsFree
                }
                caches {
                  name
                  device
                  size
                  status
                  temp
                  fsType
                  fsSize
                  fsUsed
                  fsFree
                }
              }
            }
        """
    }

    try:
        # Use API key authentication (required for Unraid 7.2+)
        headers = {
            'Content-Type': 'application/json',
        }

        # Add API key if available (Unraid 7.2+), otherwise fall back to cookie
        if server.unraid_api_key:
            headers['x-api-key'] = server.unraid_api_key
        else:
            headers['Cookie'] = server.unraid_cookie

        async with httpx.AsyncClient(verify=False) as http:
            response = await http.post(
                f'{server.unraid_url}/graphql',
                json=graphql_query,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception as e:
                    server.logger.error(f"GraphQL: Failed to parse JSON response: {e}")
                    server.logger.debug(f"GraphQL: Response text: {response.text[:500]}")
                    return None

                # Check if data is a dict before using 'in' operator
                if not isinstance(data, dict):
                    server.logger.error(f"GraphQL: Expected dict response, got {type(data)}: {data}")
                    return None

                if 'data' in data and 'array' in data.get('data', {}):
                    array_data = data['data']['array']
                    all_disks = []

                    # Combine regular disks and cache disks
                    if 'disks' in array_data and array_data['disks']:
                        all_disks.extend(array_data['disks'])
                    if 'caches' in array_data and array_data['caches']:
                        all_disks.extend(array_data['caches'])

                    if all_disks:
                        server.logger.debug(f"GraphQL: Successfully fetched data for {len(all_disks)} disk(s)")
                        return convert_graphql_to_ini(all_disks)
                    else:
                        server.logger.warning("GraphQL: No disk or cache data found")
                        return None
                else:
                    server.logger.warning(f"GraphQL: Unexpected response structure or no disk data")
                    if 'errors' in data:
                        server.logger.error(f"GraphQL errors: {data['errors']}")
                    server.logger.debug(f"GraphQL response: {json.dumps(data, indent=2)}")
                    return None
            else:
                server.logger.error(f"GraphQL: HTTP {response.status_code}: {response.text[:500]}")
                return None

    except httpx.ConnectError:
        server.logger.error("GraphQL: Could not connect to /graphql endpoint")
        return None
    except Exception as e:
        server.logger.exception(f"GraphQL: Failed to fetch disk data: {e}")
        return None


def convert_graphql_to_ini(disks):
    """
    Convert GraphQL disk array to INI format expected by disk parser

    GraphQL provides sizes in 512-byte sectors
    Parser expects values in 1024-byte sectors, so multiply by 512/1024 = 0.5
    """
    ini_sections = []

    for i, disk in enumerate(disks):
        # Extract values with defaults
        name = disk.get('name', f'disk{i}')
        device = disk.get('device', '')
        temp = disk.get('temp', 0)
        status = disk.get('status', '')
        fs_type = disk.get('fsType', '')

        # Size values from GraphQL are in 512-byte sectors
        # Parser expects 1024-byte sectors, so divide by 2
        size_sectors_512 = int(disk.get('size', 0) or 0)
        fs_size_sectors_512 = int(disk.get('fsSize', 0) or 0)
        fs_used_sectors_512 = int(disk.get('fsUsed', 0) or 0)
        fs_free_sectors_512 = int(disk.get('fsFree', 0) or 0)

        # Convert 512-byte sectors to 1024-byte sectors (divide by 2)
        sizesb = size_sectors_512 // 2 if size_sectors_512 else 0
        fssize = fs_size_sectors_512 // 2 if fs_size_sectors_512 else 0
        fsused = fs_used_sectors_512 // 2 if fs_used_sectors_512 else 0
        fsfree = fs_free_sectors_512 // 2 if fs_free_sectors_512 else 0

        # Build INI section
        section = f"[{name}]\n"
        section += f'name="{name}"\n'
        section += f'device="{device}"\n'
        section += f'temp="{temp}"\n'
        section += f'status="{status}"\n'
        section += f'fstype="{fs_type}"\n'
        section += f'sizesb="{sizesb}"\n'
        section += f'fssize="{fssize}"\n'
        section += f'fsused="{fsused}"\n'
        section += f'fsfree="{fsfree}"\n'

        ini_sections.append(section)

    return '\n'.join(ini_sections)
