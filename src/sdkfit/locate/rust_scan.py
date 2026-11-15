"""Read-only tree-sitter scan for Rust names rooted in an SDK crate.

The scan reports evidence only: every hit carries ``rooted``. Whether a hit is
certain is decided elsewhere.
"""

import posixpath
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import tree_sitter_rust
from tree_sitter import Language, Node, Parser, Tree

from .result import SiteShape
from .scan import Hit, ScanResult, _Source, _column

_SKIP_DIRECTORIES = frozenset({"target", "vendor", ".git"})


@dataclass(frozen=True, slots=True)
class _Module:
    rel: str
    tree: Tree
    source: _Source


@cache
def _parser() -> Parser:
    return Parser(Language(tree_sitter_rust.language()))


def _files(root: Path) -> list[Path]:
    found = []
    for path in root.rglob("*.rs"):
        if not path.is_file():
            continue
        directories = path.relative_to(root).parts[:-1]
        if any(
            directory in _SKIP_DIRECTORIES or directory.startswith(".")
            for directory in directories
        ):
            continue
        found.append(path)
    return sorted(found)


def _read(root: Path) -> list[_Module]:
    modules = []
    for path in _files(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
            tree = _parser().parse(text.encode("utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        if tree.root_node.has_error:
            continue
        modules.append(_Module(rel, tree, _Source(rel, tuple(text.split("\n")))))
    return modules


def _walk(node: Node) -> Iterator[Node]:
    yield node
    for child in node.children:
        yield from _walk(child)


def _text(node: Node) -> str:
    return node.text.decode("utf-8") if node.text is not None else ""


def _path_segments(node: Node) -> tuple[str, ...]:
    if node.type in {"identifier", "type_identifier"}:
        return (_text(node),)
    if node.type in {"scoped_identifier", "scoped_type_identifier"}:
        return _path_segments(node.named_children[0]) + (_text(node.named_children[-1]),)
    return ()


def _use_path(node: Node | None, prefix: tuple[str, ...]) -> tuple[str, ...] | None:
    if node is None:
        return prefix or None
    if node.type == "self":
        return prefix or None
    if node.type == "identifier":
        return prefix + (_text(node),) if prefix else (_text(node),)
    if node.type in {"scoped_identifier", "scoped_type_identifier"}:
        return _path_segments(node)
    return None


def _use_tree(
    node: Node,
    prefix: tuple[str, ...],
    crate: str,
    roots: dict[str, tuple[str, ...]],
) -> bool:
    """Bind one use tree; return whether it mentions the crate."""
    if node.type == "identifier":
        name = _text(node)
        if prefix:
            if prefix[0] != crate:
                return False
            roots[name] = prefix[1:] + (name,)
            return True
        if name == crate:
            roots[name] = ()
            return True
        return False
    if node.type == "self":
        if not prefix or prefix[0] != crate:
            return False
        roots[prefix[-1]] = prefix[1:]
        return True
    if node.type in {"scoped_identifier", "scoped_type_identifier"}:
        path = _path_segments(node)
        if not path or path[0] != crate:
            return False
        roots[path[-1]] = path[1:]
        return True
    if node.type == "use_as_clause":
        path = _use_path(node.child_by_field_name("path"), prefix)
        alias = node.child_by_field_name("alias")
        if path is None or path[0] != crate or alias is None:
            return False
        roots[_text(alias)] = path[1:]
        return True
    if node.type == "scoped_use_list":
        path = _use_path(node.child_by_field_name("path"), prefix)
        use_list = next(
            (child for child in node.named_children if child.type == "use_list"), None
        )
        if path is None or use_list is None:
            return False
        rooted = path[0] == crate
        for item in use_list.named_children:
            rooted = _use_tree(item, path, crate, roots) or rooted
        return rooted
    if node.type == "use_wildcard":
        path_node = node.named_children[0] if node.named_children else None
        path = _use_path(path_node, prefix)
        return bool(path and path[0] == crate)
    return False


def _bindings(
    tree: Tree, crate: str
) -> tuple[dict[str, tuple[str, ...]], bool]:
    """Names rooted in the crate, and whether any use roots the crate."""
    roots: dict[str, tuple[str, ...]] = {}
    crate_used = False
    for node in _walk(tree.root_node):
        if node.type != "use_declaration":
            continue
        for child in node.named_children:
            crate_used = _use_tree(child, (), crate, roots) or crate_used
    return roots, crate_used


def _callee_ref(
    node: Node | None, roots: dict[str, tuple[str, ...]], crate: str
) -> tuple[tuple[str, ...], bool] | None:
    """The canonical chain and rootedness of a call's callee."""
    if node is None:
        return None
    if node.type == "identifier":
        name = _text(node)
        if name in roots:
            return roots[name], True
        if name == crate:
            return (), True
        return None
    if node.type == "scoped_identifier":
        path = _path_segments(node)
        if not path:
            return None
        if path[0] == crate:
            return path[1:], True
        if path[0] in roots:
            return roots[path[0]] + path[1:], True
        return path, False
    return None


def _unwrap(node: Node | None) -> Node | None:
    while node is not None and node.type in {
        "reference_expression",
        "parenthesized_expression",
    }:
        node = node.named_children[0] if node.named_children else None
    return node


def _type_ref(
    node: Node | None, roots: dict[str, tuple[str, ...]], crate: str
) -> tuple[tuple[str, ...], bool] | None:
    """The canonical chain and rootedness of a type expression."""
    if node is None:
        return None
    if node.type in {"type_identifier", "identifier"}:
        name = _text(node)
        if name in roots:
            return roots[name], True
        if name == crate:
            return (), True
        return None
    if node.type in {"scoped_type_identifier", "scoped_identifier"}:
        path = _path_segments(node)
        if not path:
            return None
        if path[0] == crate:
            return path[1:], True
        if path[0] in roots:
            return roots[path[0]] + path[1:], True
        return None
    if node.type in {"generic_type", "generic_type_with_turbofish"}:
        return _type_ref(node.child_by_field_name("type"), roots, crate)
    return None


def _parameter_chain(
    node: Node | None, roots: dict[str, tuple[str, ...]], crate: str
) -> tuple[str, ...] | None:
    """The canonical chain of a rooted parameter type, through a reference."""
    while node is not None and node.type == "reference_type":
        node = node.child_by_field_name("type")
    ref = _type_ref(node, roots, crate)
    return ref[0] if ref is not None and ref[1] else None


def _returns(
    tree: Tree, roots: dict[str, tuple[str, ...]], crate: str
) -> dict[str, tuple[str, ...]]:
    """Same-file function name -> SDK return chain from its annotation.

    A missing, ``impl`` or non-SDK return type is no evidence; a name defined
    more than once in the module is ambiguous and dropped.
    """
    definitions: dict[str, list[tuple[str, ...] | None]] = {}
    for node in _walk(tree.root_node):
        if node.type != "function_item":
            continue
        name = node.child_by_field_name("name")
        if name is None:
            continue
        ref = _type_ref(node.child_by_field_name("return_type"), roots, crate)
        definitions.setdefault(_text(name), []).append(
            ref[0] if ref is not None and ref[1] else None
        )
    return {
        name: chains[0]
        for name, chains in definitions.items()
        if len(chains) == 1 and chains[0] is not None
    }


def _src_dir(rel: str) -> str:
    """The crate's ``src/`` directory for a module, else its own directory."""
    parts = rel.split("/")[:-1]
    if "src" in parts:
        return "/".join(parts[: parts.index("src") + 1])
    return posixpath.dirname(rel)


def _path_file(
    directory: str, segments: tuple[str, ...], files: frozenset[str]
) -> str | None:
    """The `.rs` or `mod.rs` file a module path names, if it exists."""
    if not segments:
        return None
    base = "/".join(segment for segment in (directory, *segments) if segment)
    return next(
        (
            candidate
            for candidate in (f"{base}.rs", f"{base}/mod.rs")
            if candidate in files
        ),
        None,
    )


def _declarations(module: _Module, files: frozenset[str]) -> dict[str, str]:
    """`mod name;` -> the file it declares, sibling or crate-rooted.

    Spec AC1: a sibling module is resolved relative to the file's directory or
    the crate `src/`; an inline `mod name { .. }` body is no other file.
    """
    directory = posixpath.dirname(module.rel)
    src = _src_dir(module.rel)
    declared: dict[str, str] = {}
    for node in module.tree.root_node.named_children:
        if node.type != "mod_item" or node.child_by_field_name("body") is not None:
            continue
        name = node.child_by_field_name("name")
        if name is None:
            continue
        declared_name = _text(name)
        target = _path_file(directory, (declared_name,), files) or _path_file(
            src, (declared_name,), files
        )
        if target is not None:
            declared[declared_name] = target
    return declared


def _imports(
    module: _Module,
    src: str,
    declared: Mapping[str, str],
    index: Mapping[str, Mapping[str, tuple[str, ...]]],
    files: frozenset[str],
) -> dict[str, tuple[str, ...]]:
    """Bare names a file imports from another module, with their return chain."""
    found: dict[str, tuple[str, ...]] = {}
    # shortcut: single-name `use` paths only; groups and aliases stay
    # unindexed until a fixture needs them.
    for node in module.tree.root_node.named_children:
        if node.type != "use_declaration":
            continue
        for child in node.named_children:
            if child.type != "scoped_identifier":
                continue
            segments = tuple(_text(child).split("::"))
            if segments[0] == "crate":
                target = _path_file(src, segments[1:-1], files)
            elif len(segments) == 2:
                target = declared.get(segments[0])
            else:
                target = None
            if target is None:
                continue
            chain = index.get(target, {}).get(segments[-1])
            if chain is not None:
                found[segments[-1]] = chain
    return found


@dataclass(frozen=True, slots=True)
class _Modules:
    """The crate's module files and the signatures one file can reach."""

    src: str
    files: frozenset[str]
    declared: Mapping[str, str]
    index: Mapping[str, Mapping[str, tuple[str, ...]]]
    imported: Mapping[str, tuple[str, ...]]


def _local_modules(
    module: _Module,
    index: Mapping[str, Mapping[str, tuple[str, ...]]],
    files: frozenset[str],
) -> _Modules:
    """Spec AC1: resolve the module declarations and imports of one file."""
    src = _src_dir(module.rel)
    declared = _declarations(module, files)
    return _Modules(
        src,
        files,
        declared,
        index,
        _imports(module, src, declared, index, files),
    )


def _fields(struct_expression: Node) -> tuple[Node, ...]:
    body = struct_expression.child_by_field_name("body")
    if body is None:
        return ()
    found = []
    for child in body.named_children:
        if child.type == "field_initializer":
            field = child.child_by_field_name("field")
            if field is not None:
                found.append(field)
        elif child.type == "shorthand_field_initializer" and child.named_children:
            found.append(child.named_children[0])
    return tuple(found)


@dataclass(frozen=True, slots=True)
class _Binding:
    """A name bound to a rooted type, its literal fields and how it was bound."""

    chain: tuple[str, ...]
    fields: tuple[Node, ...] = ()
    literal: bool = False


class _Visitor:
    """Emit rooted calls, struct fields and field accesses."""

    def __init__(
        self,
        source: _Source,
        crate: str,
        roots: dict[str, tuple[str, ...]],
        receivers: Mapping[str, str],
        returns: dict[str, tuple[str, ...]],
        modules: _Modules,
    ) -> None:
        self._source = source
        self._crate = crate
        self._roots = roots
        self._receivers = {
            key.replace("::", "."): value for key, value in receivers.items()
        }
        self._returns = returns
        self._modules = modules
        self._bindings: dict[str, _Binding] = {}
        self.rooted = False
        self.hits: list[Hit] = []

    def _emit(
        self,
        node: Node,
        shape: SiteShape,
        symbol: str,
        chain: tuple[str, ...],
        rooted: bool,
    ) -> None:
        if rooted:
            self.rooted = True
        line = self._source.lines[node.start_point.row]
        self.hits.append(
            Hit(
                self._source.path,
                node.start_point.row + 1,
                _column(line, node.start_point.column),
                shape,
                symbol,
                chain,
                rooted,
                line,
            )
        )

    def _visit_children(self, node: Node) -> None:
        for child in node.children:
            self.visit(child)

    def _bind(
        self, name: str, value: Node | None, annotation: Node | None = None
    ) -> None:
        binding = self._evidence(value, annotation)
        if binding is None:
            self._bindings.pop(name, None)
        else:
            self._bindings[name] = binding

    def _evidence(
        self, value: Node | None, annotation: Node | None
    ) -> _Binding | None:
        """The rooted type a let binds, from its annotation, literal or factory."""
        if annotation is not None:
            ref = _type_ref(annotation, self._roots, self._crate)
            if ref is None or not ref[1]:
                return None
            return _Binding(ref[0])
        literal = _unwrap(value)
        if literal is None:
            return None
        if literal.type == "struct_expression":
            ref = _type_ref(
                literal.child_by_field_name("name"), self._roots, self._crate
            )
            if ref is None or not ref[1]:
                return None
            return _Binding(ref[0], _fields(literal), True)
        if literal.type == "call_expression":
            return self._call_evidence(literal)
        return None

    def _call_evidence(self, call: Node) -> _Binding | None:
        function = call.child_by_field_name("function")
        ref = _callee_ref(function, self._roots, self._crate)
        if (
            ref is not None
            and ref[1]
            and len(ref[0]) > 1
            and ref[0][-1] in {"new", "default"}
        ):
            return _Binding(ref[0][:-1])
        candidates = []
        if ref is not None:
            candidates.append(".".join(ref[0]))
        if function is not None:
            candidates.append(".".join(_text(function).split("::")))
        for candidate in candidates:
            mapped = self._receivers.get(candidate)
            if mapped is None:
                continue
            chain = tuple(
                part for part in mapped.replace("::", ".").split(".") if part
            )
            if chain:
                return _Binding(chain)
        if function is not None and function.type == "identifier":
            annotated = self._returns.get(_text(function))
            if annotated is None:
                annotated = self._modules.imported.get(_text(function))
            if annotated is not None:
                return _Binding(annotated)
        return self._local_evidence(function)

    def _local_evidence(self, function: Node | None) -> _Binding | None:
        """The receiver chain of a call into another module of the crate."""
        if function is None or function.type != "scoped_identifier":
            return None
        segments = tuple(_text(function).split("::"))
        if segments[0] == "crate":
            target = _path_file(self._modules.src, segments[1:-1], self._modules.files)
        elif len(segments) == 2:
            target = self._modules.declared.get(segments[0])
        else:
            # shortcut: one bare module segment only, until a fixture needs it.
            return None
        if target is None:
            return None
        chain = self._modules.index.get(target, {}).get(segments[-1])
        return _Binding(chain) if chain is not None else None

    def _parameters(self, node: Node) -> None:
        """Seed the body from the annotated parameters of a function."""
        parameters = node.child_by_field_name("parameters")
        if parameters is None:
            return
        for parameter in parameters.named_children:
            if parameter.type != "parameter":
                continue
            pattern = parameter.child_by_field_name("pattern")
            if pattern is None or pattern.type != "identifier":
                continue
            chain = _parameter_chain(
                parameter.child_by_field_name("type"), self._roots, self._crate
            )
            if chain is not None:
                self._bindings[_text(pattern)] = _Binding(chain)

    def _let(self, node: Node) -> None:
        pattern = node.child_by_field_name("pattern")
        if pattern is not None and pattern.type == "identifier":
            self._bind(
                _text(pattern),
                node.child_by_field_name("value"),
                node.child_by_field_name("type"),
            )
        self._visit_children(node)

    def _assign(self, node: Node) -> None:
        left = node.child_by_field_name("left")
        if left is not None and left.type == "identifier":
            self._bind(_text(left), node.child_by_field_name("right"))
        self._visit_children(node)

    def _struct(self, node: Node) -> None:
        ref = _type_ref(node.child_by_field_name("name"), self._roots, self._crate)
        if ref is not None:
            chain, rooted = ref
            if rooted:
                self.rooted = True
                for field in _fields(node):
                    self._emit(field, SiteShape.KEYWORD, _text(field), chain, True)
        self._visit_children(node)

    def _receiver(self, node: Node | None) -> tuple[str, ...] | None:
        """The type chain a bound receiver expression stands for."""
        node = _unwrap(node)
        if node is None:
            return None
        if node.type == "identifier":
            binding = self._bindings.get(_text(node))
            return binding.chain if binding is not None else None
        if node.type == "field_expression":
            value = node.child_by_field_name("value")
            field = node.child_by_field_name("field")
        elif node.type == "call_expression":
            function = node.child_by_field_name("function")
            if function is None or function.type != "field_expression":
                return None
            value = function.child_by_field_name("value")
            field = function.child_by_field_name("field")
        else:
            return None
        chain = self._receiver(value)
        if chain is None or field is None:
            return None
        return chain + (_text(field),)

    def _field(self, node: Node) -> None:
        value = _unwrap(node.child_by_field_name("value"))
        field = node.child_by_field_name("field")
        if value is not None and field is not None:
            binding = (
                self._bindings.get(_text(value))
                if value.type == "identifier"
                else None
            )
            if binding is not None and binding.literal:
                self._emit(field, SiteShape.ATTRIBUTE, _text(field), binding.chain, True)
            else:
                chain = self._receiver(value)
                if chain is not None:
                    self._emit(
                        field,
                        SiteShape.ATTRIBUTE,
                        _text(field),
                        chain + (_text(field),),
                        True,
                    )
        self._visit_children(node)

    def _argument(self, argument: Node, call_chain: tuple[str, ...]) -> None:
        node = _unwrap(argument)
        if node is None:
            return
        if node.type == "struct_expression":
            ref = _type_ref(node.child_by_field_name("name"), self._roots, self._crate)
            if ref is not None and ref[1]:
                for field in _fields(node):
                    self._emit(field, SiteShape.KEYWORD, _text(field), call_chain, True)
        elif node.type == "identifier":
            binding = self._bindings.get(_text(node))
            if binding is not None:
                for field in binding.fields:
                    self._emit(field, SiteShape.KEYWORD, _text(field), call_chain, True)
        elif node.type == "field_expression":
            value = _unwrap(node.child_by_field_name("value"))
            field = node.child_by_field_name("field")
            if (
                value is not None
                and value.type == "identifier"
                and field is not None
                and _text(value) in self._bindings
            ):
                self._emit(field, SiteShape.ATTRIBUTE, _text(field), call_chain, True)

    def _call(self, node: Node) -> None:
        function = node.child_by_field_name("function")
        call_chain: tuple[str, ...] | None = None
        if function is not None and function.type == "field_expression":
            method = function.child_by_field_name("field")
            receiver = self._receiver(function.child_by_field_name("value"))
            if receiver is not None and method is not None:
                call_chain = receiver + (_text(method),)
                self._emit(function, SiteShape.CALL, _text(method), call_chain, True)
                value = function.child_by_field_name("value")
                if value is not None:
                    self.visit(value)
        else:
            ref = _callee_ref(function, self._roots, self._crate)
            if ref is not None:
                chain, rooted = ref
                if rooted:
                    self.rooted = True
                    call_chain = chain
                    if chain:
                        self._emit(function, SiteShape.CALL, chain[-1], chain, True)
                elif function is not None and function.type == "scoped_identifier":
                    self._emit(function, SiteShape.CALL, chain[-1], chain, False)
        arguments = node.child_by_field_name("arguments")
        if arguments is not None:
            if call_chain is not None:
                for argument in arguments.named_children:
                    self._argument(argument, call_chain)
            for argument in arguments.named_children:
                self.visit(argument)
        if function is not None and function.type != "field_expression":
            self.visit(function)

    def visit(self, node: Node) -> None:
        if node.type == "function_item":
            saved = self._bindings
            self._bindings = {}
            # Spec AC1: an annotated parameter is the body's initial receiver.
            self._parameters(node)
            self._visit_children(node)
            self._bindings = saved
        elif node.type == "call_expression":
            self._call(node)
        elif node.type == "let_declaration":
            self._let(node)
        elif node.type == "assignment_expression":
            self._assign(node)
        elif node.type == "struct_expression":
            self._struct(node)
        elif node.type == "field_expression":
            self._field(node)
        else:
            self._visit_children(node)


def scan_rust(
    root: str | Path, sdk_package: str, receivers: Mapping[str, str] | None = None
) -> ScanResult:
    """Parse ``root`` read-only and report SDK-rooted Rust evidence."""
    parsed = []
    for module in _read(Path(root)):
        roots, crate_used = _bindings(module.tree, sdk_package)
        parsed.append((module, roots, crate_used))
    files = frozenset(module.rel for module, _, _ in parsed)
    # Spec AC1/S1: index each module's resolved signatures before the pass.
    index = {
        module.rel: _returns(module.tree, roots, sdk_package)
        for module, roots, _ in parsed
    }
    modules: list[str] = []
    hits: list[Hit] = []
    for module, roots, crate_used in parsed:
        visitor = _Visitor(
            module.source,
            sdk_package,
            roots,
            receivers or {},
            index[module.rel],
            _local_modules(module, index, files),
        )
        visitor.visit(module.tree.root_node)
        if crate_used or visitor.rooted:
            modules.append(module.rel)
            hits.extend(visitor.hits)
    return ScanResult(modules=tuple(modules), hits=tuple(hits))
