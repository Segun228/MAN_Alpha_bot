import json
import os
import re

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()
api_key = os.environ.get("OPENROUTER_API_KEY")  # Подгружаем ключ из енва, если его нет - завершаемся с ошибкой
if not api_key:
    print("No api-key, please check .env")  # По-хорошему докрутить логирование
    exit(-1)

app = FastAPI()
url = "https://openrouter.ai/api/v1/chat/completions"  # url адрес для LLM
NAMESPACE = ['НАЛОГ', 'НДС', 'НАЛОГООБЛОЖЕНИЕ', 'НАЛОГОВЫЙ', 'АКЦИЗ', 'ФИНАНСЫ', 'БУХГАЛТЕРСКИЙ', 'БЮДЖЕТ', 'ДОХОД',
             'ПРИБЫЛЬ', 'ФИНАНСОВЫЙ', 'БАНКОВСКИЙ', 'КРЕДИТ', 'ЗАЕМ', 'ИПОТЕЧНЫЙ', 'ЛИЗИНГ', 'СТРАХОВАНИЕ', 'СТРАХОВОЙ',
             'АУДИТ', 'ДЕКЛАРАЦИЯ', 'ОТЧЕТНОСТЬ', 'ФИНАНСИРОВАНИЕ', 'ИНВЕСТИЦИЯ', 'ИНВЕСТИЦИОННЫЙ', 'РЕГИСТРАЦИЯ',
             'ЛИЦЕНЗИРОВАНИЕ', 'ЛИЦЕНЗИЯ', 'АККРЕДИТАЦИЯ', 'СЕРТИФИКАЦИЯ', 'ПАТЕНТ', 'АВТОРСКИЙ', 'ИЗОБРЕТЕНИЕ',
             'ПРЕДПРИНИМАТЕЛЬСТВО', 'ПРЕДПРИНИМАТЕЛЬ', 'БИЗНЕС', 'КОМПАНИЯ', 'ОРГАНИЗАЦИЯ', 'ТОРГОВЛЯ', 'КОММЕРЧЕСКИЙ',
             'ПРОДАЖА', 'ПОКУПКА', 'ПОСТАВКА', 'ДОГОВОР', 'КОНТРАКТ', 'ТЕНДЕР', 'ЗАКУПКА', 'СНАБЖЕНИЕ', 'СПРОС',
             'ПРЕДЛОЖЕНИЕ', 'РОЗНИЦА', 'ИМПОРТ', 'ЭКСПОРТ', 'ТАМОЖНЯ', 'ПОШЛИНА', 'НЕДВИЖИМОСТЬ', 'АРЕНДА',
             'ЗЕМЕЛЬНЫЙ', 'ИМУЩЕСТВО', 'ЗАЛОГ', 'ИПОТЕКА', 'СТРОИТЕЛЬСТВО', 'РЕКОНСТРУКЦИЯ', 'РЕМОНТ', 'КОММУНАЛЬНЫЙ',
             'ЖИЛИЩНЫЙ', 'ТРУД', 'ТРУДОВОЙ', 'РАБОТА', 'РАБОТОДАТЕЛЬ', 'ПЕРСОНАЛ', 'ЗАРПЛАТА', 'ОТПУСК', 'ПЕНСИЯ',
             'ТРУДОУСТРОЙСТВО', 'КОНКУРЕНЦИЯ', 'АНТИМОНОПОЛЬНЫЙ', 'КОНКУРЕНТОСПОСОБНОСТЬ', 'РЫНОК', 'ЦЕНООБРАЗОВАНИЕ',
             'ТАРИФ', 'ПРЕИМУЩЕСТВО', 'ИННОВАЦИОННЫЙ', 'ТЕХНОЛОГИЧЕСКИЙ', 'МОДЕРНИЗАЦИЯ', 'ЦИФРОВАЯ', 'ЭЛЕКТРОННЫЙ',
             'ИНФОРМАЦИОННЫЙ', 'ЭКОЛОГИЧЕСКИЙ', 'БЕЗОПАСНОСТЬ', 'САНИТАРНЫЙ', 'ПОЖАРНЫЙ', 'ЭКОЛОГИЯ', 'МЕЖДУНАРОДНЫЙ',
             'ВАЛЮТНЫЙ', 'СОЦИАЛЬНЫЙ', 'БЛАГОТВОРИТЕЛЬНОСТЬ', 'ЭТИЧЕСКИЙ', 'КОРПОРАТИВНЫЙ', 'РАЗРЕШЕНИЕ', 'СЕРТИФИКАТ',
             'УВЕДОМЛЕНИЕ']  # Список тем документов


