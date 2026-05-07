from pathlib import Path
import os
import ast

SOURCE_DIR = Path("codebase")
OUTPUT_FILE = Path("src/combined.py")

if not SOURCE_DIR.exists():
    print("MVPS Error: Source directory not found. Please make a folder named 'codebase' and place your scripts inside it.")
    exit(1)

external_imports = set()

class DangerousAssignmentChecker(ast.NodeVisitor):
    def __init__(self):
        self.dangerous = []

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id

                if name and name[0].isupper():
                    self.dangerous.append(
                        (name, node.lineno)
                    )

        self.generic_visit(node)

class SymbolCollector(ast.NodeVisitor):
    def __init__(self):
        self.symbols = set()

    def visit_FunctionDef(self, node):
        self.symbols.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.symbols.add(target.id)

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
                original = alias.name
                local = alias.asname if alias.asname else alias.name
                self.alias_map[local] = f"{node.module}_{original}"


class Flattener(ast.NodeTransformer):
    def __init__(self, module, rename_map, alias_map, module_names):
        self.module = module
        self.rename_map = rename_map
        self.alias_map = alias_map
        self.module_names = module_names

    def visit_Import(self, node):
        kept = []

        for alias in node.names:
            if alias.name not in self.module_names:
                kept.append(alias)

        if kept:
            line = ast.unparse(ast.Import(names=kept))
            external_imports.add(line)

        return None

    def visit_ImportFrom(self, node):
        if node.module not in self.module_names:
            external_imports.add(ast.unparse(node))

        return None

    def visit_FunctionDef(self, node):
        if node.name in self.rename_map:
            node.name = self.rename_map[node.name]

        self.generic_visit(node)
        return node

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id in self.rename_map:
                    target.id = self.rename_map[target.id]

        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        if node.id in self.alias_map:
            node.id = self.alias_map[node.id]

        elif node.id in self.rename_map:
            node.id = self.rename_map[node.id]

        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)

        if isinstance(node.value, ast.Name):
            module_name = node.value.id

            if module_name in self.alias_map:
                module_name = self.alias_map[module_name]

            if module_name in self.module_names:
                return ast.Name(
                    id=f"{module_name}_{node.attr}",
                    ctx=node.ctx
                )

        return node


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
        danger_checker = DangerousAssignmentChecker()
        danger_checker.visit(tree)

        for name, line in danger_checker.dangerous:
            print(
                f"MVPS Warning: '{name}' assigned on line {line} "
                f"in '{path.name}'. "
                f"This may overwrite a library class or function."
            )

        module_symbols[module] = collector.symbols
        module_paths[module] = path

module_names = set(module_symbols.keys())

dependencies = {
    module: set()
    for module in module_names
}

for module, path in module_paths.items():
    tree = ast.parse(path.read_text(encoding="utf-8"))

    collector = DependencyCollector(module_names)
    collector.visit(tree)

    for ref in collector.referenced:
        if ref in module_names and ref != module:
            dependencies[module].add(ref)


def topo_sort(dependencies):
    visited = set()
    visiting = set()
    order = []

    def visit(module):
        if module in visiting:
            raise ValueError(
                f"MVPS Error: Circular dependency detected involving '{module}'."
            )

        if module in visited:
            return

        visiting.add(module)

        for dep in dependencies.get(module, []):
            visit(dep)

        visiting.remove(module)
        visited.add(module)

        order.append(module)

    for module in dependencies:
        visit(module)

    return order


try:
    sorted_modules = topo_sort(dependencies)

except ValueError as error:
    print(str(error))
    exit(1)

output_blocks = []

total = len(sorted_modules)

for index, module in enumerate(sorted_modules, 1):
    print(f"MVPS: [{index}/{total}] linking {module}")

    path = module_paths[module]

    tree = ast.parse(path.read_text(encoding="utf-8"))

    rename_map = {
        symbol: f"{module}_{symbol}"
        for symbol in module_symbols[module]
    }

    alias_collector = AliasCollector(module_names)
    alias_collector.visit(tree)

    alias_map = alias_collector.alias_map

    tree = Flattener(
        module,
        rename_map,
        alias_map,
        module_names
    ).visit(tree)

    ast.fix_missing_locations(tree)

    module_code = ast.unparse(tree)

    output_blocks.append(
        f"# {path.name}\n{module_code}"
    )

src_dir = OUTPUT_FILE.parent
src_dir.mkdir(exist_ok=True)

for file in src_dir.glob("*.py"):
    file.unlink()

final_code = []

if external_imports:
    final_code.extend(sorted(external_imports))
    final_code.append("")

final_code.extend(output_blocks)
final_text = "\n".join(final_code)

while "\n\n\n" in final_text:
    final_text = final_text.replace("\n\n\n", "\n\n")

OUTPUT_FILE.write_text(
    final_text,
    encoding="utf-8"
)

print(f"MVPS: Successfully linked {total} modules into '{OUTPUT_FILE}'")