import requests
# import json
from environs import Env

from settings import programming_languages


def main():
    env = Env()
    env.read_env()
    sj_secret_key = env('SJ_SECRET_KEY')
    sj_login = env('SJ_LOGIN')
    sj_password = env('SJ_PASSWORD')

    # код для HH - временно отключен
    # url = 'https://api.hh.ru/vacancies'
    # payload = {
    #     'User-Agent': 'MyApp/1.0',
    #     'text': 'Python',
    #     'search_field': ["name"],  # , "description" надо поиграться с поиском по конкретным полям, ищет где попало
    #     'area': 1,
    #     'period': 30,
    #     'per_page': 100,
    # }
    # print(json.dumps((get_hh_all_lang_average_salary(url, payload)), indent=4, ensure_ascii=False))
    # код для HH - временно отключен

    # авторизация по паролю от личного кабинета - почта, ключник...
    url = 'https://api.superjob.ru/2.0/oauth2/password/'
    headers = {}
    payload = {
        'login': sj_login,
        'password': sj_password,
        'client_id': 2170,
        'client_secret': sj_secret_key,
        'hr': 0
    }
    response = make_sj_request(url, headers, payload)
    print(response.json())

    # sj_access_token = response.json()['access_token']

    payload = {
        'keyword': 'Программист',
        # 'keywords': (1, 'and', 'Программист'),
        'period': 0,  # за всё время
        'town': 4,  # для Москвы
        'count': 100
    }

    sj_vacancies = get_sj_vacancies(sj_secret_key, payload).json()
    for vacancy in sj_vacancies['objects']:
        print(f"{vacancy['profession']}, {vacancy['payment_from']}, {vacancy['town']['title']},"
              f"{vacancy['payment_to']}, {vacancy['currency']}")
    print(f"Вскго: {sj_vacancies['total']}")

    # print(json.dumps(sj_vacancies, indent=4, ensure_ascii=False))


def get_sj_vacancies(sj_secret_key, payload):
    url = '	https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': sj_secret_key}
    response = make_sj_request(url, headers, payload)
    print(response.url.title())
    return response


def make_sj_request(url, headers, payload=None):
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    return response


def get_hh_all_lang_average_salary(url, payload):
    language_count_salary = {}
    for language in programming_languages:
        payload['text'] = language
        # print(language)
        vacancies = get_hh_vacancies(url, payload).json()
        avg_salary_sum = avg_salary_count = 0
        # print(vacancies['pages'])
        for page in range(vacancies['pages']):
            payload['page'] = page
            vacancies = get_hh_vacancies(url, payload).json()
            # print(json.dumps(vacancies, indent=4, sort_keys=True, ensure_ascii=False))
            for vacancy in vacancies['items']:
                if vacancy['salary']:
                    avg_salary_sum += predict_hh_rub_salary(vacancy)
                    avg_salary_count += 1
        language_count_salary[language] = {
            "vacancies_found": vacancies['found'],
            "vacancies_processed": avg_salary_count,
            "average_salary": int(avg_salary_sum/avg_salary_count)
        }
    return language_count_salary


def predict_hh_rub_salary(vacancy):
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
    if vacancy['salary']['gross']:
        avg_salary *= 0.87
    return avg_salary  # , vacancy['salary']['from'], vacancy['salary']['to']


def get_hh_first_language_vacansies(url, payload):
    languages_info = {}
    for language in programming_languages:
        payload['text'] = language
        vacancies = get_hh_vacancies(url, payload)
        some_language_vacancies = vacancies.json()
        languages_info[language] = some_language_vacancies['found']
    return languages_info


def get_hh_vacancies(url, payload):
    vacancies = requests.get(url, params=payload)
    vacancies.raise_for_status()
    return vacancies


if __name__ == '__main__':
    main()
