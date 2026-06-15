#!/usr/bin/env python3
"""Edit a copied OpenClaw config into an isolated second-instance config.

Usage:
  python3 clone_config.py <config_path> --port 18790 --workspace /path/ws \
      [--drop-channel octo] [--drop-channel discord] [--keep-token]

What it does (safe, idempotent):
  - removes each --drop-channel from channels{} and from bindings[]
  - removes dropped channels from plugins.entries{} and plugins.allow[]
  - sets gateway.port
  - sets agents.defaults.workspace
  - regenerates gateway.auth.token (unless --keep-token)
  - clears wizard markers so the clone re-onboards cleanly

Does NOT touch providers, mcp, sub-agents, skill toggles -> clone keeps same setup.
"""
import argparse, json, secrets, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--workspace', required=True)
    ap.add_argument('--drop-channel', action='append', default=[], dest='drop')
    ap.add_argument('--keep-token', action='store_true')
    a = ap.parse_args()

    with open(a.config) as f:
        d = json.load(f)

    for ch in a.drop:
        if 'channels' in d and ch in d['channels']:
            del d['channels'][ch]
            print(f'removed channels.{ch}')
        if isinstance(d.get('bindings'), list):
            before = len(d['bindings'])
            d['bindings'] = [b for b in d['bindings']
                             if (b.get('match', {}) or {}).get('channel') != ch]
            if len(d['bindings']) != before:
                print(f'bindings: {before} -> {len(d["bindings"])} (dropped {ch})')
        pl = d.get('plugins', {})
        if isinstance(pl.get('entries'), dict) and ch in pl['entries']:
            del pl['entries'][ch]
            print(f'removed plugins.entries.{ch}')
        if isinstance(pl.get('allow'), list) and ch in pl['allow']:
            pl['allow'] = [x for x in pl['allow'] if x != ch]
            print(f'removed {ch} from plugins.allow')

    if d.get('channels') == {}:
        del d['channels']
    if d.get('bindings') == []:
        del d['bindings']

    d.setdefault('gateway', {})['port'] = a.port
    print(f'gateway.port = {a.port}')

    if not a.keep_token:
        d['gateway'].setdefault('auth', {})['token'] = secrets.token_hex(24)
        print('gateway.auth.token = (regenerated)')

    d.setdefault('agents', {}).setdefault('defaults', {})['workspace'] = a.workspace
    print(f'workspace = {a.workspace}')

    d.pop('wizard', None)

    with open(a.config, 'w') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print('saved', a.config)
    print('channels now:', list(d.get('channels', {}).keys()) or '(none)')


if __name__ == '__main__':
    sys.exit(main())
