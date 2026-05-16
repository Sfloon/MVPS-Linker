from pathlib import Path
import os, ast

source_dirs = ["codebase", "scripts", "code"]
output_file = Path("src/main.py")


def parse_file(path: Path) -> ast.Module:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"MVPS Error: '{path.name}' is not valid UTF-8.")
        raise SystemExit(1)
    except OSError as e:
        print(f"MVPS Error: Could not read '{path.name}': {e}")
        raise SystemExit(1)
    try:
        return ast.parse(source)
    except SyntaxError as e:
        print(f"MVPS Error: Syntax error in '{path.name}' line {e.lineno}: {e.msg}")
        raise SystemExit(1)


class SymbolCollector(ast.NodeVisitor):
    def __init__(self):
        self.symbols = set()

    def visit_FunctionDef(self, node):
        self.symbols.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.symbols.add(node.name)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.symbols.add(target.id)
        self.generic_visit(node)


class DangerousAssignmentChecker(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id[:1].isupper():
                print(
                    f"MVPS Warning: '{target.id}' assigned on line {node.lineno} in "
                    f"'{self.filename}'. This may shadow a class or library symbol."
                )
        self.generic_visit(node)


class DependencyCollector(ast.NodeVisitor):
    def __init__(self, module_names):
        self.module_names = module_names
        self.referenced = set()

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in self.module_names:
                self.referenced.add(alias.name)

    def visit_ImportFrom(self, node):
        if node.module in self.module_names:
            self.referenced.add(node.module)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            self.referenced.add(node.value.id)
        self.generic_visit(node)


class AliasCollector(ast.NodeVisitor):
    def __init__(self, module_names):
        self.module_names = module_names
        self.alias_map = {}

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in self.module_names and alias.asname:
                self.alias_map[alias.asname] = alias.name

    def visit_ImportFrom(self, node):
        if node.module in self.module_names:
            for alias in node.names:
                local = alias.asname or alias.name
                self.alias_map[local] = f"{node.module}_{alias.name}"


class Flattener(ast.NodeTransformer):
    def __init__(self, module, rename_map, alias_map, module_names):
        self.module = module
        self.rename_map = rename_map
        self.alias_map = alias_map
        self.module_names = module_names
        self.external_imports = set()

    def visit_Import(self, node):
        kept = [a for a in node.names if a.name not in self.module_names]
        if kept:
            self.external_imports.add(ast.unparse(ast.Import(names=kept)))
        return None

    def visit_ImportFrom(self, node):
        if node.module not in self.module_names:
            self.external_imports.add(ast.unparse(node))
        return None

    def _rename_def(self, node):
        if node.name in self.rename_map:
            node.name = self.rename_map[node.name]
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        return self._rename_def(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        return self._rename_def(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in self.rename_map:
                target.id = self.rename_map[target.id]
        self.generic_visit(node)
        return node

    def visit_Global(self, node):
        node.names = [
            self.rename_map.get(n, self.alias_map.get(n, n))
            for n in node.names
        ]
        return node

    def visit_Name(self, node):
        node.id = self.alias_map.get(node.id, self.rename_map.get(node.id, node.id))
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        if not isinstance(node.value, ast.Name):
            return node
        mod = self.alias_map.get(node.value.id, node.value.id)
        if mod in self.module_names:
            return ast.Name(id=f"{mod}_{node.attr}", ctx=node.ctx)
        return node


def topo_sort(dependencies: dict) -> list:
    visited, visiting, order = set(), set(), []

    def visit(mod):
        if mod in visiting:
            print(f"MVPS Error: Circular dependency detected involving '{mod}'.")
            raise SystemExit(1)
        if mod in visited:
            return
        visiting.add(mod)
        for dep in dependencies.get(mod, []):
            visit(dep)
        visiting.discard(mod)
        visited.add(mod)
        order.append(mod)

    for mod in dependencies:
        visit(mod)
    return order


def find_source_dir() -> Path:
    for name in source_dirs:
        path = Path(name)
        if path.exists():
            return path
    print(f"MVPS Error: Source directory not found. Create one of: {', '.join(source_dirs)} and place your scripts inside it.")
    raise SystemExit(1)


def collect_modules(source_dir: Path) -> tuple[dict, dict]:
    module_symbols, module_paths = {}, {}

    for root, _, files in os.walk(source_dir):
        for file in files:
            if not file.endswith(".py"):
                continue
            path = Path(root) / file
            module = path.stem
            if module in module_paths:
                print(f"MVPS Error: Duplicate module name '{module}'. Rename one of the files.")
                raise SystemExit(1)
            tree = parse_file(path)
            collector = SymbolCollector()
            collector.visit(tree)
            DangerousAssignmentChecker(path.name).visit(tree)
            module_symbols[module] = collector.symbols
            module_paths[module] = path

    if not module_paths:
        print(f"MVPS Error: No Python files found in '{source_dir}'.")
        raise SystemExit(1)

    return module_symbols, module_paths


source_dir = find_source_dir()
module_symbols, module_paths = collect_modules(source_dir)
module_names = set(module_symbols)

dependencies = {mod: set() for mod in module_names}
for mod, path in module_paths.items():
    tree = parse_file(path)
    collector = DependencyCollector(module_names)
    collector.visit(tree)
    dependencies[mod] = {r for r in collector.referenced if r in module_names and r != mod}

sorted_modules = topo_sort(dependencies)
output_blocks, external_imports = [], set()

for module in sorted_modules:
    path = module_paths[module]
    tree = parse_file(path)
    rename_map = {sym: f"{module}_{sym}" for sym in module_symbols[module]}
    alias_collector = AliasCollector(module_names)
    alias_collector.visit(tree)
    flattener = Flattener(module, rename_map, alias_collector.alias_map, module_names)
    tree = flattener.visit(tree)
    external_imports |= flattener.external_imports
    ast.fix_missing_locations(tree)
    output_blocks.append(f"# {path.name}\n{ast.unparse(tree)}")

output_file.parent.mkdir(exist_ok=True)
for f in output_file.parent.glob("*.py"):
    f.unlink()

sections = [*sorted(external_imports), "", *output_blocks]
final_text = "\n".join(sections)
while "\n\n\n" in final_text:
    final_text = final_text.replace("\n\n\n", "\n\n")

output_file.write_text(final_text, encoding="utf-8")
print(f"MVPS: Successfully linked {len(sorted_modules)} modules into '{output_file}'")