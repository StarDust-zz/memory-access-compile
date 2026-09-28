# memory-access-compile

Synergy deep-dive: memory **access compile** joining
[access-dont-dump](https://github.com/StarDust-zz/access-dont-dump),
[answerable-memory](https://github.com/StarDust-zz/answerable-memory),
and [cartridge-retrieves-forgets](https://github.com/StarDust-zz/cartridge-retrieves-forgets)
into one measurable `serve | hold` action.

## Run

```bash
python3 experiment.py
```

Expect `7/7 assertions passed`, exit 0.

Stdlib only. No network, GPU, or vendor API in the 7/7 path.

## Layout

| File | Role |
|------|------|
| `experiment.py` | Access-compile gate + 7 join assertions |
| `access_stub.py` | LOOKUP\|COMPOSE\|REPLAY algebra (from access-dont-dump) |
| `answerable_stub.py` | MSC/MMC WM algebra (from answerable-memory) |
| `cartridge_stub.py` | Document homes algebra (from cartridge-retrieves-forgets) |
| `DESCRIPTION.md` | Claim, falsifier, object algebra, synergy |
| `KEEPERS.txt` | What is now object vs still hunch |

## License

MIT — see [LICENSE](LICENSE).
