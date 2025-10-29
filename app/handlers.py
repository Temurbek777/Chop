from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
import keyboards as kb
from create_bot import TOKEN, bot
from docx2pdf import convert
from Converter import convert_docx_to_pdf,convert_pptx_to_pdf,convert_image_to_pdf
from utils import UploadDocumentFile, UploadPhoto
import pandas as pd
import pdfkit
import requests
import cups
import os


DOCUMENTS_DIR = 'Documents'
PHOTOS_DIR = 'Photos'

PDF_FILE = "File.pdf"
DOCX_FILE = "File.docx"
XLSX_FILE = "File.xlsx"
PPTX_FILE = "File.pptx"
TXT_FILE = "File.txt"

JPG_FILE = "File.jpg"

PRINT_FILE_ROUTE = ""

#----------------------------CREATING CONNECTION FROM CUPS--------------------------------#
conn = cups.Connection()
printers = conn.getPrinters()
form_router = Router()
options = {}
printer_name = list(printers.keys())[0]
print(printer_name)


#-------------------------------------------------------------------------------------------#


#---------------------------------CREATING CLASS FSM-----------------------------------------#
class Form(StatesGroup):
    language = State()
    command = State()
    file = State()
    copy = State()
    orientation = State()
    pages = State()
    page_per_sheet = State()
#--------------------------------------------------------------------------------------------#


#------------------------------------START COMMAND-------------------------------------------#
@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.language)
    await message.answer(text='Tilni tanlang\nВыберите язык\nChoose the language',
                         reply_markup=kb.langs
                         )
#----------------------------------------------------------------------------------------------


#----------------------------------LANGUAGE PROCESS--------------------------------------
@form_router.message(F.text, Form.language)
async def process_language(message: Message, state: FSMContext) -> None:
    await state.update_data(lang=message.text)
    await state.set_state(Form.command)
    data = await state.get_data()
    if data['lang'] == "UZB":
        await message.answer("Tanlang",
                             reply_markup=kb.chop_uz
                             )
    elif data['lang'] == "RU":
        await message.answer("Выберите команду",
                             reply_markup=kb.chop_rus
                             )
    elif data['lang'] == "ENG":
        await message.answer("Choose the command",
                             reply_markup=kb.chop_en
                             )
#---------------------------------------------------------------------------------------


#--------------------------------------------PRINT START(ENG)-----------------------------
@form_router.message(Command("print"))
async def command_print(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.file)
    await state.update_data(command=message.text)
    await message.answer(
        "Send file",
        reply_markup=ReplyKeyboardRemove(),
    )
#------------------------------------------------------------------------------------


#------------------------------CHOP(UZB)--------------------------------------------------
@form_router.message(Command("Chop_qilish"))
async def command_print(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.file)
    await state.update_data(command=message.text)
    await message.answer(
        "Faylni yuboring (.pdf, .docx, .xlsx, .pptx, .jpg, .png)",
        reply_markup=ReplyKeyboardRemove(),
    )
#-----------------------------------------------------------------------------------------


#-----------------------------ПЕЧАТАТЬ(RUS)----------------------------------------------------
@form_router.message(Command("печатать"))
async def command_print(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.file)
    await state.update_data(command=message.text)
    await message.answer(
        "Выберите файл",
        reply_markup=ReplyKeyboardRemove(),
    )
#-------------------------------------------------------------------------------------------


#--------------------------------DOCUMENT PROCESS------------------------------------------
@form_router.message(F.document | F.photo, Form.file)
async def process_file(message: Message, state: FSMContext) -> None:
    if message.document:
        await state.update_data(file=message.document.file_name)
        await message.reply("Iltmos kuting!")
        file_id = message.document.file_id
        global PRINT_FILE_ROUTE
        PRINT_FILE_ROUTE = await UploadDocumentFile(file_id, message)
        print(PRINT_FILE_ROUTE)
        if PRINT_FILE_ROUTE == 0:
            await message.answer(
                f"Bu fayl kengaytmasi qo'llab quvvatlanmaydi!\nIltmos quyidagi ketgaymali fayl yuboring yoki faylingizni quyidagi kengaytmaga o'tqazing\n.pdf, .docx, .xlsx, .pptx, .jpg, .png"
            )
        elif PRINT_FILE_ROUTE is None:
            await message.answer(
                f"Faylni yuklashda xato\nIltmos quyidagi kengaytmali fayl yuboring yoki faylingizni quyidagi kengaytmaga o'tqazing\n.pdf, .docx, .xlsx, .pptx, .jpg, .png"
            )
        else:
            await state.set_state(Form.copy)
            data = await state.get_data()
            if data['lang'] == 'UZB':
                await message.answer(
                    f"Nusxalar sonini kiriting"
                )
            elif data['lang'] == 'RU':
                await message.answer(
                    f"Введите количество копий"
                )
            elif data['lang'] == 'ENG':
                await message.answer(
                    f"Enter the copy number"
                )

        #  print(route)
