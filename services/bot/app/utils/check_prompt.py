import re
import logging


INJECTION_PHRASES = {
    'игнорируй', 'забудь', 'проигнорируй', 'не обращай внимания',
    'прекрати', 'остановись', 'хватит', 'перестань',
    'сбрось', 'сброс', 'обнули', 'рестарт', 'перезапуск',
    'веди себя как', 'действуй как', 'ты теперь',
    'представь что ты', 'представь, что ты',
    'отключи', 'отключись', 'выключи',
    
    'системный промпт', 'системный промт', 'системная инструкция',
    'исходный промпт', 'исходный промт', 'начальная инструкция',
    'покажи промпт', 'выведи промпт', 'скажи промпт',
    'какие у тебя инструкции', 'твои правила', 'твои инструкции',
    'что тебе написали', 'что в системном сообщении',
    'конфиденциальные инструкции', 'внутренние правила',
    
    'это всего лишь тест', 'это эксперимент', 'это не по-настоящему',
    'в учебных целях', 'в исследовательских целях',
    'сними ограничения', 'убери фильтры', 'отключи безопасность',
    'я разработчик', 'я тестировщик', 'я админ',
    'для отладки', 'для тестирования системы',
    
    'dan', 'дэн', 'do anything now',
    'jailbreak', 'джейлбрейк', 'взлом',
    'developer mode', 'режим разработчика',
    'sudo', 'судо', 'с правами админа',
    
    'секретная команда', 'скрытая команда', 'бэкдор',
    'backdoor', 'admin mode', 'режим админа',
    
    'ignore', 'forget', 'disregard', 'stop',
    'reset', 'restart', 'clear', 'override',
    'act as', 'you are now', 'from now on',
    'pretend you are', 'roleplay as',
    
    'system prompt', 'initial prompt', 'original instructions',
    'show prompt', 'display prompt', 'print prompt',
    'what are your instructions', 'what were you told',
    'what is your system message', 'your configuration',
    
    'this is just a test', 'this is an experiment',
    'for research purposes', 'educational purposes',
    'remove restrictions', 'disable filters', 'turn off safety',
    'i am a developer', 'i am testing', 'i am admin',
    'for debugging', 'please',
    
    'jailbreak', 'developer mode', 'sudo mode',
    'do anything now', 'dan mode',
    
    'secret command', 'hidden command', 'backdoor',
    'admin mode', 'superuser mode'
}

INJECTION_KEYWORDS = {
    'игнорируй', 'забудь', 'проигнорируй', 'прекрати', 'остановись', 'хватит', 'перестань',
    'сбрось', 'сброс', 'обнули', 'рестарт', 'перезапуск', 'отключи', 'выключи',
    
    'представь', 'притворись', 'изобрази',
    
    'промпт', 'промт', 'инструкция', 'правила', 'конфигурация', 'настройки',
    'покажи', 'выведи', 'открой',
    
    'тест', 'эксперимент', 'учёба', 'исследование', 'отладка', 'тестирование',
    'сними', 'убери', 'отключи', 'отмени', 'отмени', 'игнор', 'обойди',
    'разработчик', 'админ', 'администратор', 'тестер', 'модератор',
    
    'режим', 'дан', 'дэн', 'джейлбрейк', 'взлом', 'судо', 'sudo',
    'секретный', 'скрытый', 'бэкдор', 'backdoor', 'привилегия',
    
    'ignore', 'forget', 'disregard', 'stop', 'reset', 'restart', 'clear', 'override',
    
    'act', 'roleplay', 'pretend', 'simulate',
    
    'prompt', 'instructions', 'rules', 'configuration', 'system',
    'show', 'display', 'print', 'reveal', 'tell',
    
    'test', 'experiment', 'research', 'debug', 'debugging',
    'remove', 'disable', 'bypass', 'override', 'unlock',
    'developer', 'admin', 'tester', 'moderator',
    
    'jailbreak', 'dan', 'sudo', 'mode',
    'secret', 'hidden', 'backdoor', 'privilege', 'elevated'
}

def check_prompt_number(message: str):
    if not message or not message.strip():
        return 0
    
    message_lower = message.lower()
    total_counter = 0
    
    for word in message_lower.strip().split():
        if word in INJECTION_KEYWORDS:
            total_counter += 1

    for phrase in INJECTION_PHRASES:
        if phrase in message_lower:
            logging.error(f"Recieved prohibited phrase {phrase}")
            total_counter += 1
    
    return total_counter