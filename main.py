import requests
from environs import Env
from terminaltables import SingleTable

from settings import programming_languages


EXCHANGE_RATE = 70
HH_SEARCH_REGION = 1
HH_SEARCH_DEPTH_DAYS = 30
HH_ITEMS_IN_OUTPUT = 100
SJ_SEARCH_KEYWORD = ''
SJ_SEARCH_PERIOD = 30
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
    print_table(get_average_salary_statistics_in_hh(url, payload), 'HeadHunter')

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
        'keyword': '',
        'period': SJ_SEARCH_PERIOD,
        'town': SJ_SEARCH_REGION,
        'count': SJ_ITEMS_IN_OUTPUT
    }
    print_table(get_average_salary_statistics_in_sj(sj_secret_key, payload), 'SuperJob')


def get_sj_vacancies(sj_secret_key, payload):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': sj_secret_key}
    vacancies = requests.get(url, headers=headers, params=payload)
    vacancies.raise_for_status()
    return vacancies.json()


def get_hh_vacancies(url, payload):
    vacancies = requests.get(url, params=payload)
    vacancies.raise_for_status()
    return vacancies.json()


def get_average_salary_statistics_in_sj(sj_secret_key, payload):
    print('Загружаем вакансии из SuperJob\n по языку: ', end=" ")
    average_salary_statistics = {}
    for language in programming_languages:
        payload['keyword'] = language
        print(f'{language}', end=", ")
        vacancies = get_sj_vacancies(sj_secret_key, payload)
        if vacancies['objects']:
            avg_salary_sum = avg_salary_count = 0
            vacancies_pages = vacancies['total'] // SJ_ITEMS_IN_OUTPUT
            for page in range(vacancies_pages+1):
                payload['page'] = page
                vacancies = get_sj_vacancies(sj_secret_key, payload)
                for vacancy in vacancies['objects']:
                    if vacancy['payment_from'] or vacancy['payment_to']:
                        avg_salary_sum += predict_rub_salary_for_sj(vacancy)
                        avg_salary_count += 1
            average_salary_statistics[language] = {
                "vacancies_found": vacancies['total'],
                "vacancies_processed": avg_salary_count,
                "average_salary": int(avg_salary_sum/avg_salary_count)
            }
        else:
            average_salary_statistics[language] = {"vacancies_found": 'Вакансии не найдены'}
    return average_salary_statistics


def get_average_salary_statistics_in_hh(url, payload):
    print('Загружаем вакансии из HeadHunter\n по языку: ', end=" ")
    average_salary_statistics = {}
    for language in programming_languages:
        payload['text'] = language
        print(f'{language}', end=", ")
        vacancies = get_hh_vacancies(url, payload)
        if vacancies['items']:
            avg_salary_sum = avg_salary_count = 0
            for page in range(vacancies['pages']):
                payload['page'] = page
                vacancies = get_hh_vacancies(url, payload)
                for vacancy in vacancies['items']:
                    if vacancy['salary']:
                        avg_salary_sum += predict_rub_salary_for_hh(vacancy)
                        avg_salary_count += 1
            average_salary_statistics[language] = {
                "vacancies_found": vacancies['found'],
                "vacancies_processed": avg_salary_count,
                "average_salary": int(avg_salary_sum/avg_salary_count)
            }
        else:
            average_salary_statistics[language] = {"vacancies_found": 'Вакансии не найдены'}
    return average_salary_statistics


def predict_rub_salary_for_sj(vacancy):
    salary_from = vacancy['payment_from']
    salary_to = vacancy['payment_to']
    if vacancy['currency'] != 'rub':
        salary_from = vacancy['payment_from'] * EXCHANGE_RATE
        salary_to = vacancy['payment_to'] * EXCHANGE_RATE
    average_salary = calculating_the_average_salary(salary_from, salary_to)
    return average_salary


def predict_rub_salary_for_hh(vacancy):
    salary_from = vacancy['salary']['from'] if vacancy['salary']['from'] else 0
    salary_to = vacancy['salary']['to'] if vacancy['salary']['to'] else 0
    if vacancy['salary']['currency'] != 'RUR':
        if vacancy['salary']['from']:
            salary_from = vacancy['salary']['from'] * EXCHANGE_RATE
        if vacancy['salary']['to']:
            salary_to = vacancy['salary']['to'] * EXCHANGE_RATE
    average_salary = calculating_the_average_salary(salary_from, salary_to)
    if vacancy['salary']['gross']:
        average_salary *= RATIO_SALARY_WITHOUT_TAX
    return average_salary


def calculating_the_average_salary(salary_from, salary_to):
    if not salary_from:
        average_salary = salary_to * RATIO_MIN_SALARY
    elif not salary_to:
        average_salary = salary_from * RATIO_MAX_SALARY
    else:
        average_salary = (salary_from+salary_to)/2
    return average_salary


def print_table(salary, table_name):
    formatted_salary_block = ()
    for language, vacancies_items in salary.items():
        column_three = column_fourth = ''
        if 'vacancies_processed' not in vacancies_items:
            column_two = 'Вакансии не найдены'
        else:
            column_two, column_three, column_fourth = vacancies_items.values()
        formatted_salary_block += ((language, column_two, column_three, column_fourth),)
    columns_names = (('Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'),)
    columns_names += formatted_salary_block
    table_instance = SingleTable(columns_names, table_name)
    for column_number in range(4):
        table_instance.justify_columns[column_number] = 'center'
    print()
    print(table_instance.table)
    print()


if __name__ == '__main__':
    main()
