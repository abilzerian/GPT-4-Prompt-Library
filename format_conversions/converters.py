from datetime import datetime
import json
import re
from typing import Callable, IO

from bs4 import BeautifulSoup

import markdown
from pydantic import BaseModel, Field, ValidationError

NOW_FACTORY = datetime.now
GLOBAL_USER_ID = 1
NO_TITLE_PLACEHOLDER = "No Title"
NO_CONTENT_PLACEHOLDER = "No Content"


class BaseMetadata(BaseModel):
    title: str = Field(...)
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    user_id: int = Field(default_factory=lambda: GLOBAL_USER_ID)


def convert_datetime_to_custom_format(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d %H:%M:%S')


class PromptData(BaseMetadata):
    content: str = Field(...)
    created_at: datetime = Field(default_factory=NOW_FACTORY)
    updated_at: datetime = Field(default_factory=NOW_FACTORY)

    class Config:
        validate_assignment = True
        json_encoders = {
            datetime: convert_datetime_to_custom_format
        }

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

    def process(
            self,
            data: dict | None,
            content: str | None = None,
    ) -> PromptData | None:
        if not data:
            data = {"title": self.file_path.split('/')[-1].split('.')[0] if self.file_path else NO_TITLE_PLACEHOLDER}

        try:
            BaseMetadata(**data)  # Check if metadata is valid
        except ValidationError as e:
            print(f"Invalid metadata: {e}")
            return None

        if content:
            self.data = content
        data['content'] = self.data
        return PromptData(**data)


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

    def write(self, data: PromptData | None = None, file_path: str | None = None):
        if file_path:
            self.file_path = file_path

        if data:
            self.data = data

        with open(self.file_path, 'w') as file:
            file.write(self.data.json())


def process_markdown(markdown_content):
    title_match = re.search(r'<h1>(.*?)</h1>', markdown_content)
    title = title_match.group(1) if title_match else NO_TITLE_PLACEHOLDER

    # Parse the content and remove the Markdown tags
    soup = BeautifulSoup(markdown_content, 'lxml')
    content = soup.get_text()

    # Clean the 'markdown' indicator and title, if present
    content = content.replace(title, '', 1).strip()
    content = content.replace('markdown\n', '', 1).strip()
    content = content.replace("```", "").strip()

    if not content:
        content = NO_CONTENT_PLACEHOLDER

    return title, content


def process_json(json_data):
    """Process json files and return the content.

        Returns No Title so that the title can be set to the filename downstream.
        """
    return NO_TITLE_PLACEHOLDER, json.dumps(json_data)


def process_plain_text(text_content):
    """Process plain text files and return the content.

    Returns No Title so that the title can be set to the filename downstream.
    """
    return NO_TITLE_PLACEHOLDER, text_content


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
