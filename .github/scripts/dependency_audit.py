"""Turn pip-audit and npm audit JSON reports into a readable table and a trustworthy exit status.

The audit fails when vulnerabilities are found and also when the report cannot be trusted: the tool
failed, its JSON is missing or has an unknown shape, or it analysed fewer packages than are pinned.
pip-audit, for example, exits 0 with "No known vulnerabilities found" when its input lists nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


class UntrustedReport(Exception):
    """The audit cannot vouch for the dependencies: treat it as a failure, never as a pass."""


@dataclass(frozen=True)
class Finding:
    package: str
    version: str
    scope: str
    severity: str
    advisories: list[str]
    fix: str


def canonical(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def pinned_packages(constraints_text):
    """Return (required, optional) pins; a line with an environment marker may legitimately be skipped."""
    required, optional = {}, {}
    for line in constraints_text.splitlines():
        requirement, _, marker = line.split('#')[0].partition(';')
        if not requirement.strip():
            continue
        pin = re.fullmatch(r'([A-Za-z0-9._-]+)==([^\s=]+)', requirement.strip())
        if not pin:
            raise UntrustedReport(f'unsupported constraints line, expected name==version: {line}')
        (optional if marker.strip() else required)[canonical(pin[1])] = pin[2]
    return required, optional


def direct_requirements(requirements_text):
    """Names declared in requirements files; options such as -r and comments are not packages."""
    lines = (line.split('#')[0].strip() for line in requirements_text.splitlines())
    return {canonical(re.match(r'[A-Za-z0-9._-]+', line)[0]) for line in lines if line and not line.startswith('-')}


def python_findings(report, constraints_text, requirements_text, exit_code):
    required, optional = pinned_packages(constraints_text)
    if not required:
        raise UntrustedReport('the constraints pin no packages, so nothing would be analysed')
    # A truncated constraints file would silently shrink the audit; every declared package must be pinned.
    unpinned = sorted(direct_requirements(requirements_text) - required.keys() - optional.keys())
    if unpinned:
        raise UntrustedReport('declared requirements missing from the constraints: ' + ', '.join(unpinned))
    if not isinstance(report, dict) or not isinstance(report.get('dependencies'), list):
        raise UntrustedReport('pip-audit produced no JSON report with a dependency list')
    skipped = [dep.get('name', '?') for dep in report['dependencies'] if dep.get('skip_reason')]
    if skipped:
        raise UntrustedReport('pip-audit skipped ' + ', '.join(skipped))
    audited = {canonical(dep['name']): dep['version'] for dep in report['dependencies']}
    unaudited = sorted(f'{name}=={version}' for name, version in required.items() if audited.get(name) != version)
    unaudited += sorted(f'{name}=={version}' for name, version in optional.items()
                        if name in audited and audited[name] != version)
    if unaudited:
        raise UntrustedReport('pinned packages not analysed at their pinned version: ' + ', '.join(unaudited))
    findings = []
    for dep in report['dependencies']:
        advisories, fixes = {}, set()
        for vuln in dep.get('vulns', []):
            aliases = ', '.join(sorted(vuln.get('aliases') or []))
            advisories[vuln['id']] = f"{vuln['id']} ({aliases})" if aliases else vuln['id']
            fixes.update(vuln.get('fix_versions') or [])
        if advisories:
            findings.append(Finding(dep['name'], dep['version'], 'production', 'n/a',
                                    [advisories[key] for key in sorted(advisories)],
                                    ', '.join(sorted(fixes)) or 'none published'))
    if exit_code != 0 and not findings:
        raise UntrustedReport(f'pip-audit failed with exit code {exit_code} but reported no vulnerability')
    return findings


def checked_npm_report(report, exit_code, expected_total, label):
    if not isinstance(report, dict):
        raise UntrustedReport(f'npm audit ({label}) produced no JSON report')
    if 'error' in report:
        raise UntrustedReport(f"npm audit ({label}) failed: {report.get('message') or report['error']}")
    if report.get('auditReportVersion') != 2:
        raise UntrustedReport(f"npm audit ({label}) has auditReportVersion {report.get('auditReportVersion')}, "
                              'expected 2')
    total = report.get('metadata', {}).get('dependencies', {}).get('total')
    if total != expected_total:
        raise UntrustedReport(f'npm audit ({label}) analysed {total} packages, package-lock.json has {expected_total}')
    vulnerabilities = report.get('vulnerabilities')
    if not isinstance(vulnerabilities, dict):
        raise UntrustedReport(f'npm audit ({label}) has no vulnerability map')
    if exit_code != 0 and not vulnerabilities:
        raise UntrustedReport(f'npm audit ({label}) failed with exit code {exit_code} but reported no vulnerability')
    return vulnerabilities


def npm_findings(full, production, lockfile, exit_full, exit_production):
    packages = lockfile.get('packages') if isinstance(lockfile, dict) else None
    if not isinstance(packages, dict):
        raise UntrustedReport('package-lock.json has no packages map')
    expected_total = len([path for path in packages if path])
    if not expected_total:
        raise UntrustedReport('package-lock.json lists no packages to audit')
    vulnerabilities = checked_npm_report(full, exit_full, expected_total, 'all dependencies')
    in_production = checked_npm_report(production, exit_production, expected_total, 'production only')
    findings = []
    for name, vuln in sorted(vulnerabilities.items()):
        versions = sorted({packages.get(node, {}).get('version', '?') for node in vuln.get('nodes') or []})
        advisories = [f"{via['title']} ({via['url']})" if isinstance(via, dict) else f'via {via}'
                      for via in vuln.get('via', [])]
        fix = vuln.get('fixAvailable')
        fix = f"{fix['name']} {fix['version']}" if isinstance(fix, dict) else 'npm audit fix' if fix else 'none published'
        findings.append(Finding(name, ', '.join(versions) or '?', 'production' if name in in_production else 'development',
                                vuln.get('severity', '?'), advisories, fix))
    return findings


def render(title, findings, analysed):
    if not findings:
        return f'### {title}\n\nNo known vulnerabilities in {analysed} packages.\n'
    rows = [f'| {f.package} | {f.version} | {f.scope} | {f.severity} | {"<br>".join(f.advisories)} | {f.fix} |'
            for f in findings]
    return '\n'.join([f'### {title}', '', f'{len(findings)} of {analysed} analysed packages have known vulnerabilities.', '',
                      '| Package | Version | Scope | Severity | Advisories | Fixed in |',
                      '| --- | --- | --- | --- | --- | --- |', *rows, ''])


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def publish(text):
    print(text)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as handle:
            handle.write(text + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    python = commands.add_parser('python')
    python.add_argument('--report', required=True)
    python.add_argument('--constraints', required=True)
    python.add_argument('--requirements', nargs='+', required=True)
    python.add_argument('--exit-code', type=int, required=True)
    npm = commands.add_parser('npm')
    npm.add_argument('--full', required=True)
    npm.add_argument('--production', required=True)
    npm.add_argument('--lockfile', required=True)
    npm.add_argument('--exit-full', type=int, required=True)
    npm.add_argument('--exit-production', type=int, required=True)
    args = parser.parse_args(argv)
    title = 'Python dependencies (pip-audit)' if args.command == 'python' else 'Frontend dependencies (npm audit)'
    try:
        if args.command == 'python':
            report = read_json(args.report)
            requirements = '\n'.join(Path(path).read_text(encoding='utf-8') for path in args.requirements)
            findings = python_findings(report, Path(args.constraints).read_text(encoding='utf-8'), requirements,
                                       args.exit_code)
            analysed = len(report['dependencies'])
        else:
            lockfile = read_json(args.lockfile)
            findings = npm_findings(read_json(args.full), read_json(args.production), lockfile,
                                    args.exit_full, args.exit_production)
            analysed = len([path for path in lockfile['packages'] if path])
    except UntrustedReport as error:
        publish(f'### {title}\n\nThe audit cannot be trusted: {error}.\n')
        return 1
    publish(render(title, findings, analysed))
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
