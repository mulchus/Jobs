In english | [По-русски](../README.md)

# Jobs

The project is designed to search for programmer vacancies in Moscow among the main 10 programming languages 
on the HeadHunter and SuperJob services.
The list of programming languages is set in the file settings.py.

### How to install?

Python3 should already be installed.
Then use pip (or pip3, there is a conflict with Python2) to install dependencies.
Open the command line with the Win+R keys and enter:
```
pip install -r requirements.txt
```
It is recommended to use virtualenv/venv to isolate the project.
(https://docs.python.org/3/library/venv.html)


### Setting environment variables

Before starting, you need to create a ".env" file in the PATH_TO_THE_FOLDER_WITH_SCRIPT\
and configure the environment variables by writing the following in it.
Authorization is carried out by the login password of the user registered on the site.
```
SJ_SECRET_KEY=SuperJob secret key, as specified here: https://api.superjob.ru/
SJ_ID=ID of the application registered in the API, as specified here: https://api.superjob.ru/
SJ_LOGIN=Superjob user login
SJ_PASSWORD=Superjob User Password
```


### The command to run the script:
```
python PATH_TO_THE_FOLDER_WITH_SCRIPT\main.py
```
If you have installed a virtual environment, then the command can be entered without the path to the script.


### Project Goals
This code was written for educational purposes as part of an online course for web developers at [dvmn.org]
(https://dvmn.org/).
