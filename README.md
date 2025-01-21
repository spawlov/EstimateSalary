# Узнай будущую зарплату

### Собираем статистику с сайтов [SuperJob](https://www.superjob.ru/) и [HeadHunter](https://hh.ru) по заданным профессиям

![CaptureImage](img/capture.png)

## Как установить и запустить

[Установите Python](https://www.python.org/), если этого ещё не сделали.

***Важно! Библиотека Python Telegram Bot не работает под Python 3.12. Гарантировано работает на версии Python 3.10.15***

Проверьте, что `python` установлен и корректно настроен. Запустите его в командной строке:
```sh
python --version
```
**Версия Python должна быть не ниже 3.10** 

Возможно, вместо команды `python` здесь и в остальных инструкциях этого README придётся использовать `python3`. 

- Склонируйте репозиторий:
```shell
git clone https://github.com/spawlov/EstimateSalary.git
```

- Установите зависимости и активируйте виртуальное окружение, для этого запустите последовательно команды:
```shell
poetry install
poetry shell
```
