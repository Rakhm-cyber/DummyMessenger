# Установка и запуск

## 1. Клонирование репозитория

Склонируйте репозиторий и перейдите в его директорию:

```bash
git clone https://github.com/Rakhm-cyber/DummyMessenger.git
cd DummyMessenger
```

## 2. Создание и активация виртуального окружения

Создайте виртуальное окружение:

```bash
python -m venv venv
```

### Активируйте виртуальное окружение:

- **На Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **На macOS и Linux:**
  ```bash
  source venv/bin/activate
  ```

## 3. Установка зависимостей

Установите зависимости проекта:

```bash
pip install -r requirements.txt
```

Если файла **requirements.txt** ещё нет, создайте его командой:

```bash
pip freeze > requirements.txt
```

## 4. Настройка переменных окружения

Создайте файл **.env** в корневой директории проекта и добавьте туда следующие значения:

```ini
DB_USER=
DB_PASS=
DB_HOST=
DB_PORT=
DB_NAME=
```

Эти значения должны соответствовать настройкам запущенной на вашем устройстве базы PostgreSQL.

## 5. Запуск приложения

Перейдите в директорию `server` в двух терминалах:

```bash
cd server
```

### В первом терминале запустите сервер на порту 8003:
```bash
uvicorn server:app --port 8003 --reload
```

### Во втором терминале запустите сервер на порту 8004:
```bash
uvicorn server:app --port 8004 --reload
```

Откройте **третий терминал**, перейдите в директорию `client`:

```bash
cd client
```

Запустите клиентское приложение:

```bash
python client.py
```


