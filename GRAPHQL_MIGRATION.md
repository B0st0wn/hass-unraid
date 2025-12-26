# GraphQL Migration Guide

## Overview

This Unraid Home Assistant integration now supports **GraphQL mode** as the primary data collection method, replacing the legacy WebSocket-based approach. GraphQL provides better structured data, more comprehensive information, and improved reliability.

## Key Benefits

### 1. **Docker Container Status Monitoring**
- ✅ **NEW**: Binary sensors for each Docker container showing running/stopped state
- Container details: Image, ports, auto-start configuration
- Real-time status updates

### 2. **Virtual Machine Monitoring**
- ✅ **IMPROVED**: Better state detection (running, shut off, paused)
- More accurate vCPU and memory reporting
- UUID and architecture information

### 3. **Enhanced Data Collection**
- **Array Status**: Comprehensive array health and capacity metrics
- **Parity Checks**: Historical parity check data with status and errors
- **Shares**: User share usage and configuration
- **UPS**: Battery level, load percentage, runtime estimates
- **Disks**: Size, usage, temperature, filesystem information

## Migration Steps

### 1. **Prerequisites**
- Unraid 7.2+ with GraphQL API enabled
- API key generated (Settings → Management Access → API Keys)

### 2. **Configuration**

Update your `docker-compose.yaml` or environment variables:

```yaml
services:
  hass-unraid:
    environment:
      # Enable GraphQL mode (default: true)
      - USE_GRAPHQL=true

      # Add your Unraid API key
      - UNRAID_API_KEY=your_api_key_here

      # Optional: Adjust scan interval (default: 30 seconds)
      - SCAN_INTERVAL=30
```

Or in your configuration file:

```ini
[unraid]
host = your-unraid-server
port = 443
ssl = true
username = your_username
password = your_password
api_key = your_api_key_here  # Add this line
scan_interval = 30
```

### 3. **Generate API Key**

1. Navigate to **Settings → Management Access** in Unraid WebGUI
2. Scroll to **API Keys** section
3. Click **Generate API Key**
4. Give it a name (e.g., "Home Assistant Integration")
5. Copy the generated key to your configuration

### 4. **Switch Modes**

The integration supports both modes via the `USE_GRAPHQL` environment variable:

- **GraphQL Mode** (recommended): `USE_GRAPHQL=true` (default)
- **WebSocket Mode** (legacy): `USE_GRAPHQL=false`

### 5. **Restart the Container**

```bash
docker-compose down
docker-compose up -d
```

## New Sensors Available

### Docker Containers
Each Docker container gets:
- `binary_sensor.docker_<container_name>_state` - Running/stopped state
- Attributes:
  - `container_id` - Short container ID
  - `image` - Container image
  - `status` - Detailed status
  - `state` - Current state (running, exited, etc.)
  - `auto_start` - Auto-start configuration
  - `port_mappings` - Port mapping list

### Virtual Machines
Each VM gets:
- `binary_sensor.vm_<vm_name>_state` - Running/stopped state
- `sensor.vm_<vm_name>_vcpus` - Virtual CPU count
- `sensor.vm_<vm_name>_memory` - Memory allocation (MB)
- Attributes:
  - `uuid` - VM UUID
  - `architecture` - CPU architecture
  - `emulator` - Emulator type
  - `state` - Current state

### Array & Parity
- `sensor.array_state` - Array state (STARTED, STOPPED, etc.)
- `sensor.array_usage` - Array usage percentage
  - Attributes: `total_tb`, `used_tb`, `free_tb`
- `sensor.parity_<name>_status` - Parity disk status
- `sensor.parity_<name>_temperature` - Parity disk temperature
- `sensor.last_parity_check` - Last parity check status
  - Attributes: `duration_seconds`, `speed_mb_s`, `errors`, timestamps

### Shares
- `sensor.share_<name>_usage` - Share usage percentage
  - Attributes: `size_gb`, `used_gb`, `free_gb`, `allocator`, `use_cache`

### UPS
- `sensor.ups_<name>_battery` - Battery level (%)
- `sensor.ups_<name>_load` - Load percentage
- `sensor.ups_<name>_runtime` - Estimated runtime (minutes)
  - Attributes: `model`, `status`, `health`, voltages

## Troubleshooting

### GraphQL Queries Failing

**Symptoms**: Logs show "GraphQL: HTTP 401" or "GraphQL: HTTP 403"

