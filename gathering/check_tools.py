#!/usr/bin/env python3
"""Repeat the reviewed offline checks without changing any line's files."""
import json
from pathlib import Path
import subprocess
import sys


def checks():
    commands = []
    for number, tool in [(1, 'zto-band'), (2, 'allowance-lens'), (3, 'code-lens'), (4, 'call-rehearsal')]:
        commands.append((f'line-{number}-suite', ['-m', 'unittest', 'discover', '-s',
                         f'line-{number}/tools/{tool}', '-p', 'test_*.py', '-v'], 0))
    commands.extend([
        ('line-1-demo', ['line-1/tools/zto-band/zto_band.py', '--snapshot',
                        'line-1/tools/zto-band/observation.json', '--amount', '1'], 0),
        ('line-1-reverse', ['line-1/tools/zto-band/zto_band.py', '--snapshot',
                           'line-1/tools/zto-band/observation.json', '--input', 'IMD', '--amount', '0.1'], 0),
        ('line-1-outside-interval', ['line-1/tools/zto-band/zto_band.py', '--snapshot',
                                   'line-1/tools/zto-band/observation.json', '--amount', '1000000'], 2),
        ('line-2-demo', ['line-2/tools/allowance-lens/allowance_lens.py'], 0),
        ('line-3-zto', ['line-3/tools/code-lens/code_lens.py', '--verify',
                       'line-3/tools/code-lens/zto-observation.json'], 0),
        ('line-3-imd', ['line-3/tools/code-lens/code_lens.py', '--verify',
                       'line-3/tools/code-lens/imd-observation.json'], 0),
        ('line-4-zto', ['line-4/tools/call-rehearsal/rehearse.py', 'replay',
                       'line-4/tools/call-rehearsal/zto-observation.json'], 0),
        ('line-4-imd', ['line-4/tools/call-rehearsal/rehearse.py', 'replay',
                       'line-4/tools/call-rehearsal/imd-observation.json'], 0),
        ('line-4-revert', ['line-4/tools/call-rehearsal/rehearse.py', 'replay',
                          'line-4/tools/call-rehearsal/zto-revert-observation.json'], 1),
        ('shared-context-suite', ['-m', 'unittest', 'discover', '-s', 'shared/contract-context',
                                  '-p', 'test_*.py', '-v'], 0),
        ('shared-context-demo', ['shared/contract-context/context.py', 'demo'], 2),
    ])
    return commands


def main():
    root = Path.cwd().resolve()
    if not all((root / f'line-{n}/GOAL.md').is_file() for n in range(1, 5)):
        raise ValueError('run from the workspace root')
    results = []
    for name, args, expected in checks():
        command = [sys.executable, '-B'] + args
        completed = subprocess.run(command, text=True, capture_output=True, timeout=30, cwd=root)
        result = {'name': name, 'command': ['python3', '-B'] + args,
                  'expected_exit': expected, 'exit': completed.returncode,
                  'passed': completed.returncode == expected}
        if args[0] == '-m':
            result['test_output'] = completed.stderr
        else:
            result['stdout'] = json.loads(completed.stdout) if completed.stdout else None
            result['stderr'] = completed.stderr
        if name == 'line-2-demo':
            expected_report = json.loads((root / 'line-2/tools/allowance-lens/example-report.json').read_text())
            result['matches_recorded_report'] = result['stdout'] == expected_report
            result['passed'] = result['passed'] and result['matches_recorded_report']
        results.append(result)
    print(json.dumps({'schema': 'gathering-local-checks-v1',
                      'authority': 'local contributor checks, not independent certification',
                      'all_passed': all(r['passed'] for r in results), 'checks': results}, indent=2))
    return 0 if all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
