import html
from html.parser import HTMLParser
from pathlib import Path

import requests
from telegraph import Telegraph


class HTMLContentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self.in_title = False
        self.in_body = False
        self.body_content = []
        self.skip_script = False
        self.skip_style = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "body":
            self.in_body = True
        elif tag == "script":
            self.skip_script = True
        elif tag == "style":
            self.skip_style = True
        elif self.in_body and not self.skip_script and not self.skip_style:
            attr_str = " ".join(f'{k}="{v}"' for k, v in attrs if v is not None)
            self.body_content.append(f"<{tag} {attr_str}>" if attr_str else f"<{tag}>")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "body":
            self.in_body = False
        elif tag == "script":
            self.skip_script = False
        elif tag == "style":
            self.skip_style = False
        elif self.in_body and not self.skip_script and not self.skip_style:
            self.body_content.append(f"</{tag}>")

    def handle_data(self, data):
        if self.in_title and not self.skip_script and not self.skip_style:
            if not self.title:
                self.title = data.strip()
        elif self.in_body and not self.skip_script and not self.skip_style:
            self.body_content.append(data)

    def get_body_html(self):
        return "".join(self.body_content).strip()


class Grapher(Telegraph):
    def __init__(self, access_token=None, domain_graph=None):
        self.domain_graph = domain_graph or "telegra.ph"
        self.base_url = f"https://{self.domain_graph}"
        self.TEXT_EXTENSIONS: set[str] = {".txt", ".md"}

        super().__init__(access_token=access_token)

    @staticmethod
    def _read_text_file(file_path: str | Path, missing_label: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"{missing_label} file not found: {file_path}")

        with open(path, encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _parse_html(html_content: str) -> tuple[str, str]:
        parser = HTMLContentParser()
        parser.feed(html_content)

        return parser.title or "Untitled", parser.get_body_html()

    @staticmethod
    def _build_page_args(
        title: str,
        html_content: str,
        author: str | None = None,
        author_url: str | None = None,
    ) -> dict[str, str | None]:

        page_args = {
            "title": title,
            "html_content": html_content,
            "author_name": author or "SpyGraph",
            "author_url": author_url or None,
        }

        return page_args

    def create_grabber_page(
        self,
        content_file_path: str | None = None,
        track_url: str | None = None,
        title: str | None = None,
        author: str | None = None,
        author_url: str | None = None,
        **kwargs,
    ) -> dict:
        if content_file_path is None and track_url is None:
            passthrough_kwargs = dict(kwargs)
            if title is not None:
                passthrough_kwargs["title"] = title
            if author is not None:
                passthrough_kwargs["author_name"] = author
            if author_url is not None:
                passthrough_kwargs["author_url"] = author_url
            return super().create_page(**passthrough_kwargs)

        if not content_file_path or not track_url:
            raise ValueError("Both content_file_path and track_url are required for content-based page creation")

        file_path = Path(content_file_path)
        extension = file_path.suffix.lower()

        if extension in self.TEXT_EXTENSIONS:
            text_content = self._read_text_file(file_path, "Text")
            body_content = html.escape(text_content).replace("\n", "<br>")
            page_title = title or file_path.stem or "Untitled"
        else:
            html_content = self._read_text_file(file_path, "HTML")
            parsed_title, body_content = self._parse_html(html_content)
            page_title = title or parsed_title

        final_content = f'{body_content}\n<img src="{track_url}" />'

        page_args = self._build_page_args(page_title, final_content, author, author_url)
        page = super().create_page(**page_args)

        return {
            "url": page.get("url"),
            "path": page.get("path"),
            "views": page.get("views", 0),
            "title": page_title,
            "telegraph_domain": self.domain_graph,
            "raw_page": page,
        }

    def parse_html_file(self, html_file_path: str) -> dict:
        html_content = self._read_text_file(html_file_path, "HTML")
        title, body_content = self._parse_html(html_content)

        return {"title": title, "content": body_content, "raw_html": html_content}

    @staticmethod
    def create_graph_account(
        short_name: str,
        author_name: str | None = None,
        author_url: str | None = None,
        domain_graph: str | None = None,
    ) -> dict:
        domain = domain_graph or "telegra.ph"

        api_domain = "api.telegra.ph" if domain == "telegra.ph" else f"api.{domain}".replace("api.api.", "api.")
        api_url = f"https://{api_domain}"

        account_data = {
            "short_name": short_name,
        }
        if author_name:
            account_data["author_name"] = author_name
        if author_url:
            account_data["author_url"] = author_url

        response = requests.post(f"{api_url}/createAccount", json=account_data)

        if response.status_code != 200:
            raise Exception(f"Failed to create Telegraph account: {response.text}")

        result = response.json()

        if not result.get("ok"):
            raise Exception(f"Telegraph API error: {result.get('error', 'Unknown error')}")

        return {
            "access_token": result["result"]["access_token"],
            "auth_url": result["result"].get("auth_url"),
            "user": {
                "short_name": result["result"].get("short_name"),
                "author_name": result["result"].get("author_name"),
                "author_url": result["result"].get("author_url"),
            },
        }
