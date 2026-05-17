# stackpulse

A terminal dashboard for visualizing Docker Compose service health and resource usage in real time.

---

## Installation

```bash
pip install stackpulse
```

Or install from source:

```bash
git clone https://github.com/yourname/stackpulse.git && cd stackpulse && pip install .
```

---

## Usage

Navigate to a directory containing a `docker-compose.yml` file and run:

```bash
stackpulse
```

You can also point it at a specific Compose file:

```bash
stackpulse --file /path/to/docker-compose.yml
```

The dashboard will display CPU usage, memory consumption, network I/O, and health status for each service, refreshing every second.

**Keyboard shortcuts:**

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Force refresh |
| `↑ / ↓` | Navigate services |

---

## Requirements

- Python 3.8+
- Docker Engine with Compose plugin (or `docker-compose` v1.x)

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any significant changes.

---

## License

This project is licensed under the [MIT License](LICENSE).