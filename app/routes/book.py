from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from app import mail
from flask_mail import Message
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import os

from . import book_search_bp

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def clean_book_name(book_name):
    book_name = re.sub(r'\d+', '', book_name)
    book_name = book_name.replace(',', '').strip()
    return book_name

def clean_pages(pages):
    return re.sub(r'\D', '', pages)

def get_book_cover_image(detail_page_url):
    response = requests.get(detail_page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    img_tag = soup.find('img')
    if img_tag:
        return img_tag['src']
    return None

def search_book(query):
    search_url = f"http://libgen.is/search.php?req={query}&open=0&res=25&view=simple&phrase=1&column=def"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    table = soup.find('table', {'class': 'c'})
    if not table:
        return None
    
    rows = table.find_all('tr')[1:]
    books = []
    for row in rows:
        cols = row.find_all('td')
        title = cols[2].get_text().strip()
        author = cols[1].get_text().strip()
        publisher = cols[3].get_text().strip()
        year = cols[4].get_text().strip()
        pages = clean_pages(cols[5].get_text().strip())
        language = cols[6].get_text().strip()
        size = cols[7].get_text().strip()
        extension = cols[8].get_text().strip()
        if extension.lower() == 'pdf':
            detail_page_url = "http://libgen.is/" + cols[2].find('a')['href']
            download_page_url = cols[9].find('a')['href']
            cover_image_url = get_book_cover_image(detail_page_url)
            book_details = {
                'title': title,
                'clean_title': clean_book_name(title),
                'author': author,
                'publisher': publisher,
                'year': year,
                'pages': pages,
                'language': language,
                'size': size,
                'cover_image_url': "http://libgen.is/" + cover_image_url if cover_image_url else None,
                'download_page_url': download_page_url
            }
            books.append(book_details)
    return books

def download_book(book_name, download_page_url):
    response = requests.get(download_page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    download_div = soup.find('div', {'id': 'download'})
    if not download_div:
        return None
    
    h2_tag = download_div.find('h2')
    if not h2_tag:
        return None
    
    download_link = h2_tag.find('a')['href']
    
    book_response = requests.get(download_link, stream=True)
    total_size = int(book_response.headers.get('content-length', 0))
    
    book_name = clean_book_name(book_name)
    book_title = f"{book_name}.pdf"
    book_path = os.path.join(DOWNLOAD_DIR, book_title)
    
    with open(book_path, 'wb') as file, tqdm(
        desc=book_title,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in book_response.iter_content(chunk_size=1024):
            file.write(data)
            bar.update(len(data))
    
    return book_path

def send_email(book_path, recipient_email):
    sender_email = os.getenv('EMAIL_USER')
    
    msg = Message("Downloaded Book",
                  sender=sender_email,
                  recipients=[recipient_email])
    
    msg.body = "Please find the attached book you downloaded."
    
    with open(book_path, "rb") as attachment:
        msg.attach(os.path.basename(book_path), "application/pdf", attachment.read())
    
    mail.send(msg)

@book_search_bp.route('/search', methods=['POST', 'GET'])
@jwt_required()
def search():
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        query = data.get('query')
    else:
        query = request.args.get('query')
        
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    books = search_book(query)
    if not books:
        return jsonify({"error": "No PDF books found."}), 404
    
    return jsonify({"books": books}), 200

@book_search_bp.route('/download', methods=['POST'])
@jwt_required()
def download():
    data = request.json
    if not data or 'title' not in data or 'url' not in data or 'email' not in data:
        return jsonify({"error": "Title, URL, and email are required"}), 400
    
    book_title = data['title']
    download_page_url = data['url']
    recipient_email = data['email']
    
    book_file = download_book(book_title, download_page_url)
    if not book_file:
        return jsonify({"error": "Failed to download the book"}), 500
    
    send_email(book_file, recipient_email)
    
    return send_file(book_file, as_attachment=True)