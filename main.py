import requests
# import numpy as np

from settings import programming_languages


def main():
    url = 'https://api.hh.ru/vacancies'
    payload = {
        # 'User-Agent' : 'MyApp/1.0',
        'text': 'Python',
        'search_fields': 'name',
        'area': 1,
        'period': 30,
    }

    # print(get_first_language_vacansies(url, payload))  # сумма вакансий по каждому из 10-ти первых языкав

    language = 'Python'  # сумма вакансий по языку и зарплаты (первые 20 вакансий)
    vacancies = get_some_language_salary(language, url, payload).json()
    for vacancy in vacancies['items']:
        if vacancy['salary']:
            print(f"{vacancy['name']}, {predict_rub_salary(vacancy)} RUR")
        else:
            print(f"{vacancy['name']}, SALARY IS NOT SPECIFIED")

        # print(f"{vacancy['name']}, {salary_from}, {salary_to}, 'RUR(from {vacancy['salary']['currency']})'")
        # print(f"{vacancy['name']}, {vacancy['salary']['from']}, {vacancy['salary']['to']}
        # {vacancy['salary']['currency']}")

        # if vacancy['salary']:
        #     print(f"{vacancy['name']}, {vacancy['salary']['from']}, {vacancy['salary']['to']}"
        #           f"{vacancy['salary']['currency']}")


def predict_rub_salary(vacancy):
    exchange_rate = 70
    salary_from = vacancy['salary']['from'] if vacancy['salary']['from'] else 0
    salary_to = vacancy['salary']['to'] if vacancy['salary']['to'] else 0
    if vacancy['salary']['currency'] != 'RUR':
        if vacancy['salary']['currency'] == 'USD':
            if vacancy['salary']['from']:
                salary_from = vacancy['salary']['from'] * exchange_rate
            if vacancy['salary']['to']:
                salary_to = vacancy['salary']['to'] * exchange_rate
    if not salary_from:
        avg_salary = salary_to * 0.8
    elif not salary_to:
        avg_salary = salary_from * 1.2
    else:
        avg_salary = (salary_from+salary_to)/2

    return avg_salary  # , vacancy['salary']['from'], vacancy['salary']['to']


def get_some_language_salary(language, url, payload):
    payload['text'] = language
    vacancies = get_vacancies(url, payload)
    return vacancies


def get_first_language_vacansies(url, payload):
    languages_info = {}
    for language in programming_languages:
        payload['text'] = language
        vacancies = get_vacancies(url, payload)
        some_language_vacancies = vacancies.json()
        languages_info[language] = some_language_vacancies['found']
    return languages_info


def get_vacancies(url, payload):
    vacancies = requests.get(url, params=payload)
    vacancies.raise_for_status()
    return vacancies


if __name__ == '__main__':
    main()
