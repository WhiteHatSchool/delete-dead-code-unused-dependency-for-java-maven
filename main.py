import os
import re
import glob
import argparse

from remove_deadcode import handle_deadcode
from FUD import find_unused_dependencies
import xml.etree.ElementTree as ET

def progress_callback(idx, cnt, file, step_name):
    progress_percent = round((idx / cnt) * 100, 2)
    print(f"[{step_name}] {progress_percent}% ({idx} / {cnt}) - {file}...")


def del_dead_code(project_path):
    handle_deadcode(project_path)


def get_unused_import(project_path, formatter_path, callback = progress_callback):
    return find_unused_dependencies(project_path, formatter_path, callback=callback)


def pom_path_lists(pom_path_lists: list):
    group_id = set()
    for file in pom_path_lists:
        tree = ET.parse(file)
        root = tree.getroot()

        xmlns = ''

        m = re.search('{.*}', root.tag)
        if m:
            xmlns = m.group(0)

        tag = root.find(xmlns + 'groupId')
        if tag is not None:
            group_id.add(tag.text)

    return list(group_id)


def remove_elements_containing_substring(lst, substring):
    return [element for element in lst if substring not in element]


def del_local_dependency(unused_imports, project_group_id):
    for group_id in project_group_id:
        unused_imports = remove_elements_containing_substring(unused_data, group_id)

    return unused_imports

def pom_project_process(project_dir_path: str, formatter_jar_path: str):
    del_dead_code(project_dir)
    unused_data = get_unused_import(project_dir_path, formatter_jar_path, callback=progress_callback)
    pom_files = glob.glob(f"{os.path.expanduser(project_dir_path)}/**/pom.xml", recursive=True)
    project_group_id = pom_path_lists(pom_files)

    return del_local_dependency(unused_data, project_group_id)

if __name__ == "__main__":
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
    
    if remove_deadcode:
        del_dead_code(project_dir)
    
    # FUD.py 코드 실행
    formatter_jar = "./google-java-format-1.22.0-all-deps.jar" if args.format is None else args.format
    unused_data = get_unused_import(project_dir, formatter_jar, callback=progress_callback)

    pom_files = glob.glob(f"{os.path.expanduser(project_dir)}/**/pom.xml", recursive=True)
    project_group_id = pom_path_lists(pom_files)

    print(del_local_dependency(unused_data, project_group_id))
