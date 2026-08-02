import ast
import json
import re


CPP_SOURCE_EXTENSIONS = (".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx")


def _annotation_name(annotation):
    if annotation is None:
        return None
    try:
        return ast.unparse(annotation)
    except Exception:
        return type(annotation).__name__


def _call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


def _function_signature(node):
    args = []
    for arg in list(node.args.posonlyargs) + list(node.args.args):
        annotation = _annotation_name(arg.annotation)
        args.append(f"{arg.arg}: {annotation}" if annotation else arg.arg)
    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    for arg in node.args.kwonlyargs:
        annotation = _annotation_name(arg.annotation)
        args.append(f"{arg.arg}: {annotation}" if annotation else arg.arg)
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")

    returns = _annotation_name(node.returns)
    signature = f"{node.name}({', '.join(args)})"
    return f"{signature} -> {returns}" if returns else signature


def _class_info(node):
    methods = []
    attributes = []
    nested_classes = []

    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_function_signature(child))
        elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            annotation = _annotation_name(child.annotation)
            attributes.append(f"{child.target.id}: {annotation}" if annotation else child.target.id)
        elif isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    attributes.append(target.id)
        elif isinstance(child, ast.ClassDef):
            nested_classes.append(child.name)

    return {
        "class_name": node.name,
        "decorators": [_call_name(dec) for dec in node.decorator_list],
        "bases": [_call_name(base) for base in node.bases],
        "attributes": attributes,
        "methods": methods,
        "nested_classes": nested_classes,
    }


def extract_python_info(content):
    """Return a compact JSON summary of a Python source file for module mapping."""
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return json.dumps(
            {
                "language": "python",
                "error": f"syntax error: {exc}",
                "raw_excerpt": content[:3000],
            },
            ensure_ascii=False,
        )

    imports = []
    constants = []
    functions = []
    async_functions = []
    classes = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.extend(f"{module}.{alias.name}".strip(".") for alias in node.names)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.isupper():
                annotation = _annotation_name(node.annotation)
                constants.append(f"{node.target.id}: {annotation}" if annotation else node.target.id)
        elif isinstance(node, ast.FunctionDef):
            functions.append(_function_signature(node))
        elif isinstance(node, ast.AsyncFunctionDef):
            async_functions.append(_function_signature(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(_class_info(node))

    summary = {
        "language": "python",
        "module_docstring": ast.get_docstring(tree),
        "imports": imports,
        "constants": constants,
        "functions": functions,
        "async_functions": async_functions,
        "classes": classes,
    }
    return json.dumps(summary, ensure_ascii=False)


def _strip_cpp_comments(content):
    content = re.sub(r"/\*.*?\*/", " ", content, flags=re.DOTALL)
    content = re.sub(r"//.*", " ", content)
    return content


def extract_cpp_info(content):
    """Return a compact JSON summary of a C/C++ source or header file."""
    code = _strip_cpp_comments(content)
    includes = re.findall(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]", code, flags=re.MULTILINE)
    macros = re.findall(r"^\s*#\s*define\s+([A-Za-z_]\w*)", code, flags=re.MULTILINE)
    namespaces = re.findall(r"\bnamespace\s+([A-Za-z_]\w*)", code)
    types = [
        {"kind": kind, "name": name}
        for kind, name in re.findall(r"\b(class|struct|enum)\s+([A-Za-z_]\w*)", code)
    ]

    function_pattern = re.compile(
        r"(?:^|[;{}\n])\s*(?:template\s*<[^;{}]+>\s*)?"
        r"(?:(?:inline|static|virtual|explicit|constexpr|friend|extern)\s+)*"
        r"(?:[A-Za-z_][\w:<>,~*&\s]+?)\s+"
        r"([A-Za-z_~]\w*(?:::[A-Za-z_~]\w*)?)\s*\(([^;{}()]*)\)\s*(?:const\s*)?(?:override\s*)?(?:=|;|\{)",
        flags=re.MULTILINE,
    )
    skipped = {
        "if", "for", "while", "switch", "catch", "return", "sizeof", "delete", "new"
    }
    functions = []
    seen = set()
    for name, params in function_pattern.findall(code):
        short_name = name.split("::")[-1]
        if short_name in skipped or name in seen:
            continue
        seen.add(name)
        compact_params = " ".join(params.split())
        functions.append(f"{name}({compact_params})")
        if len(functions) >= 80:
            break

    summary = {
        "language": "c/c++",
        "includes": includes[:80],
        "macros": macros[:80],
        "namespaces": sorted(set(namespaces))[:40],
        "types": types[:80],
        "functions": functions,
        "raw_excerpt": code[:3000],
    }
    return json.dumps(summary, ensure_ascii=False)


def looks_like_cpp(content, file_path=None):
    if file_path and file_path.lower().endswith(CPP_SOURCE_EXTENSIONS):
        return True
    return bool(re.search(r"^\s*#\s*include\b|\bnamespace\b|::|\b(class|struct|enum)\s+\w+\s*[{:]", content, re.MULTILINE))


def extract_source_info(content, file_path=None):
    if looks_like_cpp(content, file_path):
        return extract_cpp_info(content)
    return extract_python_info(content)
