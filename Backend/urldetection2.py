import pandas as pd
import numpy as np
from tld import get_tld
from urllib.parse import urlparse
import re
import joblib 
import sys
import json
import requests

from groq import Groq

# Load the pre-trained model
with open('RF_malaciousURL.pkl', 'rb') as RF_spamURL_classifier:
    model = joblib.load("RF_malaciousURL.pkl")

# Function to process input URL into features
def process_input(url):
    df = {'url': [url]}
    data = pd.DataFrame(df, columns=['url', 'url_len', 'https', 'http', 'tld', 'tld_len', 'hostname_len', '@', '?', '-', '=', '.', '#', '%', '+', '$', '!', '*', ',', '//', 'digits', 'letters', 'short_url', 'ip_address'])
    data['url_len'] = data['url'].apply(lambda x: len(str(x)))
    data['https'] = data['url'].apply(lambda i: i.count('https'))
    data['http'] = data['url'].str.replace('https', '').apply(lambda i: i.count('http'))
    data['tld'] = data['url'].apply(lambda i: get_tld(i, fail_silently=True))
    
    def tld_length(tld):
        try:
            return len(tld)
        except:
            return 0
            
    data['tld_len'] = data['tld'].apply(lambda i: tld_length(i))
    data['hostname_len'] = data['url'].apply(lambda i: len(urlparse(i).netloc))
    
    features = ['@', '?', '-', '=', '.', '#', '%', '+', '$', '!', '*', ',', '//']
    data = data.drop(["tld"], axis=1)
    for feature in features:
        data[feature] = data['url'].apply(lambda i: i.count(feature))
    
    data['digits'] = data['url'].apply(lambda i: sum(c.isdigit() for c in i))
    data['letters'] = data['url'].apply(lambda i: sum(c.isalpha() for c in i))
    
    short_url_patterns = re.compile(r'bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|'
                                    r'yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|'
                                    r'short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|'
                                    r'doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|'
                                    r'db\.tt|qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|'
                                    r'q\.gs|is\.gd|po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|'
                                    r'x\.co|prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|'
                                    r'tr\.im|link\.zip\.net')

    data['short_url'] = data['url'].apply(lambda x: 1 if re.search(short_url_patterns, x) else 0)
    
    ip_address_patterns = re.compile(
        r'(([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\\/?)|'
        r'((0x[0-9a-fA-F]{1,2})\.(0x[0-9a-fA-F]{1,2})\.(0x[0-9a-fA-F]{1,2})\.(0x[0-9a-fA-F]{1,2})\\/?)|'
        r'([0-9]+(?:\.[0-9]+){3}:[0-9]+)|'
        r'(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}|'
        r'([0-9]+(?:\.[0-9]+){3}:[0-9]+)|'
        r'([0-9]+(?:\.[0-9]+){3}(?:\/\d{1,2})?)'
    )
    
    data['ip_address'] = data['url'].apply(lambda x: 1 if re.search(ip_address_patterns, x) else 0)
    data = data.drop(['url'], axis=1)
    
    return data


# Main URL classification function
def classify_url(url):
    data = process_input(url)
    pred = model.predict(data)
    pre=model.predict_proba(data)
    try: 
        if pre[0][0]<=0.25:
            pred_llm = fetch_llm_classification(url)
            return pred_llm
        else:
            return pred
    except:
        return pred

# Function to fetch LLM classification
def fetch_llm_classification(url):
    client = Groq(api_key="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")
    
    def process_message_chunk(chunk):
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Answer in Yes or No if the given message looks legitimate or not. You will be given a chunk of a webpage, based on the wordings you must return a one word answer Yes or No regarding whether the webpage is a malicious website or not. Content is: {chunk}. Content ends here. Reply only in one word."
                }
            ], model="llama3-70b-8192",
        )
        response = chat_completion.choices[0].message.content.strip().lower()
        return 1 if 'yes'in response.lower() else 0

    aggregated_results = []
    
    def process_large_input(input_text, chunk_size=512):
        chunks = [input_text[i:i+chunk_size] for i in range(0, len(input_text), chunk_size)]
        for chunk in chunks:
            result = process_message_chunk(chunk)
            aggregated_results.append(result)
    
    input_text = scrape_webpage(url)
    if input_text:
        process_large_input(input_text)
        avg_confidence = sum(aggregated_results) / len(aggregated_results) if aggregated_results else 0
        return avg_confidence
    else:
        return None
    
