import glob
import subprocess
import os
import platform


def get_java_file_list(project_dir):
    return glob.glob(f"{os.path.expanduser(project_dir)}/**/*.java", recursive=True)


def get_import_list(formatter_jar, file):
    all_import = []
    used_import = set()
    
    # 파일을 읽을 때 인코딩을 명시적으로 지정
    with open(file, "r", encoding="utf-8") as f:
        all_import += [line.strip() for line in f if line.strip().startswith("import")]
        result = subprocess.run(["java", "-jar", formatter_jar, "--fix-imports-only", file], stdout=subprocess.PIPE,
                                text=True, encoding="utf-8")
        used_import.update(
            [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("import")]
        )
    
    return all_import, used_import


def del_unused_import(formatter_jar, file):
    subprocess.run(["java", "-jar", formatter_jar, "--replace", file])


def list_of_unused_import(all_import, used_import):
    unused_imports = set()

    for import_line in all_import:
        if import_line not in used_import:
            unused_imports.add(import_line)

    return list(unused_imports)


def find_unused_dependencies(project_dir, formatter_jar, agree=False, callback=None):
    java_files = get_java_file_list(project_dir)
    total_files = len(java_files)
    current_file_index = 0

    all_imports = []
    used_imports = set()

    # 포맷팅된 파일에서 사용된 import 문과 원본 파일의 import 문 비교
    for file in java_files:
        imports, used_import = get_import_list(formatter_jar, file)
        
        all_imports += imports
        used_imports.update(used_import)

        current_file_index += 1
        callback(current_file_index, total_files, file, "Finding")

    # 사용되지 않는 import 문 추출
    unused_imports = list_of_unused_import(all_imports, used_import)

    if len(unused_imports) == 0:
        return []

    # 동의 옵션이 켜져 있지 않은 경우
    if not agree:
        response = input("Do you want to remove unused import statements? (y/n): ")
        agree = True if response.lower() == 'y' else False

    # 미사용 의존성을 지우지 않는 경우
    if not agree:
        print("\nNo input from user. No formatting and import statement removal is performed. ;(\n")
        return unused_imports    
    
    current_file_index = 0
    # 각 Java 파일에 Google Java Formatter를 적용하여 포맷팅 및 사용되지 않는 import문 제거
    for file in java_files:
        del_unused_import(formatter_jar, file)

        current_file_index = current_file_index + 1
        callback(current_file_index, total_files, file, "Removing")

    return unused_imports
