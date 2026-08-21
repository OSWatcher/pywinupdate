# pywinupdate

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Python-controlled search and installation of Windows updates via WinRM and Ansible. Searches for available Windows updates on a remote host and installs them one by one, rebooting and resuming as needed.

Part of the [OSWatcher](https://github.com/OSWatcher) project, where it's used to install updates on Windows VMs one at a time so each update can be captured as a separate snapshot.

## Installation

```bash
pip install pywinupdate
```

## Usage

```bash
pywinupdate search <host> --user <user> --password <password>
pywinupdate update <host> --user <user> --password <password> [--one]
```

`--user`/`--password` default to `vagrant`/`vagrant` (the standard Vagrant box credentials) and `--port` defaults to `5985`. Run `pywinupdate --help` for the full list of options.

## Requirements

- A remote Windows host reachable over WinRM
- Ansible (installed automatically as a dependency)

## Development

```bash
poetry install
poetry run poe ccode   # format + lint
poetry run poe type    # mypy
```

## License

[Apache 2.0](LICENSE)
