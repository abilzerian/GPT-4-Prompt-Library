import os
from typing import Callable

from format_conversions.converters import (
    FileReaderFactory, FileWriter, process_markdown, process_json, process_plain_text
)

PARENT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_directories(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


def make_dirs(path, directories):
    for directory in directories:
        os.makedirs(os.path.join(path, directory), exist_ok=True)


def process_directories():
    parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    output_path = os.path.join(parent_path, 'processed_prompts')
    dirs = get_directories(parent_path)

    # Skip hidden directories and the processed_prompts dir
    dirs = [d for d in dirs if not d.startswith('.') and d not in ['processed_prompts', 'venv']]

    print(dirs)
    make_dirs(output_path, dirs)


def process_files(
        input_path: str,
        processing_function: Callable[[str], any],
        output_path: str = os.path.join(PARENT_PATH, 'processed_prompts')
) -> None:
    file_reader = FileReaderFactory(input_path).create()
    data = processing_function(file_reader.data)

    output = file_reader.process(*data)

    output_path = os.path.join(output_path, input_path.split('/')[-2], f"{output.title}.json")

    file_writer = FileWriter(data=output, file_path=output_path)
    file_writer.write()


def rename_files_in_subdirectories(root_directory, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = []

    # List all directories one level down from the root, excluding hidden and specified directories
    subdirectories = [
        os.path.join(root_directory, d)
        for d in os.listdir(root_directory)
        if os.path.isdir(os.path.join(root_directory, d)) and not d.startswith('.') and d not in exclude_dirs
    ]

    for subdirectory in subdirectories:
        for filename in os.listdir(subdirectory):
            file_path = os.path.join(subdirectory, filename)
            if os.path.isfile(file_path):
                new_filename = filename.replace(' ', '_')
                new_file_path = os.path.join(subdirectory, new_filename)
                os.rename(file_path, new_file_path)
                print(f"Renamed: {file_path} -> {new_file_path}")


if __name__ == '__main__':
    PROCESS_DIRECTORIES = False
    RENAME_FILES = False
    EXCLUDE_DIRS = ['venv', 'processed_prompts', "format_conversions"]

    if PROCESS_DIRECTORIES:
        process_directories()

    script_directory = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_directory, '..'))

    if RENAME_FILES:
        rename_files_in_subdirectories(root_dir, EXCLUDE_DIRS)

    INPUT_PATH = os.path.join(PARENT_PATH, 'miscellaneous')
    for file in os.listdir(INPUT_PATH):
        if file.endswith('.md'):
            process_files(os.path.join(INPUT_PATH, file), processing_function=process_markdown)
        elif file.endswith('.json'):
            process_files(os.path.join(INPUT_PATH, file), processing_function=process_json)
        elif file.endswith('.txt'):
            process_files(os.path.join(INPUT_PATH, file), processing_function=process_plain_text)
        else:
            print(f"Unsupported file format: {file}")
