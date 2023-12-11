import os
from os.path import join, dirname
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    jsonify
)
from pymongo import MongoClient
import requests
from datetime import datetime 
from bson import ObjectId

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

connection_string = os.environ.get("MONGODB_URl")
db_name = os.environ.get("DB_NAME")

client = MongoClient(connection_string)
db = client[db_name]
app = Flask(__name__)

@app.route('/')
def main():
    word_result = db.words.find({}, {'_id': False})
    words = []
    for word in word_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    return render_template('index.html', words=words)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = "cc8619ac-32aa-4f22-af56-f8c43cee4217"
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        return redirect(url_for(
            'error',
            word=f'"{keyword}"'
        ))
    
    if type(definitions[0]) is str:
        suggestions = ', '.join(definitions)
        return redirect(url_for(
            'error',
            word=keyword,
            suggs=suggestions
        ))


    status = request.args.get('status_give', 'new')
    return render_template(
        'detail.html',
        word=keyword,
        definitions=definitions,
        status=status
    )

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')

    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was saved!!!',
    })


@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
    'result': 'success',
    'msg': f'the word {word} was deleted'
    })

@app.route('/error')
def error():
    word_error = request.args.get('word')
    suggestions = request.args.get('suggs')
    suggs = suggestions.split(', ')
    return render_template('error.html', word=word_error, suggs=suggs)

@app.route("/api/get_exs", methods=["GET"])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'example':example.get('example'),
            'id':str(example.get('_id')),
        })
    return jsonify({
        'result':'success',
        'examples': examples
      })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word': word,
        'example': example,
    }
    db.examples.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'Your example, {example}, for the word, {word}, was the saved!'
        })


@app.route("/api/delete_ex", methods=["POST"])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg': f'Your word, {word} was deleted!'    
    })

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True, port=5000)