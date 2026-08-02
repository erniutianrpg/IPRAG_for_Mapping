import argparse
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_MAPPING_PATH = SCRIPT_DIR / "removed_none_file_mapping.json"
DEFAULT_SOURCE_ROOT = REPO_ROOT / "experiment" / "project"
DEFAULT_OUTPUT_ROOT = SCRIPT_DIR / "module_summaries"

TARGET_MODULES = [
    ("bigbluebutton", "Apps"),
    ("hadoop", "YARN"),
    ("jabref", "cli"),
    ("mediastore", "Packaging"),
    ("teammates", "Client"),
    ("teastore", "Recommender"),
]

TEXT_EXTENSIONS = {
    ".java",
    ".scala",
    ".kt",
    ".kts",
    ".xml",
    ".properties",
    ".gradle",
    ".md",
    ".txt",
}


class ChatClient:
    def __init__(self):
        self.api_key = os.environ.get("LLM_API_KEY", "").strip()
        self.base_url = os.environ.get("LLM_BASE_URL", "").rstrip("/")
        self.model = os.environ.get("LLM_CHAT_MODEL", "").strip()
        self.max_retries = int(os.environ.get("LLM_API_MAX_RETRIES", "3"))
        self.retry_delay = float(os.environ.get("LLM_API_RETRY_DELAY_SECONDS", "2"))
        self.ssl_verify = os.environ.get("LLM_SSL_VERIFY", "true").lower() != "false"
        self.trust_env = os.environ.get("LLM_TRUST_ENV", "true").lower() != "false"
        handlers = []
        if not self.trust_env:
            handlers.append(urllib.request.ProxyHandler({}))
        if not self.ssl_verify:
            handlers.append(
                urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
            )
        self.opener = urllib.request.build_opener(*handlers)

        missing = [
            name
            for name, value in [
                ("LLM_API_KEY", self.api_key),
                ("LLM_BASE_URL", self.base_url),
                ("LLM_CHAT_MODEL", self.model),
            ]
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing environment variables: "
                + ", ".join(missing)
                + ". Load experiment/settings.ps1 first."
            )

    def complete(self, messages, temperature=0.2):
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with self.opener.open(request, timeout=120) as response:
                    result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        raise RuntimeError(f"LLM request failed after retries: {last_error}")


def normalize_path(path):
    return str(path).replace("\\", "/").strip().lower()


def load_mapping(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def find_case_mapping(mapping, project, module):
    project_data = mapping.get(project)
    if not project_data:
        return None

    for module_name, file_mapping in project_data.items():
        if module_name.lower() == module.lower():
            return module_name, file_mapping
    return None


def source_project_candidates(source_root, project):
    return [
        source_root / "java" / project / project,
        source_root / "java" / project,
        source_root / project / project,
        source_root / project,
    ]


def find_project_source_dir(source_root, project):
    for candidate in source_project_candidates(source_root, project):
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def build_source_index(project_source_dir):
    index = {}
    for path in project_source_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        relative = normalize_path(path.relative_to(project_source_dir))
        index.setdefault(relative, []).append(path)
    return index


def resolve_by_suffix(source_index, mapped_path):
    suffix = normalize_path(mapped_path)
    matches = []
    for relative, paths in source_index.items():
        if relative.endswith(suffix) or suffix.endswith(relative):
            matches.extend(paths)

    if not matches:
        return None, []

    matches = sorted(set(matches), key=lambda path: len(str(path)))
    return matches[0], matches[1:]


def read_text(path, max_chars):
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    if len(text) <= max_chars:
        return text
    head = max_chars // 2
    tail = max_chars - head
    return (
        text[:head]
        + "\n\n/* ... content truncated for summarization ... */\n\n"
        + text[-tail:]
    )


def summarize_file(client, project, module, mapped_path, source_path, max_chars):
    content = read_text(source_path, max_chars)
    messages = [
        {
            "role": "system",
            "content": (
                "You summarize source files for architecture recovery. "
                "Be concise, precise, and focus on responsibilities, key APIs, "
                "dependencies, and why the file belongs to the target module."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Project: {project}\n"
                f"Target module: {module}\n"
                f"Mapped path: {mapped_path}\n"
                f"Resolved source path: {source_path}\n\n"
                "Summarize this file in Chinese using this format:\n"
                "1. Main responsibilities: ...\n"
                "2. Key structures/API: ...\n"
                "3. Relationship with the target module: ...\n\n"
                "Source code:\n"
                "```text\n"
                f"{content}\n"
                "```"
            ),
        },
    ]
    return client.complete(messages)


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def aggregate_module_summary(client, project, module, file_summaries, chunk_size):
    partials = []
    for chunk_index, chunk in enumerate(chunked(file_summaries, chunk_size), start=1):
        body = "\n\n".join(
            f"file: {item['mapped_path']}\nSummary:\n{item['summary']}" for item in chunk
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You aggregate file-level summaries into architecture module "
                    "summaries. Avoid listing every file unless needed."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Project: {project}\n"
                    f"Module: {module}\n"
                    f"Chunk: {chunk_index}\n\n"
                    "Based on the file summaries below, generate a local summary for this module, including: "
                    "module responsibilities, core capabilities, main code areas, and key dependencies/interactions.\n\n"
                    f"{body}"
                ),
            },
        ]
        partials.append(client.complete(messages))

    if len(partials) == 1:
        body = partials[0]
    else:
        body = "\n\n".join(
            f"Local summary {index}:\n{summary}"
            for index, summary in enumerate(partials, start=1)
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You write final architecture module summaries in Chinese. "
                "Be specific, compact, and useful for architecture analysis."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Project: {project}\n"
                f"Module: {module}\n\n"
                "Aggregate the information below and generate the final module-level summary. Format:\n"
                "# <project> / <module>\n"
                "## Module responsibilities\n"
                "## Core functions\n"
                "## Main code areas\n"
                "## Interactions with other modules\n"
                "## Architecture recognition clues\n\n"
                f"{body}"
            ),
        },
    ]
    return client.complete(messages)


