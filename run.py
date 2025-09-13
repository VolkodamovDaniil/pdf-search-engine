from app import app

if __name__ == '__main__':
    print("Запуск поисковой системы PDF...")
    print("Откройте http://localhost:5000 в вашем браузере")
    app.run(debug=False, host='0.0.0.0', port=5000)