import os
import argparse
import json

from call_deepseek_withFeedback import traverse_and_process


class PackageNode:
    def __init__(self, name, parent=None):
        """
        Initialize package node
        :param name: Package name
        :param parent: Parent package node
        """
        self.name = name
        self.parent = parent  # Parent package node
        self.children = {}  # Dictionary of child packages, key is child package name, value is PackageNode instance
        self.files = []  # List of file nodes

    def add_child(self, child_name):
        """
        Add child package
        :param child_name: Child package name
        :return: Newly created child package node
        """
        if child_name not in self.children:
            self.children[child_name] = PackageNode(child_name, parent=self)
        return self.children[child_name]

    def add_file(self, file_node):
        """
        Add file node
        :param file_node: FileNode instance
        """
        self.files.append(file_node)

    def get_full_package_name(self):
        """
        Get full package name (including parent packages)
        :return: Full package name
        """
        names = []
        node = self
        while node.parent is not None:
            names.insert(0, node.name)
            node = node.parent
        return ".".join(names) if names else self.name


class FileNode:
    def __init__(self, name, parent_package, project_root):
        """
        Initialize file node
        :param name: File name
        :param parent_package: Parent PackageNode instance
        :param project_root: Project root directory
        """
        self.name = name
        self.parent = parent_package  # Parent package node
        self.project_root = project_root  # Project root directory
        self.full_path = self.get_absolute_path()

    def get_absolute_path(self):
        """
        Get file's absolute path
        :return: File's absolute path
        """
        # Get package path (relative to project root)
        package_path = self.get_package_path()

        # If the first part of project root and package path are the same, remove the duplicate part
        if package_path and package_path[0] == os.path.basename(self.project_root):
            package_path = package_path[1:]

        # Concatenate project root and package path, avoiding duplicate root path
        return os.path.join(self.project_root, *package_path, self.name)

    def get_package_path(self):
        """
        Get the package path of the file (relative to project root)
        :return: Package path (as a list)
        """
        path = []
        current = self.parent
        while current is not None:
            path.insert(0, current.name)
            current = current.parent
        return path


def parse_java_project(project_path, exclude_dirs=None):
    """
    Parse Java project directory and build package tree (based on directory structure)
    :param project_path: Project root directory path
    :param exclude_dirs: List of directories to exclude
    :return: Root node of the package tree
    """
    if not os.path.exists(project_path) or not os.path.isdir(project_path):
        raise ValueError("Invalid project path.")

    root = PackageNode(os.path.basename(os.path.abspath(project_path)))

    for current_dir, dirs, files in os.walk(project_path):
        # Exclude specified directories
        if exclude_dirs:
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # Calculate relative path of current directory to project root
        rel_path = os.path.relpath(current_dir, project_path)
        if rel_path == ".":
            current_node = root
        else:
            # Directly split the path using os.sep
            package_names = rel_path.split(os.sep)
            current_node = root
            for pkg in package_names:
                current_node = current_node.add_child(pkg)

        # Add Java files
        for file in files:
            if file.endswith(".java"):
                file_node = FileNode(file, parent_package=current_node, project_root=project_path)
                current_node.add_file(file_node)

    return root


def prune_tree(node):
    """
    Prune the package tree by removing nodes that have no Java files and all their subpackages also have no Java files.
    :param node: Current package node
    :return: Whether to keep the current node
    """
    # First, recursively prune child packages
    children_to_remove = []
    for child_name, child_node in node.children.items():
        if not prune_tree(child_node):
            children_to_remove.append(child_name)
    for child_name in children_to_remove:
        del node.children[child_name]

    # If the current node has no files and no child packages, do not keep it
    if not node.files and not node.children:
        return False
    return True


