from datetime import datetime
import json
import re
from typing import Callable, IO

import markdown
from pydantic import BaseModel, Field, ValidationError

NOW_FACTORY = datetime.now
GLOBAL_USER_ID = 1


class BaseMetadata(BaseModel):
    title: str = Field(...)
    tags: list[str] = Field(...)
    categories: list[str] = Field(...)
    user_id: int = Field(...)


class PromptData(BaseMetadata):
    content: str = Field(...)
    created_at: datetime = Field(default_factory=NOW_FACTORY)
    updated_at: datetime = Field(default_factory=NOW_FACTORY)

    class Config:
        validate_assignment = True

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name != 'updated_at':
            self.__dict__['updated_at'] = NOW_FACTORY()


class FileReader:

    def __init__(self, read_strategy: Callable[[str | IO], any], file_path: str = None):
        self.read_strategy = read_strategy
        self.data = None
        self.file_path = file_path

    def read(self, file_path: str | None = None) -> 'FileReader':
        if file_path:
            self.file_path = file_path
        with open(self.file_path, 'r') as file:
            self.data = self.read_strategy(file)
        return self

    def process(self, metadata: dict | None) -> PromptData | None:
        if not metadata:
            metadata = {
                "title": self.file_path.split('/')[-1].split('.')[0] if self.file_path else "No Title",
                'tags': [],
                "categories": [],
                "user": GLOBAL_USER_ID,
            }

        try:
            BaseMetadata(**metadata)  # Check if metadata is valid
        except ValidationError as e:
            print(f"Invalid metadata: {e}")
            return None

        metadata['content'] = self.data
        return PromptData(**metadata)


class FileReaderFactory:

    def __init__(self, filepath: str = None):
        self.filepath = filepath

    @staticmethod
    def json_read_strategy(file: IO) -> dict:
        return json.load(file)

    @staticmethod
    def markdown_read_strategy(file: IO) -> str:
        return markdown.markdown(file.read())

    @staticmethod
    def plain_text_read_strategy(file: IO) -> str:
        return file.read()

    def create(self) -> FileReader:
        if self.filepath.endswith('.json'):
            return FileReader(read_strategy=self.json_read_strategy).read(self.filepath)
        elif self.filepath.endswith('.md'):
            return FileReader(read_strategy=self.markdown_read_strategy).read(self.filepath)
        elif self.filepath.endswith('.txt'):
            return FileReader(read_strategy=self.plain_text_read_strategy).read(self.filepath)
        else:
            raise ValueError(f'Unsupported file type for: {self.filepath}')


class FileWriter:
    def __init__(self, data: PromptData, file_path: str = None):
        self.file_path = file_path
        self.data = data

    def write(self, data: dict | PromptData | None = None, file_path: str | None = None):
        if file_path:
            self.file_path = file_path

        if data:
            self.data = data

        if not isinstance(self.data, dict):
            self.data = dict(self.data)

        with open(self.file_path, 'w') as file:
            json.dump(self.data, file)


def process_markdown(markdown_content):
    title_match = re.search(r'<h1>(.*?)</h1>', markdown_content)
    title = title_match.group(1) if title_match else 'No Title'

    # Extract the content inside <p><code> tags
    content_match = re.search(r'<p><code>(.*?)</code></p>', markdown_content, re.DOTALL)
    content = content_match.group(1) if content_match else 'No Content'

    # Clean the 'markdown' indicator if present
    content = re.sub(r'^markdown\n', '', content)

    return title, content


if __name__ == '__main__':
    from pprint import pprint
    # Test the prompt class
    prompt = PromptData(
        title='Test', content='This is a test prompt', tags=['test'], categories=['test'], user_id=GLOBAL_USER_ID
    )

    pprint(dict(prompt))

    # wait 5 seconds
    from time import sleep
    sleep(5)

    # Change the title to check if updated_at is updated
    prompt.title = 'Test 2'
    pprint(dict(prompt))
