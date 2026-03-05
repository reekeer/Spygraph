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
            attr_str = " ".join([f'{k}="{v}"' for k, v in attrs if v is not None])
            if attr_str:
                self.body_content.append(f"<{tag} {attr_str}>")
            else:
                self.body_content.append(f"<{tag}>")
    
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
        super().__init__(access_token=access_token)
    
    def create_page_from_html(
        self,
        html_file_path: str,
        img_src: str,
        author: str = None,
        author_url: str = None
    ) -> dict:
        file_path = Path(html_file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file_path}")
        
        with open(file_path, encoding='utf-8') as f:
            html_content = f.read()
        
        parser = HTMLContentParser()
        parser.feed(html_content)
        
        title = parser.title or "Untitled"
        body_content = parser.get_body_html()
        
        img_html = f'<img src="{img_src}" />'
        final_content = f"{body_content}\n{img_html}"
        
        page_args = {
            "title": title,
            "html_content": final_content,
        }
        
        if author:
            page_args["author_name"] = author
        if author_url:
            page_args["author_url"] = author_url
        
        page = self.create_page(**page_args)
        
        return {
            "url": page.get("url"),
            "path": page.get("path"),
            "views": page.get("views", 0),
            "title": title,
            "image_src": img_src,
            "raw_page": page
        }
    
    def parse_html_file(self, html_file_path: str) -> dict:
        file_path = Path(html_file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file_path}")
        
        with open(file_path, encoding='utf-8') as f:
            html_content = f.read()
        
        parser = HTMLContentParser()
        parser.feed(html_content)
        
        return {
            "title": parser.title or "Untitled",
            "content": parser.get_body_html(),
            "raw_html": html_content
        }
    
    def create_page_from_txt_with_image(
        self,
        txt_file_path: str,
        img_src: str,
        title: str = None,
        tracking_domain: str = None,
        author: str = None,
        author_url: str = None
    ) -> dict:
        file_path = Path(txt_file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Text file not found: {txt_file_path}")
        
        with open(file_path, encoding='utf-8') as f:
            text_content = f.read()
        
        safe_text = html.escape(text_content)
        html_content = safe_text.replace('\n', '<br>')
        
        if tracking_domain:
            tracking_img_src = f"{img_src}?domain={tracking_domain}"
        else:
            tracking_img_src = img_src
        
        img_html = f'<img src="{tracking_img_src}" />'
        final_content = f"{html_content}\n{img_html}"
        
        page_args = {
            "title": title or file_path.stem or "Untitled",
            "html_content": final_content,
        }
        
        if author:
            page_args["author_name"] = author
        if author_url:
            page_args["author_url"] = author_url
        
        page = self.create_page(**page_args)
        
        return {
            "url": page.get("url"),
            "path": page.get("path"),
            "views": page.get("views", 0),
            "title": page_args["title"],
            "image_src": img_src,
            "tracking_domain": tracking_domain,
            "telegraph_domain": self.domain_graph,
            "raw_page": page
        }
        
    @staticmethod
    def create_account(
        short_name: str,
        author_name: str = None,
        author_url: str = None,
        domain_graph: str = None
    ) -> dict:
        domain = domain_graph or "telegra.ph"
        
        if domain == "telegra.ph":
            api_domain = "api.telegra.ph"
        else:
            api_domain = f"api.{domain}".replace("api.api.", "api.")
        
        api_url = f"https://{api_domain}"
        
        account_data = {
            "short_name": short_name,
        }
        if author_name:
            account_data["author_name"] = author_name
        if author_url:
            account_data["author_url"] = author_url
        
        response = requests.post(
            f"{api_url}/createAccount",
            json=account_data
        )
        
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
            }
        }
    
    def create_page_from_html_with_domain(
        self,
        html_file_path: str,
        img_src: str,
        tracking_domain: str = None,
        title: str = None,
        author: str = None,
        author_url: str = None
    ) -> dict:
        file_path = Path(html_file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file_path}")
        
        with open(file_path, encoding='utf-8') as f:
            html_content = f.read()
        
        parser = HTMLContentParser()
        parser.feed(html_content)
        
        page_title = title or parser.title or "Untitled"
        body_content = parser.get_body_html()
        
        if tracking_domain:
            tracking_img_src = f"{img_src}?domain={tracking_domain}"
        else:
            tracking_img_src = img_src
        
        img_html = f'<img src="{tracking_img_src}" />'
        final_content = f"{body_content}\n{img_html}"
        
        page_args = {
            "title": page_title,
            "html_content": final_content,
        }
        
        if author:
            page_args["author_name"] = author
        if author_url:
            page_args["author_url"] = author_url
        
        page = self.create_page(**page_args)
        
        return {
            "url": page.get("url"),
            "path": page.get("path"),
            "views": page.get("views", 0),
            "title": page_title,
            "image_src": img_src,
            "tracking_domain": tracking_domain,
            "telegraph_domain": self.domain_graph,
            "raw_page": page
        }
        