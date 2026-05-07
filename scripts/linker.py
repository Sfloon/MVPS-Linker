from pathlib import Path
import os
import ast

SOURCE_DIR = Path("codebase")
OUTPUT_FILE = Path("src/combined.py")

if not SOURCE_DIR.exists():
    print("MVPS Error: Source directory not found. Please make a folder named 'codebase' in which your scripts are placed.")

class SymbolCollector(ast.NodeVisitor):
    def __init__(self):
        self.symbols = set()

    def visit_FunctionDef(self, node):
        self.symbols.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        for t in node.targets:
            if isinstance(t, ast.Name):
                self.symbols.add(t.id)
        self.generic_visit(node)

class DependencyCollector(ast.NodeVisitor):
    def __init__(self, module_names):
        self.referenced = set()
        self.module_names = module_names

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            self.referenced.add(node.value.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name in self.module_names:
                self.referenced.add(alias.name)

    def visit_ImportFrom(self, node):
        if node.module in self.module_names:
            self.referenced.add(node.module)

class Flattener(ast.NodeTransformer):
    def __init__(self, module, rename_map, alias_map):
        self.module = module
        self.rename_map = rename_map
        self.alias_map = alias_map

    def visit_Import(self, node):
        return None

    def visit_ImportFrom(self, node):
        return None

    def visit_FunctionDef(self, node):
        if node.name in self.rename_map:
            node.name = self.rename_map[node.name]
        self.generic_visit(node)
        return node

    def visit_Assign(self, node):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in self.rename_map:
                t.id = self.rename_map[t.id]
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        if node.id in self.alias_map:
            node.id = self.alias_map[node.id]
        if node.id in self.rename_map:
            node.id = self.rename_map[node.id]
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        if isinstance(node.value, ast.Name):
            module_name = node.value.id
            if module_name in self.alias_map:
                module_name = self.alias_map[module_name]
            attr = node.attr
            key = f"{module_name}_{attr}"
            return ast.Name(id=key, ctx=node.ctx)
        return node

class AliasCollector(ast.NodeVisitor):
    def __init__(self, module_names):
        self.alias_map = {}
        self.module_names = module_names

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in self.module_names and alias.asname:
                self.alias_map[alias.asname] = alias.name

    def visit_ImportFrom(self, node):
        if node.module in self.module_names:
            for alias in node.names:
                original = alias.name
                local_name = alias.asname if alias.asname else alias.name
                source_module = node.module
                self.alias_map[local_name] = f"{source_module}_{original}"

module_symbols = {}
module_paths = {}

for root, dirs, files in os.walk(SOURCE_DIR):
    for file in files:
        if not file.endswith(".py"):
            continue
        path = Path(root) / file
        module = path.stem
        tree = ast.parse(path.read_text(encoding="utf-8"))
        collector = SymbolCollector()
        collector.visit(tree)
        module_symbols[module] = collector.symbols
        module_paths[module] = path

module_names = set(module_symbols.keys())
dependencies = {module: set() for module in module_symbols}

for module, path in module_paths.items():
    tree = ast.parse(path.read_text(encoding="utf-8"))
    dependency_collector = DependencyCollector(module_names)
    dependency_collector.visit(tree)
    for ref in dependency_collector.referenced:
        if ref in module_symbols and ref != module:
            dependencies[module].add(ref)

def topo_sort(deps):
    visited = set()
    in_progress = set()
    order = []

    def visit(mod):
        if mod in in_progress:
            raise ValueError(f"MVPS Error: Circular dependency detected involving the following script: {mod}. Make sure modules aren't importing eachother.")
        if mod in visited:
            return
        in_progress.add(mod)
        for dep in deps.get(mod, []):
            visit(dep)
        in_progress.remove(mod)
        visited.add(mod)
        order.append(mod)

    for mod in deps:
        visit(mod)
    return order

try:
    sorted_modules = topo_sort(dependencies)
except ValueError as e:
    print(str(e))
    exit(1)

output_blocks = []

total = len(sorted_modules)

for i, module in enumerate(sorted_modules, 1):
    print(f"MVPS: [{i}/{total}] linking {module}")
    
    path = module_paths[module]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    
    rename_map = {
        name: f"{module}_{name}"
        for name in module_symbols[module]
    }

    alias_collector = AliasCollector(module_names)
    alias_collector.visit(tree)
    alias_map = alias_collector.alias_map

    tree = Flattener(module, rename_map, alias_map).visit(tree)
    ast.fix_missing_locations(tree)

    output_blocks.append(ast.unparse(tree))

src_dir = Path("src")
src_dir.mkdir(exist_ok=True)
for f in src_dir.glob("*.py"):
    f.unlink()

OUTPUT_FILE.write_text("\n\n".join(output_blocks), encoding="utf-8")