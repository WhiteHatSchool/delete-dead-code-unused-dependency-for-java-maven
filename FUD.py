import glob
import subprocess
import os
import platform

def find_unused_dependencies(project_dir, formatter_jar, debug, agree=False):
    project_dir = os.path.expanduser(project_dir)
    java_files = glob.glob(f"{project_dir}/**/*.java", recursive=True)
    total_files = len(java_files)
    current_file_index = 0

    # 포맷팅된 파일에서 사용된 import 문과 원본 파일의 import 문 비교
    original_imports = []
    formatted_imports = []

    print("\n" + "-" * 100)

    for file in java_files:
        # 파일을 읽을 때 인코딩을 명시적으로 지정
        with open(file, "r", encoding="utf-8") as f:
            original_imports += [line.strip() for line in f if line.strip().startswith("import")]
            result = subprocess.run(["java", "-jar", formatter_jar, "--fix-imports-only", file], stdout=subprocess.PIPE,
                                    text=True, encoding="utf-8")
            formatted_imports += [line.strip() for line in result.stdout.splitlines() if
                                  line.strip().startswith("import")]

        # 진행 상황 업데이트
        current_file_index += 1
        progress_percent = round((current_file_index / total_files) * 100, 2)

        # 진행률 표시
        print(f"\nFinding Unused Dependency... {progress_percent}% ({current_file_index} / {total_files})")

        # 디버그 메시지 (옵션)
        if debug:
            print(f"[+] {file} ({progress_percent}%)")

    # 사용되지 않는 import 문 추출
    unused_imports = []
    for import_line in original_imports:
        is_used = any(import_line == formatted_import for formatted_import in formatted_imports)
        if not is_used:
            unused_imports.append(import_line)

    print("\n" + "-" * 100)
    print("\n** Original Import List **")
    print("\n".join(original_imports))

    print("\n** Unused Import List **")

    # 사용되지 않은 Import문이 존재할 경우
    if unused_imports:
        print("\n".join(unused_imports))
        print("\n" + "-" * 100)

        if not agree:
        # 사용자의 입력 받기
            response = input("Do you want to remove unused import statements? (y/n): ")
            agree = True if response.lower() == 'y' else False

        # 사용자가 'y'를 입력한 경우
        if agree:
            # 각 Java 파일에 Google Java Formatter를 적용하여 포맷팅 및 사용되지 않는 import문 제거
            for file in java_files:
                print(f"\n[+] Formatting and removing unused import statements: {file}")
                subprocess.run(["java", "-jar", formatter_jar, "--replace", file])
            print("\nComplete formatting and removing unused import statements! XD\n")

        # 사용자가 'n'을 입력한 경우
        else:
            print("\nNo input from user. No formatting and import statement removal is performed. ;(\n")

    # 사용되지 않은 Import문이 존재하지 않을 경우
    else:
        print("\n" + "-" * 100)
        print("\nThere are no unused import statements. ;(\n")
