# See - Phone Number OSINT Tool

A powerful Python CLI tool for phone number investigation using online APIs with Tor support for anonymity.

## Features

- Phone number validation and parsing
- Carrier detection
- Country and timezone lookup
- Line type identification (mobile, fixed-line, VoIP, etc.)
- Owner lookup (with API keys)
- Social media profile detection
- Google dorks for OSINT
- **Tor proxy support** for anonymous requests
- **Automatic circuit rotation**
- JSON output for pipeline integration
- Rich terminal display

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd see

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Install with Tor support (optional)
pip install -e ".[tor]"
```

### System Requirements for Tor

```bash
# Debian/Ubuntu
sudo apt install tor

# macOS
brew install tor

# Start Tor service
sudo systemctl start tor
# or
brew services start tor
```

## Quick Start

```bash
# Scan a phone number
see scan +34612345678

# Find owner information
see owner +34612345678

# Validate a phone number
see validate +34612345678

# Get carrier information
see carrier +34612345678

# Check Tor status
see tor-status
```

## Anonymous Usage with Tor

```bash
# Single request through Tor
see owner +34612345678 --tor

# Scan through Tor
see scan +34612345678 --tor

# Force direct connection (ignore config)
see owner +34612345678 --no-tor
```

### Tor Configuration (config.yaml)

```yaml
tor:
  enabled: false              # Enable by default
  socks_port: 9050            # Tor SOCKS port
  control_port: 9051          # For circuit rotation
  max_requests_per_circuit: 10  # Rotate every N requests
  auto_rotate: true           # Auto-rotate when max reached
  exit_countries: []          # Empty = random, or ["us", "de"]
```

### Environment Variables

```bash
export SEE_TOR_ENABLED=true
export SEE_NUMVERIFY_KEY=your_key
export SEE_ABSTRACT_KEY=your_key
```

## Configuration

### API Keys

For enhanced data (owner name, location), configure API keys:

```bash
# Set NumVerify API key
see config --set numverify=YOUR_API_KEY

# Set Abstract API key
see config --set abstract=YOUR_API_KEY
```

### Get Free API Keys

- **NumVerify**: https://numverify.com (100 requests/month free)
- **Abstract**: https://abstractapi.com (100 requests/month free)

## Commands

| Command | Description | Tor Support |
|---------|-------------|-------------|
| `see scan <phone>` | Full OSINT scan | ✓ |
| `see owner <phone>` | Find owner info | ✓ |
| `see validate <phone>` | Validate phone format | - |
| `see carrier <phone>` | Get carrier info | ✓ |
| `see tor-status` | Check Tor connection | - |
| `see config --show` | Show configuration | - |
| `see version` | Show version | - |

## Output Formats

```bash
# JSON output
see scan +34612345678 --format json

# Display output (default)
see scan +34612345678 --format display

# Both JSON and display
see scan +34612345678 --format both

# Save to file
see scan +34612345678 --output results.json
```

## Project Structure

```
see/
├── src/see/
│   ├── cli.py                 # CLI entry point
│   ├── core/
│   │   ├── parser.py          # Phone number parsing
│   │   └── aggregator.py      # Module orchestration
│   ├── modules/
│   │   ├── base.py            # Module interface
│   │   ├── phonenumbers_mod.py # Offline lookup
│   │   ├── numverify_mod.py   # NumVerify API
│   │   ├── abstract_mod.py    # Abstract Person API
│   │   ├── maigret_mod.py     # Social media OSINT
│   │   └── google_dorks_mod.py # Search engine dorks
│   ├── output/
│   │   ├── json_formatter.py  # JSON output
│   │   └── rich_display.py    # Terminal display
│   └── utils/
│       ├── config.py          # Configuration
│       ├── http_client.py     # HTTP client with Tor
│       ├── logger.py          # Logging
│       └── tor_client.py      # Tor client & rotation
├── tests/
├── pyproject.toml
└── config.example.yaml
```

## Security Features

- **Tor Integration**: All requests can be routed through Tor
- **Circuit Rotation**: Automatic IP rotation every N requests
- **Rate Limiting**: Built-in rate limiting for API calls
- **Input Validation**: Phone number validation before processing
- **No Data Storage**: Results not stored unless explicitly saved

## License

MIT License
