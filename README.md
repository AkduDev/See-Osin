# See-OSIN

Modular OSINT framework for phone number and email intelligence with Tor support.

## Features

### Phone Intelligence
- Phone number validation and parsing
- Carrier detection (phonenumbers, NumVerify, NumLookup)
- Owner lookup (Abstract API)
- Country and timezone lookup
- Line type identification (mobile, fixed-line, VoIP, etc.)

### Email Intelligence
- Breach data (Holehe, DeHashed)
- Disposable email detection
- Social media profiles (26+ platforms)
- DNS analysis (MX, SPF, DKIM, DMARC)
- SMTP verification
- Gravatar lookup

### Security Features
- **Tor proxy support** for anonymous requests
- **Automatic circuit rotation**
- **API keys via environment variables** (never in config files)
- **Non-blocking DNS** with asyncio
- **Rate limiting** for API calls

## Installation

```bash
# Clone the repository
git clone https://github.com/AkduDev/See-Osin.git
cd See-Osin

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Install with Tor support (optional)
pip install -e ".[tor]"
```

## Quick Start

```bash
# Phone number scan
see phone-scan +34612345678

# Email scan
see email-scan user@example.com

# Validate phone number
see phone-validate +34612345678

# Get carrier info
see phone-carrier +34612345678

# Check breaches
see email-breaches user@example.com

# Check disposable
see email-disposable user@example.com
```

## Configuration

### Environment Variables (Recommended)

```bash
# Create .env file
cp .env.example .env

# Add your API keys
NUMVERIFY_API_KEY=your_key
ABSTRACT_API_KEY=your_key
HUNTER_API_KEY=your_key
DEHASHED_API_KEY=your_key
```

### Get Free API Keys

- **NumVerify**: https://numverify.com (100 requests/month free)
- **Abstract**: https://abstractapi.com (100 requests/month free)
- **Hunter.io**: https://hunter.io (25 searches/month free)
- **DeHashed**: https://dehashed.com (paid)

## Commands

| Command | Description | Tor Support |
|---------|-------------|-------------|
| `see phone-scan <phone>` | Full phone OSINT scan | ✓ |
| `see phone-carrier <phone>` | Get carrier info | ✓ |
| `see phone-owner <phone>` | Find owner info | ✓ |
| `see phone-validate <phone>` | Validate phone format | - |
| `see email-scan <email>` | Full email OSINT scan | ✓ |
| `see email-breaches <email>` | Check breaches | ✓ |
| `see email-social <email>` | Find social profiles | ✓ |
| `see email-disposable <email>` | Check if disposable | - |
| `see scan <target>` | Legacy full scan | ✓ |
| `see version` | Show version | - |

## Output Formats

```bash
# JSON output
see phone-scan +34612345678 --format json

# Display output (default)
see phone-scan +34612345678 --format display

# Save to file
see phone-scan +34612345678 --output results.json
```

## Tor Usage

```bash
# Single request through Tor
see phone-scan +34612345678 --tor

# Force direct connection
see phone-scan +34612345678 --no-tor
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed project structure.

## Security

- API keys stored in environment variables (never committed)
- Passwords excluded from DeHashed output by default
- All HTTP requests support Tor routing
- Non-blocking DNS resolution
- Input validation on all user inputs

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
