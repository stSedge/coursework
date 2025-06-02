import telebot 
import re
import fitz

from KnowledgeGraph import KnowledgeGraph
from Model import Model

bot = telebot.TeleBot('7541038514:AAHTKmoXpdDAu_lsr2OX55nXhaEJejVbicU')
user_has_sent_doc = {}

@bot.message_handler(commands = ['start'])
def start(message):
  bot.send_message(message.chat.id, 'Hi, I can help you understand any documentation! Send me a pdf document')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    if user_has_sent_doc.get(chat_id, False):
        bot.send_message(chat_id, Model().get_answer(message.text))
    else:
        bot.send_message(chat_id, "Please send the document in pdf format first")

def extract_clean_text_from_pdf(pdf_path):
    text = ''
    with fitz.open(pdf_path) as doc:
        for page in doc:
            page_text = page.get_text()
            text += page_text + '\n'
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x20-\x7Eа-яА-ЯёЁ]', '', text)
    text = text.strip()
    return text

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = f"{message.document.file_name}"
    with open(file_path, 'wb') as f:
        f.write(downloaded_file)
    clean_text = extract_clean_text_from_pdf(file_path)
    create_kg(clean_text)
    user_has_sent_doc[message.chat.id] = True
    bot.send_message(message.chat.id, "I'm ready to answer your questions!")

def create_kg(text):
    kg = KnowledgeGraph(text)
    kg.create_knowledge_graph()


bot.polling(none_stop = True)