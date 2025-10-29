from create_bot import bot, TOKEN
import requests
import pandas as pd
import pdfkit
import os


from app.Converter import convert_docx_to_pdf,convert_pptx_to_pdf, convert_image_to_pdf

DOCUMENTS_DIR = 'Documents'
PHOTOS_DIR = 'Photos'

PDF_FILE = "File.pdf"
DOCX_FILE = "File.docx"
XLSX_FILE = "File.xlsx"
PPTX_FILE = "File.pptx"
TXT_FILE = "File.txt"

JPG_FILE = "File.jpg"

document_route = ""
photo_route = ""

async def UploadDocumentFile(file_id, message):
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    file_extension = message.document.file_name.split('.')[-1]
    print(file_extension)
    download_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'
    print(download_url)
    res = requests.get(download_url)

    if res.status_code == 200:
        # ==============================IF FILE FORMAT IS ============== PDF ======================================
        if file_extension == 'pdf':
            file_path = os.path.join(DOCUMENTS_DIR, PDF_FILE)
            with open(file_path, 'wb') as file:
                file.write(res.content)
                print("File downloaded")
                global document_route
                document_route = file_path
            return document_route
        # ==============================IF FILE FORMAT IS ============== DOCX ======================================
        elif file_extension == 'docx':
            file_path = os.path.join(DOCUMENTS_DIR, DOCX_FILE)
            with open(file_path, 'wb') as file:
                file.write(res.content)
                print("File downloaded")
                # route = os.path.abspath('File.docx')  #/home/temur/PycharmProjects/StreetPrint/Documents
                convert_docx_to_pdf(file_path, '/home/temur/PycharmProjects/StreetPrint/Documents')
                document_route = "/home/temur/PycharmProjects/StreetPrint/Documents/File.pdf"
            return document_route
        # ==============================IF FILE FORMAT IS ============== TXT ======================================
        elif file_extension == 'txt':
            file_path = os.path.join(DOCUMENTS_DIR, TXT_FILE)
            with open(file_path, 'wb') as file:
                file.write(res.content)
                print("File downloaded")
                document_route = file_path
                print(document_route)
            return document_route
        # ==============================IF FILE FORMAT IS ============== XLSX ======================================
        elif file_extension == 'xlsx':
            file_path = os.path.join(DOCUMENTS_DIR, XLSX_FILE)
            with open(file_path, 'wb') as file:
                file.write(res.content)
                print("File downloaded")
                # route = os.path.abspath('File.xlsx')
                # print(route)
                df = pd.read_excel(file_path)
                html = df.to_html()
                pdfkit.from_string(html, '/home/temur/PycharmProjects/StreetPrint/Documents/File.pdf')
                document_route = '/home/temur/PycharmProjects/StreetPrint/Documents/File.pdf'
            return document_route
        # ==============================IF FILE FORMAT IS ============== PPTX ======================================
        elif file_extension == 'pptx':
            file_path = os.path.join(DOCUMENTS_DIR, PPTX_FILE)
            with open(file_path, 'wb') as file:
                file.write(res.content)
                print("File downloaded")
                # route = os.path.abspath('File.pptx')
                # print(route)
                convert_pptx_to_pdf(file_path, '/home/temur/PycharmProjects/StreetPrint/Documents/File.pdf')
                document_route = "/home/temur/PycharmProjects/StreetPrint/Documents/File.pdf"
            return document_route
        else:
            return 0
    else:
        return None


async def UploadPhoto(file_id, message):
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    file_extension = file_path.split('.')[-1]
    print(file_path)
    print(file_extension)
    download_file = await bot.download_file(file_path)
    download_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'
    print(download_file)
    res = requests.get(download_url)
    if res.status_code == 200:
        if file_extension == "jpg" or file_extension == "png":
            file_path = os.path.join(PHOTOS_DIR, JPG_FILE)
            with open(file_path, 'wb') as file:
                file.write(res.content)
                print("File downloaded")
                global photo_route
            photo_route = "/home/temur/PycharmProjects/StreetPrint/Photos/File.jpg"
            print(photo_route)
            return photo_route
        else:
            return 0
    else:
        return None