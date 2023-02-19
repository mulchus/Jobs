import requests
from environs import Env
from terminaltables import SingleTable

from settings import programming_languages


EXCHANGE_RATE = 70
HH_SEARCH_REGION = 1
HH_SEARCH_DEPTH_DAYS = 30
HH_ITEMS_IN_OUTPUT = 100
SJ_SEARCH_CATALOGUE = 48
SJ_SEARCH_KEYWORD = ''
SJ_SEARCH_PERIOD = 30  # 1 — 24 часа, 3 — 3 дня, 7 — неделя, 0 — за все время
SJ_SEARCH_REGION = 4
SJ_ITEMS_IN_OUTPUT = 100
RATIO_MIN_SALARY = 0.8
RATIO_MAX_SALARY = 1.2
RATIO_SALARY_WITHOUT_TAX = 0.87


def main():
    env = Env()
    env.read_env()
    sj_secret_key = env('SJ_SECRET_KEY')
    sj_login = env('SJ_LOGIN')
    sj_password = env('SJ_PASSWORD')
    sj_client_id = env('SJ_CLIENT_ID')
    programming_languages.reverse()

    url = 'https://api.hh.ru/vacancies'
    payload = {
        'User-Agent': 'MyApp/1.0',
        'text': '',
        'search_field': ["name"],
        'area': HH_SEARCH_REGION,
        'period': HH_SEARCH_DEPTH_DAYS,
        'per_page': HH_ITEMS_IN_OUTPUT,
    }
    hh_salary = (get_for_all_languages_average_salary_hh(url, payload))
    print_table(hh_salary, 'HeadHunter')

    url = 'https://api.superjob.ru/2.0/oauth2/password/'
    headers = {}
    payload = {
        'login': sj_login,
        'password': sj_password,
        'client_id': sj_client_id,
        'client_secret': sj_secret_key
    }
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()

    payload = {
        'catalogues': SJ_SEARCH_CATALOGUE,
        'keyword': '',
        'period': SJ_SEARCH_PERIOD,
        'town': SJ_SEARCH_REGION,
        'count': SJ_ITEMS_IN_OUTPUT
    }
    sj_salary = (get_for_all_languages_average_salary_sj(sj_secret_key, payload))
    print_table(sj_salary, 'SuperJob')


def predict_rub_salary_for_sj(vacancy):
    salary_from = vacancy['payment_from']
    salary_to = vacancy['payment_to']
    if vacancy['currency'] != 'rub':
        if vacancy['currency'] == 'usd':
            salary_from = vacancy['payment_from'] * EXCHANGE_RATE
            salary_to = vacancy['payment_to'] * EXCHANGE_RATE
    if not salary_from:
        avg_salary = salary_to * RATIO_MIN_SALARY
    elif not salary_to:
        avg_salary = salary_from * RATIO_MAX_SALARY
    else:
        avg_salary = (salary_from+salary_to)/2
    return avg_salary


def get_sj_vacancies(sj_secret_key, payload):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': sj_secret_key}
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    return response


def get_hh_vacancies(url, payload):
    vacancies = requests.get(url, params=payload)
    vacancies.raise_for_status()
    return vacancies


def get_for_all_languages_average_salary_sj(sj_secret_key, payload):
    print('Загружаем вакансии из SuperJob\n по языку: ', end=" ")
    array_of_languages_average_salary = {}
    for language in programming_languages:
        payload['keyword'] = language
        print(f'{language}', end=", ")
        vacancies = get_sj_vacancies(sj_secret_key, payload).json()
        if vacancies['objects']:
            avg_salary_sum = avg_salary_count = 0
            vacancies_pages = vacancies['total'] // SJ_ITEMS_IN_OUTPUT
            for page in range(vacancies_pages+1):
                payload['page'] = page
                vacancies = get_sj_vacancies(sj_secret_key, payload).json()
                for vacancy in vacancies['objects']:
                    if vacancy['payment_from'] or vacancy['payment_to']:
                        avg_salary_sum += predict_rub_salary_for_sj(vacancy)
                        avg_salary_count += 1
            array_of_languages_average_salary[language] = {
                "vacancies_found": vacancies['total'],
                "vacancies_processed": avg_salary_count,
                "average_salary": int(avg_salary_sum/avg_salary_count)
            }
        else:
            array_of_languages_average_salary[language] = {"vacancies_found": 'Вакансии не найдены'}
    return array_of_languages_average_salary


def get_for_all_languages_average_salary_hh(url, payload):
    print('Загружаем вакансии из HeadHunter\n по языку: ', end=" ")
    array_of_languages_average_salary = {}
    for language in programming_languages:
        payload['text'] = language
        print(f'{language}', end=", ")
        vacancies = get_hh_vacancies(url, payload).json()
        if vacancies['items']:
            avg_salary_sum = avg_salary_count = 0
            for page in range(vacancies['pages']):
                payload['page'] = page
                vacancies = get_hh_vacancies(url, payload).json()
                for vacancy in vacancies['items']:
                    if vacancy['salary']:
                        avg_salary_sum += predict_rub_salary_for_hh(vacancy)
                        avg_salary_count += 1
            array_of_languages_average_salary[language] = {
                "vacancies_found": vacancies['found'],
                "vacancies_processed": avg_salary_count,
                "average_salary": int(avg_salary_sum/avg_salary_count)
            }
        else:
            array_of_languages_average_salary[language] = {"vacancies_found": 'Вакансии не найдены'}
    return array_of_languages_average_salary


def predict_rub_salary_for_hh(vacancy):
    salary_from = vacancy['salary']['from'] if vacancy['salary']['from'] else 0
    salary_to = vacancy['salary']['to'] if vacancy['salary']['to'] else 0
    if vacancy['salary']['currency'] != 'RUR':
        if vacancy['salary']['currency'] == 'USD':
            if vacancy['salary']['from']:
                salary_from = vacancy['salary']['from'] * EXCHANGE_RATE
            if vacancy['salary']['to']:
                salary_to = vacancy['salary']['to'] * EXCHANGE_RATE
    if not salary_from:
        avg_salary = salary_to * RATIO_MIN_SALARY
    elif not salary_to:
        avg_salary = salary_from * RATIO_MAX_SALARY
    else:
        avg_salary = (salary_from+salary_to)/2
    if vacancy['salary']['gross']:
        avg_salary *= RATIO_SALARY_WITHOUT_TAX
    return avg_salary


def print_table(salary, table_name):
    formatted_salary_block = ()
    for language, vacancies_items in salary.items():
        b = c = ''
        if 'vacancies_processed' not in vacancies_items:
            a = 'Вакансии не найдены'
        else:
            a, b, c = vacancies_items.values()
        formatted_salary_block += ((language, a, b, c),)
    table_data = (('Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'), )
    table_data += formatted_salary_block
    table_instance = SingleTable(table_data, table_name)
    for i in range(4):
        table_instance.justify_columns[i] = 'center'
    print()
    print(table_instance.table)
    print()


if __name__ == '__main__':
    main()
