import glob
import os
import subprocess


def get_java_file_list(project_dir):
    return glob.glob(f"{os.path.expanduser(project_dir)}/**/*.java", recursive=True)


def get_import_list(formatter_jar, file):
    file_import = []
    # 파일을 읽을 때 인코딩을 명시적으로 지정
    with open(file, "r", encoding="utf-8") as f:
        file_import += [line.strip() for line in f if line.strip().startswith("import")]

    return list(map(lambda x: x.replace("import ", "").replace(";", ""), file_import))


def del_unused_import(formatter_jar, file):
    return subprocess.run(["java", "-jar", formatter_jar, "--replace", file])


def get_wildcard_import(import_statement):
    if import_statement.endswith(".*"):
        return import_statement
    else:
        parts = import_statement.split('.')
        if len(parts) > 1:
            parts.pop()
            return '.'.join(parts) + '.*'
        else:
            return import_statement + '.*'


def list_of_unused_import(all_import, used_import):
    unused_imports = set()
    for import_line in all_import:
        if get_wildcard_import(import_line) not in used_import and import_line not in used_import:
            unused_imports.add(import_line)

    for import_line in unused_imports:
        if get_wildcard_import(import_line) in used_import:
            unused_imports.remove(import_line)

    return list(unused_imports)


def find_unused_dependencies(project_dir, formatter_jar, callback=None):
    java_files = get_java_file_list(project_dir)
    total_files = len(java_files)

    ##########  find all imports  ##########
    all_imports = []
    current_file_index = 0
    # 포맷팅된 파일에서 사용된 import 문과 원본 파일의 import 문 비교
    for file in java_files:
        all_imports += get_import_list(formatter_jar, file)

        current_file_index += 1
        callback(current_file_index, total_files, file, "Finding")

    ##########  delete import and find used import  ##########
    used_import = set()
    current_file_index = 0
    # 각 Java 파일에 Google Java Formatter를 적용하여 포맷팅 및 사용되지 않는 import문 제거
    for file in java_files:
        del_unused_import(formatter_jar, file)

        used_import.update(get_import_list(formatter_jar, file))
        current_file_index = current_file_index + 1
        callback(current_file_index, total_files, file, "Removing")

    ##########  find unused import  ##########
    unused_imports = list_of_unused_import(all_imports, used_import)
    if len(unused_imports) == 0:
        return []

    return unused_imports
