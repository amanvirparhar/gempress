# GemPress

![GemPress Thumbnail](./thumbnail.png)

A Python script that uses Google’s [Gemini-1.5-Flash](https://ai.google.dev/gemini-api/docs/models/gemini#gemini-1.5-flash) model to fix basic typesetting and formatting issues in public domain eBooks from [Project Gutenberg](https://www.gutenberg.org).

## Setup

1. Clone the repository, and `cd` into it:
   ```bash
   git clone https://github.com/amanvirparhar/gempress
   cd gempress
   ```
2. Create a .env file in this directory with the following contents:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
3. Install [`uv`](https://github.com/astral-sh/uv).

## Usage

1. Put the raw text file of the book you want to reformat in the same directory as `main.py`.
2. Change the path to the text file in `main.py` to the name of the file you want to reformat.
3. Run the script:
   ```bash
   uv run --with-requirements requirements.txt --python 3.13 main.py
   ```
4. You should find an ePub file in the same directory as `main.py` with the same name as the input file (except with the `.epub` file extension).
5. Feel free to play around with `prompt.txt`.