def print_tree(node, indent=0):
    """
    Print the package tree structure to the console
    :param node: Current package node
    :param indent: Indentation level
    """
    prefix = '  ' * indent
    if node.parent is None:
        print(f"{prefix}Package: {node.name}")
    else:
        print(f"{prefix}Package: {node.get_full_package_name()}")
    for file in node.files:
        print(f"{prefix}  File: {file.name} (Path: {file.full_path})")
    for child in sorted(node.children.values(), key=lambda x: x.name):
        print_tree(child, indent + 1)


def list_all_files_with_full_paths(node, output_text_file=None):
    """
    List all files' full package paths and optionally save to a text file
    :param node: Current package node
    :param output_text_file: Output text file name (optional)
    """
    file_paths = []

    def recurse(current_node):
        for file in current_node.files:
            file_paths.append(file.full_path)
        for child in current_node.children.values():
            recurse(child)

    recurse(node)

    if output_text_file:
        with open(output_text_file, 'w', encoding='utf-8') as f:
            for path in file_paths:
                f.write(path + '\n')
        print(f"All Java files' full package paths have been saved to {output_text_file}")
    else:
        print("All Java files' full package paths:")
        for path in file_paths:
            print(path)


def traverse_from_all_files(node):
    """
    Starting from all file nodes, traverse upwards through parent package nodes and print each file's package path
    :param node: Root package node
    """
    file_nodes = []

    def collect_files(current_node):
        for file in current_node.files:
            file_nodes.append(file)
        for child in current_node.children.values():
            collect_files(child)

    collect_files(node)

    for file in file_nodes:
        path = []
        current = file.parent
        while current is not None and current.parent is not None:
            path.insert(0, current.name)
            current = current.parent
        full_path = ".".join(path) + f".{file.name}" if path else file.name
        print(full_path)


def save_node_to_module_mapping(node_to_module, mapping_output_file):
    """
    Saves the node_to_module mapping to a JSON file.
    :param node_to_module: Dictionary mapping PackageNode instances to module names.
    :param mapping_output_file: Path to the output JSON file.
    """
    try:
        output_json_path = os.path.join(output_directory, mapping_output_file)
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(node_to_module, json_file, indent=4)
        print(f"Package to module mapping has been saved to {mapping_output_file}")
    except Exception as e:
        print(f"Error saving mapping to {mapping_output_file}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Parse Java project package structure and list all Java files' full package paths.")
    parser.add_argument('project_path', help='Java project root directory path')
    parser.add_argument('--mapping_output', default='module_mapping.json',
                        help='Path to save the package to module mapping as a JSON file (default: module_mapping.json)')
    parser.add_argument('--exclude', nargs='*', help='List of directories to exclude, e.g., --exclude test build out')
    parser.add_argument('--module_path', help='Path of the documentation module name')
    parser.add_argument('--tfidf_result_path', help='Path of the tfidf result')
    parser.add_argument('--output_path', help='Path of the output')
    args = parser.parse_args()

    project_path = args.project_path
    output_path = args.output_path
    mapping_output_file = os.path.join(output_path, args.mapping_output)
    exclude_dirs = args.exclude if args.exclude else None
    module_path = args.module_path
    json_path=args.tfidf_result_path

    if not os.path.exists(project_path):
        print(f"Project path does not exist: {project_path}")
        return
    try:
        package_tree = parse_java_project(project_path, exclude_dirs=exclude_dirs)
        # Prune the package tree by removing branches with no Java files
        prune_success = prune_tree(package_tree)
        if not prune_success:
            print("No Java files in the project.")
            return
        print("Package structure tree (text form):")
        # print_tree(package_tree)
        print("\nAll Java files' full package paths:")
        # list_all_files_with_full_paths(package_tree, output_text_file=output_file)

        print("\nDetermining package paths based on all Java files:")
        node_to_module = traverse_and_process(package_tree, module_path, json_path, project_path, output_path)

        #print("\nSaving package to module mapping:")
        #save_node_to_module_mapping(node_to_module, mapping_output_file)

    except ValueError as ve:
        print(f"Error: {ve}")


if __name__ == "__main__":
    main()