#=============================IF THE FILE PHOTO===============================================
    elif message.photo:
        await state.update_data(file=message.photo[-1].file_id)

        file_id = message.photo[-1].file_id
        photo_file_route = await UploadPhoto(file_id, message)

        if photo_file_route == 0:
            await message.answer(
                f"Bu fayl kengaytmasi qo'llab quvvatlanmaydi!\nIltmos quyidagi ketgaymali fayl yuboring yoki faylingizni quyidagi kengaytmaga o'tqazing\n.pdf, .docx, .xlsx, .pptx, .jpg, .png"
            )
        elif photo_file_route is None:
            await message.answer(
                f"Faylni yuklashda xato\nIltmos quyidagi kengaytmali fayl yuboring yoki faylingizni quyidagi kengaytmaga o'tqazing\n.pdf, .docx, .xlsx, .pptx, .jpg, .png"
            )
        else:
            PRINT_FILE_ROUTE = convert_image_to_pdf(photo_file_route)
            print(PRINT_FILE_ROUTE)
            await state.set_state(Form.copy)
            data = await state.get_data()
            if data['lang'] == 'UZB':
                await message.answer(
                    f"Nusxalar sonini kiriting"
                )
            elif data['lang'] == 'RU':
                await message.answer(
                    f"Введите количество копий"
                )
            elif data['lang'] == 'ENG':
                await message.answer(
                    f"Enter the copy number"
                )




#-----------------------------------------------------------------------------------------------


#---------------------------------------COPIES PROCESS------------------------------------------
@form_router.message(F.text, Form.copy)
async def process_copy(message: Message, state: FSMContext) -> None:
    await state.update_data(copies=message.text)
    await state.set_state(Form.orientation)
    data = await state.get_data()
    if data['lang'] == 'UZB':
        await message.answer(f"Tanlang:", reply_markup=kb.orient_uzb
                             )
    if data['lang'] == 'RU':
        await message.answer("Выберите: ", reply_markup=kb.orient_rus
                             )

    if data['lang'] == 'ENG':
        await message.answer("Choose: ", reply_markup=kb.orient_en
                             )
#------------------------------------------------------------------------------------------


#---------------------------ORIENTATION PROCESS---------------------------------------------------
@form_router.message(F.text, Form.orientation)
async def process_orientation(message: Message, state: FSMContext) -> None:
    # await state.update_data(orienation=message.text)
    if message.text == '/Portret' or message.text == '/Портрет':
        await state.update_data(orientation=3)
    else:
        await state.update_data(orientation=4)
    await state.set_state(Form.pages)
    data = await state.get_data()

    if data['lang'] == 'UZB':
        await message.answer(
            "Betlarni tanlang",
            reply_markup=ReplyKeyboardRemove()
        )
    elif data['lang'] == 'RU':
        await message.answer(
            "Выберите страниц",
            reply_markup=ReplyKeyboardRemove()
        )
    elif data['lang'] == 'ENG':
        await message.answer(
            "Choose pages",
            reply_markup=ReplyKeyboardRemove()
        )
#-------------------------------------------------------------------------------------------------


#----------------------------------------PAGES PROCESS--------------------------------------------
@form_router.message(F.text, Form.pages)
async def process_pages(message: Message, state: FSMContext) -> None:
    await state.update_data(page_ranges=message.text)
    await state.set_state(Form.page_per_sheet)
    data = await state.get_data()
    if data['lang'] == 'UZB':
        await message.answer("Betdagi varoqlar sonini kiriting", reply_markup=ReplyKeyboardRemove()
                             )
    elif data['lang'] == 'RU':
        await message.answer("Страниц в одном листе", reply_markup=ReplyKeyboardRemove()
                             )
    elif data['lang'] == 'ENG':
        await message.answer("Pages per sheet", reply_markup=ReplyKeyboardRemove()
                             )
#--------------------------------------------------------------------------------------------------


#---------------------------------------PAGE_PER_SHEET PROCESS-------------------------------------
@form_router.message(F.text, Form.page_per_sheet)
async def process_pages(message: Message, state: FSMContext) -> None:
    await state.update_data(pages_per_sheet=message.text)
    data = await state.get_data()
    #await state.clear()
    if data['lang'] == 'UZB':
        await message.answer(
            f"Tekshiring:\nFayl: {data['file']},\nNusxa soni: {data['copies']},\nBetlar: {data['page_ranges']},\nBir betdagi varoqlar soni: {data['pages_per_sheet']}",
            reply_markup=kb.final_chop_uz
        )
    elif data['lang'] == 'RU':
        await message.answer(
            f"Проверьте:\nФайл: {data['file']},\nЧисло копий: {data['copies']},\nСтраницы: {data['page_ranges']},\nЧисло страниц на одном листе: {data['pages_per_sheet']}",
            reply_markup=kb.final_chop_rus
        )
    elif data['lang'] == 'ENG':
        await message.answer(
            f"Check settings:\nFile: {data['file']},\nCopy: {data['copies']},\nPages: {data['page_ranges']},\nPages per sheet: {data['pages_per_sheet']}",
            reply_markup=kb.final_chop_en
        )

    data['orientation-requested'] = data['orientation']
    data['page-ranges'] = data['page_ranges']
    data['number-up'] = data['pages_per_sheet']

    del data['orientation'], data['page_ranges'], data['pages_per_sheet']

    print(data)
    options['copies'] = data['copies']
    options['media'] = 'A4'
    options['orientation-requested'] = str(data['orientation-requested'])
    options['page-ranges'] = data['page-ranges']
    options['number-up'] = data['number-up']
    print(options)
    print(PRINT_FILE_ROUTE)
    await state.clear()
#-------------------------------------------------------------------------------------------------


#----------------------------------CHOP QILISH-----------------------------------------------------
@form_router.message(Command('Chop'))
async def final_print(message: Message) -> None:
    await message.answer(
        f"Iltmos kuting",
        reply_markup=ReplyKeyboardRemove(),
    )
    #print(route)
    job_id = conn.printFile(printer_name, PRINT_FILE_ROUTE, "Test Print", options=options)
    print(job_id)
#--------------------------------------------------------------------------------------------------