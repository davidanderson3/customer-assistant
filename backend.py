from flask import Flask, request, jsonify, render_template
import os
from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.callbacks import get_openai_callback
import pandas as pd
import json
from flask_cors import CORS
from json.decoder import JSONDecodeError

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('customer_assistant.html')

# Initialize AzureChatOpenAI
llm = AzureChatOpenAI(deployment_name=os.environ.get("MODEL", "default-model"),
                      temperature=0,
                      api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "default-version"), 
                      api_key=os.environ.get("AZURE_API_KEY"),
                      azure_endpoint=os.environ.get("AZURE_ENDPOINT")
                      )

@app.route('/get_instructions', methods=['GET'])
def get_instructions():
    try:
        with open('instructions.txt', 'r') as file:
            instructions = file.read()
        return jsonify({'status': 'success', 'instructions': instructions})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    
@app.route('/saveCategories', methods=['POST'])
def save_categories():
    data = request.json
    categories = data.get('categories', [])
    
    # Load existing categories
    try:
        with open('categories.json', 'r') as file:
            existing_categories_data = json.load(file)
            existing_categories = existing_categories_data.get('categories', [])
    except (FileNotFoundError, JSONDecodeError):
        existing_categories = []

    # Create KB files for new categories
    for category in categories:
        if category not in existing_categories:
            create_kb_file_for_category(category)

    # Save updated categories list
    with open('categories.json', 'w') as file:
        json.dump(data, file, indent=4)
    return jsonify({"message": "Categories updated successfully"}), 200

def create_kb_file_for_category(category):
    filename = f"{category.lower()}_kb.txt"
    if not os.path.exists(filename):  # Check if file already exists
        with open(filename, 'w') as file:
            file.write("")  # Create an empty file


# Add a route to fetch categories
@app.route('/getCategories', methods=['GET'])
def get_categories():
    try:
        with open('categories.json', 'r') as file:
            data = json.load(file)
            return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({"categories": []}), 200

@app.route('/save_feedback', methods=['POST'])
def save_feedback():
    try:
        data = request.json
        print("Received data:", data)

        filename = 'feedback.json'
        print("Current Working Directory:", os.getcwd())

        feedback_data = []
        try:
            with open(filename, 'r') as file:
                try:
                    feedback_data = json.load(file)
                except JSONDecodeError:
                    print("JSONDecodeError: The file is empty or contains invalid JSON. Starting with an empty list.")
                    feedback_data = []
        except FileNotFoundError:
            print(f"File {filename} not found. A new file will be created.")

        feedback_data.append(data)

        with open(filename, 'w') as file:
            json.dump(feedback_data, file, indent=4)
        print("Data written to file successfully.")

        return {'status': 'success'}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'status': 'error', 'message': str(e)}

@app.route('/predict_category', methods=['POST'])
def predict_category():
    input_data = request.json
    input_text = input_data.get('text', '')
    existing_categories = input_data.get('categories', [])

    # Check if input data is complete
    if not input_text or not existing_categories:
        return jsonify({'status': 'error', 'message': 'Missing required data'}), 400

    try:
        categories_str = ', '.join(existing_categories)
        prompt = f"Given the list of categories [{categories_str}], predict the most relevant category or categories for this inquiry: {input_text}"

        llm_response = llm.invoke(prompt)
        response_text = llm_response.content  # Extract the response content

        # Assuming the LLM response needs to be parsed for categories
        # Insert your parsing logic here, for now, let's assume it returns a list
        # If your LLM returns a list of categories as a string, you'll need to parse it
        try:
            predicted_categories = json.loads(response_text)
        except json.JSONDecodeError:
            # Handle cases where the response is not in JSON format
            predicted_categories = [response_text]  # or some other parsing logic

        return jsonify({'categories': predicted_categories})

    except Exception as e:
        print(f"An error occurred: {e}")  # Debugging log
        return jsonify({'status': 'error', 'message': str(e)}), 500

    # Fallback return statement in case none of the above returns are executed
    return jsonify({'status': 'error', 'message': 'Unexpected error occurred'}), 500


@app.route('/get_kb_content', methods=['GET'])
def get_kb_content():
    category = request.args.get('category')
    filename = f"{category.lower()}_kb.txt"  # e.g., 'umls_kb.txt' or 'drugs_kb.txt'

    try:
        with open(filename, 'r') as file:
            content = file.read()
        return jsonify({'status': 'success', 'content': content})
    except FileNotFoundError:
        return jsonify({'status': 'success', 'content': ''})  # Return empty content if file not found
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


    
@app.route('/save_kb_entry', methods=['POST'])
def save_kb_entry():
    data = request.json
    category = data['category']
    entry = data['entry']

    filename = f"{category.lower()}_kb.txt"  # e.g., 'umls_kb.txt' or 'drugs_kb.txt'

    try:
        with open(filename, 'w') as file:  # Open file in write mode
            file.write(entry)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/save_instructions', methods=['POST'])
def save_instructions():
    try:
        instructions = request.json.get('instructions', '')
        print("Received instructions: ", instructions)  # Debug print

        # Specify the correct path where the server has write permissions
        with open('instructions.txt', 'w') as file:
            file.write(instructions)

        print("Instructions saved.")  # Debug print
        return jsonify({'status': 'success'})
    except Exception as e:
        print("Error: ", str(e))  # Debug print
        return jsonify({'status': 'error', 'message': str(e)})
    
@app.route('/save_category_and_kb', methods=['POST'])
def save_category_and_kb():
    try:
        data = request.json
        oldCategoryName = data['oldCategoryName']
        newCategoryName = data['newCategoryName']
        kbContent = data['kbContent']

        # Update the category name in your categories data
        # You'll need to implement the logic to update the category name
        # and ensure that the corresponding knowledge base file is also updated

        # Example: Rename the file
        old_filename = f"{oldCategoryName.lower()}_kb.txt"
        new_filename = f"{newCategoryName.lower()}_kb.txt"
        os.rename(old_filename, new_filename)

        # Save the updated content to the new file
        with open(new_filename, 'w') as file:
            file.write(kbContent)

        return jsonify({'status': 'success'})
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/run_code', methods=['POST'])
def run_code():
    input_data = request.json
    input_text = input_data.get('code', '')

    try:
        llm_response = llm.invoke(f"{input_text}")
        # Replace the following line with the correct way to access the response content
        result = llm_response.content  # or whatever the correct attribute is
        temperature_used = llm.temperature
    except Exception as e:
        result = f"Error: {str(e)}"

    return jsonify({'result': result})


if __name__ == '__main__':
    app.run(debug=True)
