# See-OSIN Architecture

Modular OSINT framework for phone number and email intelligence.

## Project Structure

```
see/
├── src/see/
│   ├── cli.py                    # CLI entry point
│   ├── core/
│   │   ├── engine.py             # SeeEngine orchestrator
│   │   ├── registry.py           # Module registry
│   │   ├── parser.py             # Phone number parsing
│   │   ├── types.py              # Result dataclasses
│   │   └── constants.py          # Shared constants
│   ├── modules/
│   │   ├── base.py               # BaseModule + BaseProvider ABCs
│   │   ├── phones/
│   │   │   ├── domain.py         # PhoneDomain orchestrator
│   │   │   └── providers/
│   │   │       ├── phonenumbers_provider.py  # Offline lookup
│   │   │       ├── numverify.py              # NumVerify API
│   │   │       ├── numlookup.py              # NumLookup API
│   │   │       └── abstract.py               # Abstract API
│   │   └── emails/
│   │       ├── domain.py         # EmailDomain orchestrator
│   │       └── providers/
│   │           ├── base.py           # BaseEmailProvider
│   │           ├── holehe.py         # Holehe breach check
│   │           ├── disposable.py     # Disposable email check
│   │           ├── social.py         # Social media (26+ platforms)
│   │           ├── intelligence.py   # DNS/MX/SPF/DKIM analysis
│   │           ├── reverse.py        # Email-to-phone lookup
│   │           ├── smtp.py           # SMTP verification
│   │           ├── gravatar.py       # Gravatar lookup
│   │           ├── hunter.py         # Hunter.io API
│   │           └── dehashed.py       # DeHashed API
│   ├── output/
│   │   ├── rich_display.py       # Terminal display
│   │   └── json_formatter.py     # JSON output
│   └── utils/
│       ├── config.py             # Configuration loader
│       ├── http_client.py        # HTTP client with Tor
│       ├── logger.py             # Logging
│       ├── tor_client.py         # Tor integration
│       └── hashing.py            # MD5/SHA256 utilities
├── tests/
├── pyproject.toml
├── config.yaml                   # Config (empty keys)
├── config.example.yaml           # Example config
├── .env.example                  # Environment variables template
├── LICENSE                       # MIT License
└── CONTRIBUTING.md               # Contribution guidelines
```

## Architecture Principles

### 1. Module Registry Pattern
Each domain (phones, emails) has a registry that auto-discovers and manages providers.

```python
# core/registry.py
class ModuleRegistry:
    def register(self, module): ...
    def get_module(self, name): ...
    def get_available_modules(self): ...
```

### 2. Domain-Based Organization
Modules are organized by domain, not by provider:

- `phones/` - All phone-related providers
- `emails/` - All email-related providers

### 3. Provider Pattern
Each provider implements a common interface:

```python
class BaseProvider(ABC):
    @property
    def name(self) -> str: ...
    
    @property
    def is_available(self) -> bool: ...
    
    async def get_data(self, target, config): ...
```

### 4. Configuration via Environment Variables
API keys are stored in environment variables, NOT in config files:

```python
# .env file
NUMVERIFY_API_KEY=your_key
ABSTRACT_API_KEY=your_key
DEHASHED_API_KEY=your_key
```

### 5. Tor Integration
All HTTP requests support optional Tor routing:

```python
async with HTTPClient(use_tor=config.tor.enabled) as client:
    data = await client.get(url)
```

### 6. Non-Blocking DNS
DNS calls use `asyncio.to_thread()` to prevent event loop blocking:

```python
async def _get_mx_records(self, domain):
    def resolve():
        return dns.resolver.resolve(domain, 'MX')
    return await asyncio.to_thread(resolve)
```

## Data Flow

```
User Input
    ↓
CLI Parser (cli.py)
    ↓
Engine (engine.py)
    ↓
Registry → Domain → Providers
    ↓
Result Aggregation
    ↓
Display/JSON Output
```

## Adding a New Provider

1. Create provider class in appropriate domain folder
2. Implement `BaseProvider` interface
3. Add `@property` for `is_available`
4. Register in `__init__.py`
5. Provider auto-discovered by registry

## Security Considerations

- API keys never committed to repository
- Passwords excluded from DeHashed output by default
- All HTTP requests support Tor routing
- Rate limiting built into providers
- Input validation on all user inputs
