import os
import re
import subprocess
import platform


def make_executable(path):
    """Make the file at the given path executable."""
    if platform.system() != 'Windows':
        mode = os.stat(path).st_mode
        mode |= (mode & 0o444) >> 2    # Copy R bits to X.
        os.chmod(path, mode)


def run_pmd(pmd_path, project_dir, ruleset_path, report_path):
    try:
        result = subprocess.run(
            [pmd_path, "check", "-d", project_dir, "-R", ruleset_path, "-f", "text", "-r", report_path],
            capture_output=True,
            text=True,
            shell=(platform.system() == 'Windows')
        )
        if result.returncode not in (0, 4):  # 4는 위반 사항이 있을 때 반환되는 코드
            raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout,
                                                stderr=result.stderr)
    except subprocess.CalledProcessError as e:
        print("Error during DeadCode analysis: " + str(e))  # DeadCode 분석 중 오류가 발생했습니다
        print(e.output)
        print(e.stderr)  # 오류 메시지 출력 추가
        raise RuntimeError("Failed to run PMD analysis")


def parse_pmd_report(report_path):
    deadcode_positions = []
    pattern = re.compile(r'^(.*?):(\d+):\s*')

    with open(report_path, 'r', encoding='utf-8') as file:
        for line in file:
            if any(keyword in line for keyword in
                   ['UnusedLocalVariable', 'UnusedPrivateField', 'UnusedPrivateMethod', 'UnusedAssignment']):
                match = pattern.match(line)
                if match:
                    file_path = match.group(1).strip()
                    line_number_str = match.group(2).strip()
                    try:
                        line_number = int(line_number_str)
                        deadcode_positions.append((file_path, line_number, line.strip()))
                    except ValueError as e:
                        print("Failed to parse line number: " + line.strip() + " - " + str(e))  # 라인 번호 파싱 실패
                else:
                    print("Unexpected format: " + line.strip())  # 예상치 못한 형식
    return deadcode_positions


def remove_unused_line(lines, line_number, removed_lines, line_adjustments, first_pass):
    line_index = line_number - 1
    if 0 <= line_index < len(lines):
        content = lines[line_index].strip()
        if content:
            removed_lines.append((line_index, content))  # 제거된 라인을 리스트에 추가
        lines.pop(line_index)  # 해당 라인을 리스트에서 제거
        if not first_pass:
            for i in range(line_index, len(line_adjustments)):
                line_adjustments[i] += 1  # 이후 라인의 원본 줄 번호를 1씩 증가


def remove_unused_private_method(lines, line_number, removed_lines, line_adjustments, first_pass):
    start_line = line_number - 1
    while start_line >= 0 and not re.search(r'\bprivate static\b', lines[start_line]):
        start_line -= 1

    if start_line < 0:
        return

    brace_line = start_line
    while brace_line < len(lines) and '{' not in lines[brace_line]:
        brace_line += 1

    if brace_line >= len(lines):
        return

    brace_count = 0
    end_line = brace_line
    while end_line < len(lines):
        brace_count += lines[end_line].count("{")
        brace_count -= lines[end_line].count("}")
        end_line += 1
        if brace_count == 0:
            break

    removed_lines.extend((i, lines[i].strip()) for i in range(start_line, end_line) if lines[start_line].strip())
    for i in range(end_line - 1, start_line - 1, -1):
        lines.pop(start_line)
    if not first_pass:
        for i in range(start_line, len(line_adjustments)):
            line_adjustments[i] += (end_line - start_line)

def remove_deadcode(file_path, issues, first_pass, debug = False):
    if not os.path.exists(file_path):
        if debug:
            print("File does not exist: " + file_path)  # 파일이 존재하지 않습니다
        return [], []

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    line_adjustments = [0] * len(lines)
    removed_lines = []

    for line_number, issue in sorted(issues, key=lambda x: x[0], reverse=True):
        if 'UnusedLocalVariable' in issue or 'UnusedAssignment' in issue or 'UnusedPrivateField' in issue:
            remove_unused_line(lines, line_number, removed_lines, line_adjustments, first_pass)
        elif 'UnusedPrivateMethod' in issue:
            remove_unused_private_method(lines, line_number, removed_lines, line_adjustments, first_pass)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

    return removed_lines, line_adjustments


def handle_deadcode(project_dir, debug = False):
    base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 디렉토리를 기준으로 경로 설정
    if platform.system() == 'Windows':
        pmd_path = os.path.join(base_dir, "PMD_deadcode_search", "bin", "pmd.bat")  # PMD 실행 파일의 경로
    else:
        pmd_path = os.path.join(base_dir, "PMD_deadcode_search", "bin", "pmd")  # PMD 실행 파일의 경로
    ruleset_path = os.path.join(base_dir, "PMD_deadcode_search", "deadcode.xml")  # 규칙 파일 경로
    report_path = os.path.join(base_dir, "PMD_deadcode_search", "report", "report.txt")  # 결과 보고서 파일 상대 경로

    # Make the PMD file executable if on a Unix-like system
    if platform.system() != 'Windows':
        make_executable(pmd_path)

    try:
        # PMD를 전체 프로젝트 디렉토리에 대해 실행
        run_pmd(pmd_path, project_dir, ruleset_path, report_path)

        deadcode_positions = parse_pmd_report(report_path)

        if not deadcode_positions:
            print("\nNo more DeadCode to remove!")  # 더 이상 제거할 DeadCode가 없습니다
            return

        # 파일별로 그룹화
        grouped_positions = {}
        for file_path, line_number, issue in deadcode_positions:
            if file_path not in grouped_positions:
                grouped_positions[file_path] = []
            grouped_positions[file_path].append((line_number, issue))

        total_files = len(grouped_positions)
        current_file_index = 0

        # 각 파일에 대해 데드 코드 제거
        for file_path, issues in grouped_positions.items():
            removed_lines, line_adjustments = remove_deadcode(file_path, issues, first_pass=True, debug=debug)
            for line_index, content in removed_lines:
                original_line_number = line_index + 1  # 줄 번호는 1부터 시작
                adjusted_line_number = original_line_number + line_adjustments[line_index]
                if debug:
                    print(f"[+] Removed DeadCode at {file_path}:{adjusted_line_number}: <{content}>")  # DeadCode 제거 완료

            current_file_index += 1
            progress_percent = round((current_file_index / total_files) * 100, 2)
            print(f"Removing DeadCode... {progress_percent}% ({current_file_index} / {total_files})")
            if debug:
                print(f"[+] Processed file: {file_path} ({progress_percent}%)")
    except RuntimeError as e:
        print("\nFailed to perform deadcode analysis due to an error.")

