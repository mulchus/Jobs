import requests
from datetime import datetime


def main():
    url = 'https://api.hh.ru/vacancies'
    payload = {
        'text': 'программист',
        'search_fields': 'name',
        'area': 1,
        'published_at': datetime.strptime('2023-02-01', '%Y-%m-%d'),
        'per_page': '10',
        'page': '2'
    }
    print(payload['published_at'])
    vacancies = requests.get(url, params=payload)
    vacancies.raise_for_status()
    print(vacancies.json())

if __name__ == '__main__':
    main()