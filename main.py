import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel
import pypub
from html2image import Html2Image


class GemPress:
    def __init__(self, input_file: str, model_name: str = "models/gemini-1.5-flash"):
        # path to the book file
        self.input_file = input_file

        # gemini model
        self.model_name = model_name

        # html2image config
        self.hti = Html2Image()
        self.hti.browser.use_new_headless = True

        # gemini config
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])

        # read prompt from prompt.txt
        with open("prompt.txt", "r") as file:
            self.prompt = file.read()

        self.paragraphs = []
        self.tagged_content = ""
        self.book_data = None

    def load_and_tag_content(self):
        # split the book content into paragraphs
        with open(self.input_file, "r") as file:
            self.paragraphs = file.read().split("\n\n")

        # create a new file with tagged paragraphs
        self.tagged_content = ""
        for i, paragraph in enumerate(self.paragraphs):
            stripped_paragraph = paragraph.strip()
            if stripped_paragraph == "":
                continue
            self.tagged_content += f"<p_{i}>{stripped_paragraph}</p_{i}>\n"
            self.paragraphs[i] = stripped_paragraph

    def generate_book_data(self):
        class ChapterData(BaseModel):
            # pydantic model for each chapter
            number: int
            name: str
            tag_index_of_first_paragraph: int
            tag_index_of_last_paragraph: int

        class BookData(BaseModel):
            # pydantic model for the book data
            title: str
            author: str
            is_poetry: bool
            chapters: list[ChapterData]

        class TextToModify(BaseModel):
            # pydantic model for text to modify in the book
            tag_index_of_paragraph: int
            explanation: str
            exact_string_to_find: str
            exact_string_to_replace: str

        # generate data regarding the book using gemini and the schemas defined above
        response = genai.GenerativeModel(model_name=self.model_name).generate_content(
            f"{self.prompt}\n{self.tagged_content}",
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=BookData),
            request_options={
                "timeout": 600
            },
        )

        # parse the response and clean up the data
        self.book_data = json.loads(response.text)
        self.book_data["title"] = self.book_data["title"].strip()
        self.book_data["author"] = self.book_data["author"].strip()
        for chapter in self.book_data["chapters"]:
            chapter["name"] = chapter["name"].strip()

    def generate_cover(self):
        # cover in html (will later be converted to an image)
        html_cover = f'''
        <html>
        <head>
            <style>
                html {{
                    width: 1600px;
                    height: 2400px;
                }}
                body {{
                    margin: 0;
                    height: 100%;
                    background-color: #d9aa5a;
                    color: #332014;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    align-items: center;
                    font-family: 'Junicode', serif;
                }}
                .title {{
                    padding-top: 250px;
                    padding-left: 100px;
                    padding-right: 100px;
                    text-align: center;
                    font-size: 200px;
                    letter-spacing: -4px;
                    font-weight: 700;
                    line-height: 0.9;
                }}
                .author {{
                    padding-bottom: 250px;
                    text-align: center;
                    font-size: 100px;
                    letter-spacing: -2px;
                    font-weight: 400;
                    line-height: 0.9;
                }}
            </style>
        </head>
        <body>
            <div class="title">{self.book_data["title"]}</div>
            <div class="author">{self.book_data["author"]}</div>
        </body>
        </html>
        '''

        # save the cover as an image
        self.hti.screenshot(
            html_str=html_cover,
            save_as='cover.png',
            size=(1600, 2400)
        )

    def create_epub(self):
        # create an epub file
        epub = pypub.Epub(
            title=self.book_data["title"],
            creator=self.book_data["author"],
            cover="cover.png"
        )

        # if poems, then use <br/>; otherwise, use space
        separator = " "
        if self.book_data["is_poetry"]:
            separator = "<br/>"

        for chapter in self.book_data["chapters"]:
            chapter_html = ""
            start_idx = chapter["tag_index_of_first_paragraph"]
            end_idx = chapter["tag_index_of_last_paragraph"]

            # add formatted paragraphs to the current chapter
            for i in range(start_idx, end_idx + 1):
                self.paragraphs[i] = self.paragraphs[i].replace(
                    "\n", separator)
                chapter_html += f"<p>{self.paragraphs[i]}</p>\n"

            # either use the chapter number or the chapter name as the title
            chapter_title = f"Chapter {chapter['number']}"
            if "name" in chapter.keys() and chapter["name"].strip() != "":
                chapter_title = f"{chapter['name']}"

            # create and add the chapter to the epub
            epub_chapter = pypub.create_chapter_from_html(
                html=chapter_html.encode(),
                title=chapter_title
            )
            epub.add_chapter(epub_chapter)

        # save the epub file to the disk
        epub.create(self.book_data['title'].replace(' ', '_').lower())

        # delete the cover image from the disk after creating the epub
        os.remove("cover.png")

    def process_book(self):
        self.load_and_tag_content()
        self.generate_book_data()
        self.generate_cover()
        self.create_epub()


if __name__ == "__main__":
    # load environment variables from .env file
    load_dotenv()

    # process the book with GemPress (provide path to the book file)
    gempress = GemPress("a_boys_will.txt")
    gempress.process_book()