def load_existing_file_summaries(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {item["mapped_path"]: item for item in data.get("files", [])}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


def process_module(args, client, mapping, project, requested_module):
    result = {
        "project": project,
        "requested_module": requested_module,
        "status": "pending",
        "warnings": [],
    }

    case_mapping = find_case_mapping(mapping, project, requested_module)
    if not case_mapping:
        result["status"] = "missing_mapping"
        result["warnings"].append("Mapping not found.")
        return result

    module, file_mapping = case_mapping
    source_dir = find_project_source_dir(args.source_root, project)
    if not source_dir:
        result["status"] = "missing_source"
        result["module"] = module
        result["warnings"].append("Source directory not found.")
        return result

    output_dir = args.output_root / project / module
    file_summary_path = output_dir / "file_summaries.json"
    module_summary_path = output_dir / "module_summary.md"

    source_index = build_source_index(source_dir)
    cached = {} if args.force else load_existing_file_summaries(file_summary_path)

    file_jobs = []
    unmatched = []
    ambiguous = []
    for mapped_path in sorted(file_mapping.keys()):
        source_path, extra_matches = resolve_by_suffix(source_index, mapped_path)
        if not source_path:
            unmatched.append(mapped_path)
            continue
        if extra_matches:
            ambiguous.append(
                {
                    "mapped_path": mapped_path,
                    "chosen": str(source_path),
                    "other_matches": [str(path) for path in extra_matches[:10]],
                }
            )

        if mapped_path in cached:
            continue

        file_jobs.append(
            {
                "mapped_path": mapped_path,
                "source_path": str(source_path),
            }
        )

    summaries = list(cached.values())

    if args.dry_run:
        result.update(
            {
                "status": "dry_run",
                "module": module,
                "source_dir": str(source_dir),
                "mapped_files": len(file_mapping),
                "matched_files": len(file_mapping) - len(unmatched),
                "unmatched_files": len(unmatched),
                "cached_file_summaries": len(cached),
                "pending_file_summaries": len(file_jobs),
            }
        )
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                summarize_file,
                client,
                project,
                module,
                job["mapped_path"],
                Path(job["source_path"]),
                args.max_file_chars,
            ): job
            for job in file_jobs
        }
        for future in as_completed(futures):
            job = futures[future]
            summary_item = {
                "mapped_path": job["mapped_path"],
                "source_path": job["source_path"],
                "summary": future.result(),
            }
            summaries.append(summary_item)

            write_json(
                file_summary_path,
                {
                    "project": project,
                    "module": module,
                    "source_dir": str(source_dir),
                    "files": sorted(summaries, key=lambda item: item["mapped_path"]),
                    "unmatched_files": unmatched,
                    "ambiguous_matches": ambiguous,
                },
            )

    summaries = sorted(summaries, key=lambda item: item["mapped_path"])
    if summaries:
        module_summary = aggregate_module_summary(
            client, project, module, summaries, args.aggregate_chunk_size
        )
        write_text(module_summary_path, module_summary)
        status = "ok"
    else:
        module_summary = ""
        status = "no_matched_files"

    write_json(
        file_summary_path,
        {
            "project": project,
            "module": module,
            "source_dir": str(source_dir),
            "files": summaries,
            "unmatched_files": unmatched,
            "ambiguous_matches": ambiguous,
        },
    )

    result.update(
        {
            "status": status,
            "module": module,
            "source_dir": str(source_dir),
            "mapped_files": len(file_mapping),
            "matched_files": len(file_mapping) - len(unmatched),
            "unmatched_files": len(unmatched),
            "file_summaries": str(file_summary_path),
            "module_summary": str(module_summary_path) if module_summary else None,
        }
    )
    return result


def parse_target(value):
    if ":" not in value:
        raise argparse.ArgumentTypeError("Target must be PROJECT:MODULE")
    project, module = value.split(":", 1)
    project = project.strip()
    module = module.strip()
    if not project or not module:
        raise argparse.ArgumentTypeError("Target must be PROJECT:MODULE")
    return project, module


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate file-level summaries and aggregate module-level summaries "
            "for selected removed modules."
        )
    )
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING_PATH)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--target",
        action="append",
        type=parse_target,
        help="Target module as PROJECT:MODULE. Can be specified multiple times.",
    )
    parser.add_argument("--workers", type=int, default=int(os.environ.get("LLM_PARALLEL_WORKERS", "4")))
    parser.add_argument("--max-file-chars", type=int, default=24000)
    parser.add_argument("--aggregate-chunk-size", type=int, default=30)
    parser.add_argument("--force", action="store_true", help="Regenerate cached file summaries.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve files without calling the LLM.")
    args = parser.parse_args()

    targets = args.target or TARGET_MODULES
    mapping = load_mapping(args.mapping)
    client = None if args.dry_run else ChatClient()

    report = []
    for project, module in targets:
        print(f"[Run] {project}/{module}")
        result = process_module(args, client, mapping, project, module)
        report.append(result)
        print(f"[{result['status']}] {project}/{module}")

    report_path = args.output_root / "run_report.json"
    write_json(report_path, report)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
