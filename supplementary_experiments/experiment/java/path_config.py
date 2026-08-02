import os
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_ROOT = EXPERIMENT_ROOT / "project"
DATASET_ROOT = Path(os.environ.get("EXPERIMENT_PROJECT_ROOT", DEFAULT_DATASET_ROOT)).resolve()


def has_source_files(path, suffix=".java"):
    path = Path(path)
    if not path.exists() or not path.is_dir():
        return False
    return any(path.rglob(f"*{suffix}"))


def resolve_source_root(project_dir, project_name=None, suffix=".java"):
    """Resolve the actual source root inside one dataset project directory."""
    project_dir = Path(project_dir).resolve()
    project_name = project_name or project_dir.name

    nested_same_name = project_dir / project_name
    if has_source_files(nested_same_name, suffix):
        return str(nested_same_name)

    if has_source_files(project_dir, suffix):
        return str(project_dir)

    for child in sorted(project_dir.iterdir() if project_dir.exists() else []):
        if child.is_dir() and has_source_files(child, suffix):
            return str(child)

    return str(project_dir)


def java_project_dir(project_name, dataset_root=None):
    dataset_root = Path(dataset_root or DATASET_ROOT)
    return str((dataset_root / "java" / project_name).resolve())


def first_existing_file(base_dir, candidates):
    base_dir = Path(base_dir)
    for candidate in candidates:
        path = base_dir / candidate
        if path.exists():
            return str(path.resolve())
    return None


def infer_module_info(project_dir, project_name):
    candidates = [
        f"updated_config_{project_name}.txt",
        f"{project_name}_accurateModules1.txt",
        f"{project_name}_early1.txt",
        "hadoop_early1.txt",
    ]
    found = first_existing_file(project_dir, candidates)
    if found:
        return found

    project_dir = Path(project_dir)
    patterns = ("*accurateModules*.txt", "updated_config*.txt", "*early*.txt")
    for pattern in patterns:
        matches = sorted(project_dir.glob(pattern))
        if matches:
            return str(matches[0].resolve())
    return None


def infer_gt_file(project_dir, project_name):
    candidates = [
        f"updated_{project_name}_gt.json",
        f"{project_name}_gt.json",
    ]
    found = first_existing_file(project_dir, candidates)
    if found:
        return found

    matches = sorted(Path(project_dir).glob("*gt*.json"))
    if matches:
        return str(matches[0].resolve())
    return None
