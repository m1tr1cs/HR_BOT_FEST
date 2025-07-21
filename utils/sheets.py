import json
import logging
from datetime import datetime
from gspread import authorize
from oauth2client.service_account import ServiceAccountCredentials


VACANCIES_SHEET_ID = "1_yR6ROVpWwphP2TZLLydov_TF1JB6x9AnLJGkSflCOk"
CANDIDATES_SHEET_ID = "1rAsVrzZWlAFTifn-r7Hjq5pZZWsd_Bp_VmBR3tdWOWc"
VACANCIES_CACHE_FILE = "vacancies.json"


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = authorize(creds)

def load_vacancies_from_sheet():
    try:
        sheet = client.open_by_key(VACANCIES_SHEET_ID).sheet1
        records = sheet.get_all_records()
        data = [dict(record, vacancy_id=i + 2) for i, record in enumerate(records)]
        with open(VACANCIES_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"✅ Вакансії оновлено: {len(data)} записів")
        return data
    except Exception:
        logging.exception("❌ Помилка завантаження вакансій з Google Sheets")
        return []

def get_vacancies():
    try:
        with open(VACANCIES_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return load_vacancies_from_sheet()

def save_candidate(name, phone, age, chat_id, vacancy_details):
    try:
        sheet = client.open_by_key(CANDIDATES_SHEET_ID).sheet1
        chat_ids = sheet.col_values(6)
        repeat_note = ""
        if str(chat_id) in chat_ids:
            repeat_note = " (повторне звернення)"

        job_description = f"{vacancy_details.get('position')} - {vacancy_details.get('market')} ({vacancy_details.get('location')})"
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sheet.append_row([name + repeat_note, age, job_description, phone, date, str(chat_id)])
        logging.info(f"📝 Збережено кандидата: {name} на вакансію: {job_description}")
    except Exception:
        logging.exception("❌ Помилка при збереженні кандидата")
