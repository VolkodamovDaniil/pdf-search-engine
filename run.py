from app import app

if __name__ == '__main__':
    print("Starting PDF Search Engine...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=False, host='0.0.0.0', port=5000)