import requests
from environs import Env
from terminaltables import SingleTable

from settings import programming_languages


HH_SEARCH_REGION = 1
HH_SEARCH_DEPTH_DAYS = 30
HH_VACANCIES_IN_OUTPUT = 100
SJ_SEARCH_KEYWORD = ''
SJ_SEARCH_PERIOD = 30
SJ_SEARCH_REGION = 4
SJ_VACANCIES_IN_OUTPUT = 100
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

    exchange_rates = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')
    exchange_rates.raise_for_status()
    exchange_rates = exchange_rates.json()

    url = 'https://api.hh.ru/vacancies'
    payload = {
        'User-Agent': 'MyApp/1.0',
        'text': '',
        'search_field': ["name"],
        'area': HH_SEARCH_REGION,
        'period': HH_SEARCH_DEPTH_DAYS,
        'per_page': HH_VACANCIES_IN_OUTPUT,
    }
    print_table(get_average_salary_statistics_in_hh(url, payload, exchange_rates), 'HeadHunter')

    url = 'https://api.superjob.ru/2.0/oauth2/password/'
    payload = {
        'login': sj_login,
        'password': sj_password,
        'client_id': sj_client_id,
        'client_secret': sj_secret_key
    }
    response = requests.get(url, params=payload)
    response.raise_for_status()

    payload = {
        'period': SJ_SEARCH_PERIOD,
        'town': SJ_SEARCH_REGION,
        'count': SJ_VACANCIES_IN_OUTPUT
    }
    print_table(get_average_salary_statistics_in_sj(sj_secret_key, payload, exchange_rates), 'SuperJob')


def get_vacancies(url, headers, payload):
    vacancies = requests.get(url, headers=headers, params=payload)
    vacancies.raise_for_status()
    return vacancies.json()


def get_average_salary_statistics_in_sj(sj_secret_key, payload, exchange_rates):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': sj_secret_key}
    print('Загружаем вакансии из SuperJob\n по языку: ', end=" ")
    average_salary_statistics = {}
    for language in programming_languages:
        payload['keyword'] = f'Программист {language}'
        print(f'{language}', end=", ")
        page = avg_salary_sum = avg_salary_count = 0
        while True:
            payload['page'] = page
            vacancies = get_vacancies(url, headers, payload)
            if not vacancies['objects']:
                average_salary_statistics[language] = {"vacancies_found": 'Вакансии не найдены'}
                break
            for vacancy in vacancies['objects']:
                if not vacancy['payment_from'] and not vacancy['payment_to']:
                    continue
                avg_salary_sum += predict_salary_in_rubles_for_sj(vacancy, exchange_rates)
                avg_salary_count += 1
            number_of_vacancies_pages = vacancies['total'] // SJ_VACANCIES_IN_OUTPUT
            if page >= number_of_vacancies_pages-1:
                average_salary = check_division_by_zero(avg_salary_sum, avg_salary_count)
                average_salary_statistics[language] = {
                    "vacancies_found": vacancies['total'],
                    "vacancies_processed": avg_salary_count,
                    "average_salary": average_salary
                }
                break
            page += 1
    return average_salary_statistics


def get_average_salary_statistics_in_hh(url, payload, exchange_rates):
    print('Загружаем вакансии из HeadHunter\n по языку: ', end=" ")
    average_salary_statistics = {}
    for language in programming_languages:
        payload['text'] = f'Программист {language}'
        print(f'{language}', end=", ")
        page = avg_salary_sum = avg_salary_count = 0
        while True:
            payload['page'] = page
            vacancies = get_vacancies(url, '', payload)
            if not vacancies['items']:
                average_salary_statistics[language] = {"vacancies_found": 'Вакансии не найдены'}
                break
            for vacancy in vacancies['items']:
                if not vacancy['salary']:
                    continue
                avg_salary_sum += predict_salary_in_rubles_for_hh(vacancy, exchange_rates)
                avg_salary_count += 1
            if page >= vacancies['pages']-1:
                average_salary = check_division_by_zero(avg_salary_sum, avg_salary_count)
                average_salary_statistics[language] = {
                    "vacancies_found": vacancies['found'],
                    "vacancies_processed": avg_salary_count,
                    "average_salary": average_salary
                }
                break
            page += 1
    return average_salary_statistics


def check_division_by_zero(avg_salary_sum, avg_salary_count):
    try:
        average_salary = int(avg_salary_sum / avg_salary_count)
    except ZeroDivisionError:
        average_salary = 'Ошибка вычисления'
    return average_salary


def predict_salary_in_rubles_for_sj(vacancy, exchange_rates):
    salary_from = vacancy['payment_from']
    salary_to = vacancy['payment_to']
    if vacancy['currency'] != 'rub':
        exchange_rate = exchange_rates['Valute'][(vacancy['currency']).upper()]['Value']
        salary_from = vacancy['payment_from'] * exchange_rate
        salary_to = vacancy['payment_to'] * exchange_rate
    average_salary = calculate_average_salary(salary_from, salary_to)
    return average_salary


def predict_salary_in_rubles_for_hh(vacancy, exchange_rates):
    salary_from = vacancy['salary']['from'] if vacancy['salary']['from'] else 0
    salary_to = vacancy['salary']['to'] if vacancy['salary']['to'] else 0
    if vacancy['salary']['currency'] != 'RUR':
        exchange_rate = exchange_rates['Valute'][vacancy['salary']['currency']]['Value']
        if vacancy['salary']['from']:
            salary_from = vacancy['salary']['from'] * exchange_rate
        if vacancy['salary']['to']:
            salary_to = vacancy['salary']['to'] * exchange_rate
    average_salary = calculate_average_salary(salary_from, salary_to)
    if vacancy['salary']['gross']:
        average_salary *= RATIO_SALARY_WITHOUT_TAX
    return average_salary


def calculate_average_salary(salary_from, salary_to):
    if not salary_from:
        average_salary = salary_to * RATIO_MIN_SALARY
    elif not salary_to:
        average_salary = salary_from * RATIO_MAX_SALARY
    else:
        average_salary = (salary_from+salary_to)/2
    return average_salary


def print_table(salary, table_name):
    formatted_salary_block = ()
    for language, vacancies_statistic in salary.items():
        column_three = column_fourth = ''
        if 'vacancies_processed' not in vacancies_statistic:
            column_two = 'Вакансии не найдены'
        else:
            column_two, column_three, column_fourth = vacancies_statistic.values()
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