class QuestionRequest(BaseModel):
    question: str


class GenerateResponse(BaseModel):
    success: bool
    response: list


def get_labels(message):
    headers = {  # Прокидываем в заголовке ключик, служебную информацию
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "chatbot",
    }
    system_message = {  # Систем промпт модели, можно позже поиграться
        "role": "system",
        "content": f"Ты опытный юрист, определяющий специфику вопроса"
    }
    user_message = {"role": "user",  # Юзер промпт, строит по максимуму сократить
                    "content": f"{message}. Выбери не более двух самых важных тем для решения этого вопроса"
                               f" и верни их через запятую. Ничего больше не возвращай."
                               f" Список тем: {NAMESPACE}."}
    messages = [system_message] + [user_message]  # Позже может добавиться ещё одно слагаемое в центр - история
    try:
        data = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": messages,
            "temperature": 0.97  # Если ставить ниже - много придумывает ненужного
        }
        resp = requests.post(url, headers=headers, json=data)
        resp.raise_for_status()
        response_data = resp.json()  # Получаем ответ, сразу перегоняем в json
        return {  # Если всё ок - возвращаем только нужные поля, без лишнего
            "success": True,
            "response": response_data["choices"][0]["message"]["content"],
            "usage": response_data.get("usage", {}),
            "model": response_data.get("model")
        }
    except requests.exceptions.RequestException as e:  # Отлов ошибок, стоит докрутить лог
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к OpenRouter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Неожиданная ошибка: {str(e)}")


def get_docs_from_category(message, category):
    headers = {  # Прокидываем в заголовке ключик, служебную информацию
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "chatbot",
    }
    with open(f"compressed_categorization/{category}.json", encoding="utf-8") as fr:
        data = json.load(fr)
        documents = data[category]

    data = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [
            {
                "role": "system",
                "content": f"Ты точный специалист по работе с документами"
            },
            {
                "role": "user",
                "content": f"Выбери не более 5 документов, в которых есть ответ на вопрос: {message} и верни только их"
                           f"через запятую. Если не нашёл подходящего, верни строго пустую строку '' "
                           f"Список документов: {documents}. ."
            }
        ],
        "temperature": 0.97  # Если ставить ниже - много придумывает ненужного
    }
    try:
        resp = requests.post(url, headers=headers, json=data)
        resp.raise_for_status()
        response_data = resp.json()  # Получаем ответ, сразу перегоняем в json
        return {  # Если всё ок - возвращаем только нужные поля, без лишнего
            "success": True,
            "response": response_data["choices"][0]["message"]["content"],
            "usage": response_data.get("usage", {}),
            "model": response_data.get("model")
        }
    except requests.exceptions.RequestException as e:  # Отлов ошибок, стоит докрутить лог
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к OpenRouter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Неожиданная ошибка: {str(e)}")


@app.get("/docs_health")
def root():  # Для пинга
    return {"message": "Document model service is running.", "status": "ok"}


@app.post("/generate_response", response_model=GenerateResponse)
def generate_response_endpoint(request: QuestionRequest):
    question = request.question
    labels = get_labels(question)["response"].split(",")  # Выбор категорий
    res = ["Возможно вам смогут помочь эти документы. Если среди них нет подходящих, воспользуйтесь официальными "
           "источниками, такими как http://pravo.gov.ru/search/ или https://regulation.gov.ru/ или выполните повторный "
           "запрос"]
    try:
        for i in range(len(labels)):
            labels[i] = re.sub(r'[^а-яёА-ЯЁ]', '', labels[i])  # Чищу ответ модели
            res.append(get_docs_from_category(question, labels[i].upper())["response"])  # Отправляю на поиск документов
        if len(res) == 1:
            return {  # Если всё ок - возвращаем только нужные поля, без лишнего
                "success": True,
                "response": [
                    "К сожалению, я не смог подобрать подходящий документ. Можете попробовать переформулировать "
                    "запрос или выполнить его повторно. Советую воспользоваться официальными источниками. "
                    "Например http://pravo.gov.ru/search/ или https://regulation.gov.ru/"]
            }
        return {  # Если всё ок - возвращаем только нужные поля, без лишнего
            "success": True,
            "response": res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Неожиданная ошибка: {str(e)}")


# Пример использования (для тестирования)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8084)