def scrape_webpage(url):
    response = requests.get(url)
    if response.status_code == 200:
        text = response.text
        text = re.sub(r'style="[^"]*"', '', text, flags=re.DOTALL)  # Remove inline CSS
        text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)  # Remove embedded CSS
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)  # Remove JavaScript
        text = re.sub(r'<[^>]*>', '', text)  # Remove HTML tags
        text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespaces with a single space
        return text.strip()
    else:
        print("Failed to fetch the webpage:", response.status_code)
        return None
    
def feedback_message_chunk(chunk):
    # Placeholder for the actual API call to process a single chunk
    # This should be replaced with the actual API call logic
    
    client = Groq(api_key="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")
    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Answer in Yes or No if the given message looks legitimate or not. You will be given a chunk of a webpage, based on the wordings you must return a one word answer Yes or No regarding whether the webpage is a malicious website or not. Content is "+chunk+" content ends here. Reply only in one word."
        }
    ], model="llama3-70b-8192",
    )
    response = chat_completion.choices[0].message.content.strip().lower()
    
    if not 'yes' in response.lower():
        # If the response is yes, return a detailed explanation
        explanation = "Explain why this chunk is flagged as malicious. Content is "+chunk+" content ends here."
        explanation_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": explanation
                }
            ], model="llama3-70b-8192",
        )
        explanation_text = explanation_completion.choices[0].message.content
        return (1, explanation_text)
    else:
        # If the response is no, return a summary
        summary = "Summarize this chunk. Content is "+chunk+" content ends here."
        summary_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": summary
                }
            ], model="llama3-70b-8192",
        )
        summary_text = summary_completion.choices[0].message.content
        return (0, summary_text)
    
def feedback_large_input(input_text, chunk_size=512):
    # Split the input text into chunks
    chunks = [input_text[i:i+chunk_size] for i in range(0, len(input_text), chunk_size)]
    # Process each chunk and aggregate the results
    aggregated_results = []
    for chunk in chunks:
        result = feedback_message_chunk(chunk)
        # Convert 'Yes'/'No' to binary (1/0) and add confidence score
        aggregated_results.append((result))  
    analysis = analyze_feedback_chunks(aggregated_results)
    return analysis

def analyze_feedback_chunks(results):
    total_score = sum(result[0] for result in results)
    average_score = total_score / len(results)
    client = Groq(api_key="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")
    if average_score < 0.7:
        # If the average score is above 0.7, return a detailed summary
        summaries = [result[1] for result in results if result[0] == 0]
        detailed_summary = "Detailed Summary:\n" + "\n".join(summaries)
        details = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Here is all the chunks data together explaining the summary of each chunk.Do not present any information which is not directly inferred from the text Generate an overall summary based on the same.  Ensure that you provide thorogh insights for abput "+str(len(results)*50)+" words"+detailed_summary

                }
            ], model="mixtral-8x7b-32768",
        )
        summary_text = details.choices[0].message.content
        small = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Here is all the chunks data together explaining the summary of each chunk.Do not present any information which is not directly inferred from the text Generate an overall summary based on the same. Limit your response to 150 characters"+detailed_summary

                }
            ], model="mixtral-8x7b-32768",
        )
        mini = small.choices[0].message.content
        return summary_text, mini
    else:
        # If the average score is 0.7 or below, return a detailed analysis
        analyses = [result[1] for result in results if result[0] == 1]
        detailed_analysis = "Detailed Analysis of Malicious Content:\n" + "\n".join(analyses)
        details = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Here is all the chunks data together explaining why each chunk is flagged as malicious. Generate an overall summary based on the same and provide examples from the webpage. Do not present any information which is not directly inferred from the text. Ensure that you provide thorough insights for abput "+str(len(results)*50)+" words"+detailed_analysis

                }
            ], model="mixtral-8x7b-32768",
        )
        summary_text = details.choices[0].message.content
        small = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Here is all the chunks data together explaining why each chunk is flagged as malicious. Generate an overall summary based on the same and provide examples from the webpage. Do not present any information which is not directly inferred from the text Limit the response to 150 characters"+detailed_analysis

                }
            ], model="mixtral-8x7b-32768",
        )
        mini = small.choices[0].message.content
        return summary_text,mini


url = sys.argv[1] if len(sys.argv) > 1 else 'https://66515fd1887786d466eb10aa--phenomenal-griffin-74186c.netlify.app/'
input_text = scrape_webpage(url)
if input_text:
    avg_confidence ,mini= feedback_large_input(input_text)
    with open("outputfeedback.txt",'w') as f:
        f.write(url)
        f.write(avg_confidence)
        f.write(mini)

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else ''
    result = classify_url(url)
    res=result.tolist() if hasattr(result,'tolist') else result
    print(json.dumps(res))