**Solution**:
1. Verify API key is correctly configured
2. Check API key is still valid in Unraid settings
3. Ensure Unraid version is 7.2 or higher

### No Docker/VM Sensors Appearing

**Symptoms**: Docker or VM sensors don't show up in Home Assistant

**Solution**:
1. Check `USE_GRAPHQL=true` is set
2. Verify containers/VMs exist on Unraid server
3. Check logs for GraphQL errors
4. Ensure API key has proper permissions

### Session Cookie Errors

**Symptoms**: Logs show session refresh failures

**Solution**:
1. Verify username and password are correct
2. Check network connectivity to Unraid server
3. Ensure SSL certificate is valid (or disable SSL verification)

### Slow Updates

**Symptoms**: Sensors update slowly or inconsistently

**Solution**:
1. Adjust `scan_interval` (default: 30 seconds)
2. Check server performance - GraphQL queries are more intensive than WebSocket
3. Monitor Unraid server load

## Performance Considerations

### GraphQL vs WebSocket

| Aspect | GraphQL | WebSocket |
|--------|---------|-----------|
| **Data Structure** | Structured JSON | INI-formatted text |
| **Latency** | Polling-based (~30s) | Real-time push |
| **Completeness** | More comprehensive | Limited fields |
| **Server Load** | Higher (polling) | Lower (push) |
| **Reliability** | Better error handling | Connection sensitive |
| **Docker/VM Status** | ✅ Yes | ❌ No |

### Recommendations

- **Use GraphQL** for:
  - Docker container monitoring
  - VM status tracking
  - Comprehensive metrics
  - Unraid 7.2+ installations

- **Use WebSocket** for:
  - Lower latency requirements
  - Older Unraid versions (<7.2)
  - Minimal server load

### Optimization Tips

1. **Adjust scan intervals** per data type:
   - Fast-changing data (Docker, VMs): 30 seconds
   - Slow-changing data (Shares): 3600 seconds (1 hour)

2. **Monitor server load**: GraphQL queries are more CPU-intensive

3. **Use API keys**: More secure and efficient than cookie-based auth

## Reverting to WebSocket Mode

If you need to revert to WebSocket mode:

1. Set `USE_GRAPHQL=false` in environment variables
2. Restart the container
3. WebSocket-based sensors will resume
4. Note: Docker/VM running status sensors will not be available

## Architecture Details

### GraphQL Query Structure

The integration uses separate polling loops for different data types:

1. **Disks** (`graphql_disk_loop`): Disk usage, temperatures, filesystem info
2. **Docker** (`graphql_docker_loop`): Container states, images, ports
3. **VMs** (`graphql_vms_loop`): VM states, CPU, memory allocations
4. **Array** (`graphql_array_loop`): Array status, capacity, parity checks
5. **Shares** (`graphql_shares_loop`): User share usage and config
6. **UPS** (`graphql_ups_loop`): UPS battery, load, runtime

### File Structure

```
app/parsers/
├── graphql_client.py       # Base GraphQL client
├── graphql_docker.py       # Docker container queries
├── graphql_vms.py          # Virtual machine queries
├── graphql_array.py        # Array status & parity queries
├── graphql_shares.py       # User shares queries
├── graphql_ups.py          # UPS device queries
└── graphql_disks.py        # Disk queries (existing, refactored)
```

## Known Limitations

1. **API Availability**: Requires Unraid 7.2+
2. **Polling Latency**: Updates happen every `scan_interval` (default 30s)
3. **Schema Changes**: Unraid GraphQL schema may change between versions
4. **Network Requirements**: Requires stable network connection to Unraid server

## Future Enhancements

- [ ] GraphQL subscriptions for real-time updates
- [ ] Configurable polling intervals per data type
- [ ] Automatic fallback from GraphQL to WebSocket
- [ ] Support for Unraid Connect remote access
- [ ] Network throughput metrics via GraphQL
- [ ] CPU and memory metrics via GraphQL (currently via psutil)

## Support

If you encounter issues:

1. Enable debug logging in Home Assistant
2. Check container logs: `docker logs hass-unraid`
3. Verify GraphQL endpoint: `https://your-unraid/graphql`
4. Test API key with GraphQL playground (Settings → Developer Options)
5. Open an issue on GitHub with logs and configuration

## References

- [Unraid API Documentation](https://docs.unraid.net/API/)
- [GraphQL Official Site](https://graphql.org/)
- [Home Assistant MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/)
