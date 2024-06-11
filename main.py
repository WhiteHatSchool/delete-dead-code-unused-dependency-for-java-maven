from remove_deadcode import handle_deadcode
from FUD import find_unused_dependencies
import os

def progress_callback(idx, cnt, file, step_name):
    progress_percent = round((idx / cnt) * 100, 2)
    print(f"[{step_name}] {file}... {progress_percent}% ({idx} / {cnt})")


def get_unused_import(project_path, formatter_path, agree, callback = None, remove_deadcode = True):
    # Deadcode 처리
    if remove_deadcode:
        handle_deadcode(project_path)

    return find_unused_dependencies(project_path, formatter_path, agree, callback=progress_callback)


if __name__ == "__main__":
    import argparse

    # 1. Parser 생성
    parser = argparse.ArgumentParser(description='FUD: Find DeadCode & Unused Dependencies in Java Project')

    # 2. Argument 추가
    parser.add_argument('-y', dest="agree", action="store_true", help="동의 옵션에서 모두 y를 선택")
    parser.add_argument('-p', '--project', dest="project" , action="store", type=str, default=None, help="프로젝트 경로")
    parser.add_argument('-f', '--formater', dest="format" , action="store", type=str, default=None, help="formater 경로")
    
    args = parser.parse_args()

    # 사용자로부터 프로젝트 경로 입력 받기
    if args.project is None:
        project_dir = input("Write the project's directory: ")
    project_dir = os.path.expanduser(args.project)  # 확장

    # 데드코드 제거 여부 묻기
    remove_deadcode = args.agree
    if not remove_deadcode:
        remove_deadcode_option = input("Do you want to remove dead code? (y/n): ")
        remove_deadcode = True if remove_deadcode_option.lower() == "y" else False

    # FUD.py 코드 실행
    formatter_jar = "./google-java-format-1.22.0-all-deps.jar" if args.format is None else args.format
    print(get_unused_import(project_dir, formatter_jar, agree=args.agree, callback=progress_callback))
