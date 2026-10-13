"""Hash-pinned, offline single-case adaptation; never import or run Polygon."""
import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path

PINS = {
    'polygon/environment.py': '9f8ddd7a61368cc8b14155ad0aa6f94b3a699e494143b16004cca64e3ac0742a',
    'polygon/smt/formula.py': 'ecdc290227e8c717fa20065313331b605fd54566a844ec9ce88c6d99190207cc',
    'polygon/smt/provers/smtlibv2.py': 'b0b6afd7bca13a964c639120699b68eb101be13fd18d768e9f36eec2e3b97bdc',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def adapt_environment(text):
    tree = ast.parse(text)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Environment')
    check = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'check')
    wrapper = check.body[-1]
    assert isinstance(wrapper, ast.With)
    # Keep the original result projection and clear() in precisely the same order.
    lines = text.splitlines(keepends=True)
    result_start = next(n.lineno for n in wrapper.body if isinstance(n, ast.If)
                        and ast.unparse(n.test) == "ret['status'] == 'ERR'")
    projection = ''.join(line[4:] if line.strip() else line
                         for line in lines[result_start - 1:wrapper.end_lineno])
    direct = ('        ret = {}\n'
              '        start = datetime.datetime.now()\n'
              '        task(ret)\n\n' + projection)
    lines[wrapper.lineno - 1:wrapper.end_lineno] = [direct]
    # An isolated single-use Environment is required because task now mutates self.
    signature = ('    def check(self, q1, q2, use_precise_encoding=False, *,\n'
                 '              solver_timeout_seconds):\n'
                 '        if type(solver_timeout_seconds) is not int or solver_timeout_seconds <= 0:\n'
                 '            raise ValueError("solver_timeout_seconds must be a positive integer")\n'
                 '        if getattr(self, "_serial_case_used", False):\n'
                 '            raise RuntimeError("serial adapter requires a fresh Environment per case")\n'
                 '        self._serial_case_used = True\n'
                 '        self.formulas.timeout = solver_timeout_seconds\n')
    lines[check.lineno - 1] = signature
    return ''.join(lines)


def adapt_formula(text):
    old = "executable_options=['--in', f'-T:300'],"
    assert text.count(old) == 1
    return text.replace(old, "executable_options=['--in', f'-T:{self.timeout}'],")


def build(source, destination):
    source, destination = Path(source), Path(destination)
    originals = {}
    for rel, expected in PINS.items():
        path = source / (rel + '.txt')
        if not path.exists():
            path = source / rel
        data = path.read_bytes()
        if digest(data) != expected:
            raise ValueError(f'upstream hash mismatch: {rel}')
        originals[rel] = data
    # Validate all input bytes and transformed syntax before creating any output.
    transformed = {}
    for rel, data in originals.items():
        original = data.decode()
        if rel.endswith('environment.py'):
            adapted = adapt_environment(original)
        elif rel.endswith('formula.py'):
            adapted = adapt_formula(original)
        else:
            adapted = original
        ast.parse(adapted)
        transformed[rel] = adapted
    destination.mkdir(parents=True, exist_ok=False)
    diffs, manifest = [], []
    for rel, data in originals.items():
        original, adapted = data.decode(), transformed[rel]
        path = destination / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(adapted)
        diffs.extend(difflib.unified_diff(original.splitlines(keepends=True),
                                        adapted.splitlines(keepends=True),
                                        fromfile='a/' + rel, tofile='b/' + rel, n=0))
        manifest.append({'path': rel, 'original_sha256': digest(data),
                         'adapted_sha256': digest(adapted.encode())})
    (destination / 'serial.patch').write_text(''.join(diffs))
    (destination / 'BUILD.json').write_text(json.dumps({
        'files': manifest, 'complete_checkout': False, 'imports_of_polygon': 0,
        'solver_runs': 0, 'scope': 'single-use Environment.check only; disambiguate unchanged',
    }, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.destination), indent=2))
