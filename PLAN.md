# See - Phone OSINT Tool - Plan de Implementación

> **Nota**: este es el plan histórico original. El estado real del proyecto
> (proveedores implementados, comandos, configuración) vive en `README.md`
> y `ARCHITECTURE.md`. Las APIs marcadas como "CallTracer" se sustituyeron
> por el scraping defensivo de Should I Answer (sin API pública fiable).

## Visión General

**See** es una herramienta CLI en Python para obtener información en tiempo real de números de teléfono usando APIs online.

## Stack

- Python ≥3.11
- Typer (CLI)
- Rich (terminal output)
- httpx (HTTP async)
- phonenumbers (parser)
- Pydantic (validation)

## APIs

| API | Free Tier | Datos |
|-----|-----------|-------|
| NumVerify | 100/mes | Carrier, validación, location, type |
| HIBP | Key de pago (3s delay) | Breaches |
| Should I Answer | Sin API (scraping público) | Spam reports |

## Estructura

```
see/
├── src/see/
│   ├── cli.py
│   ├── core/
│   │   ├── parser.py
│   │   └── aggregator.py
│   ├── modules/
│   │   ├── base.py
│   │   ├── phonenumbers_mod.py
│   │   └── numverify_mod.py
│   ├── output/
│   │   ├── json_formatter.py
│   │   └── rich_display.py
│   └── utils/
│       ├── config.py
│       ├── http_client.py
│       └── logger.py
├── tests/
├── pyproject.toml
└── config.example.yaml
```

## Comandos

```bash
see scan +34612345678      # Lookup completo
see carrier +34612345678   # Solo carrier
see validate +34612345678  # Validar
see config --set numverify=KEY
see credits                # Ver créditos
```

## Fases

1. ✅ Setup proyecto
2. ✅ Core (parser, config, http_client, logger)
3. ⏳ Módulo base
4. ⏳ Módulo phonenumbers
5. ⏳ Módulo NumVerify
6. ⏳ Output JSON
7. ⏳ Rich display
8. ⏳ CLI completa
9. ⏳ Tests
10. ⏳ README

## Config

```yaml
api_keys:
  numverify: "YOUR_KEY"
```

Env: `SEE_NUMVERIFY_KEY=xxx`
