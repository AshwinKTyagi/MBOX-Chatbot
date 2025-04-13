import hashlib
import os
from dotenv import load_dotenv
from datetime import datetime
import mailbox
from email.utils import parsedate_to_datetime
import re
from fastembed import TextEmbedding

# Path to your mbox file
mbox_file = '../INBOX.mbox/mbox'
mbox = mailbox.mbox(mbox_file)

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def get_mbox_count():
    return len(mbox)

"""

    Prepare Email for insertion into the vector database
    - Extract metadata
    - Clean message body
    - Create vector embedding

"""
def get_message(idx = int):
    message = ''
    if mbox[idx].is_multipart():
        for part in mbox[idx].walk():
            if part.get_content_type() == 'text/plain':
                message +=  part.get_payload() + '\n'        
    else:
        payload = mbox[idx].get_payload(decode=True)
        if payload:
            message = payload.decode(mbox[idx].get_content_charset() or 'utf-8', errors='replace')

    clean_message = re.sub(r'<[^>]+>', ' ', message)    
    return str(clean_message)

def clean_addr(addr = str):
    if not addr:
        return []
    return [a.strip() for a in addr.split(',')]

def extract_metadata(idx = int):
    message = mbox[idx]
    data = get_message(idx)
    if not data:
        return None, None   
    
    date_obj = message.get('Date')
    try:
        date = datetime.fromisoformat(date_obj).isoformat()
    except:
        date = None
    
    subject = message.get('Subject', '(No Subject)')
    thread_id = re.sub(r'^(re|fw|fwd):\s*', '', subject.strip(), flags=re.IGNORECASE)
    thread_id = hashlib.md5(thread_id.encode()).hexdigest()
    
    metadata = {
        "subject": subject,
        "from": message.get('From'),
        "to": ", ".join(clean_addr(message.get('To'))),
        "cc": ", ".join(clean_addr(message.get('Cc'))),
        "date": date,
        "thread_id": thread_id,
        "is_reply": subject.lower().startswith(('re:', 'fw:', 'fwd:')),
        "has_link": 'http' in data.lower(),
        "n_tokens": len(data.split()),
        "attachments": bool(message.get_content_maintype() != 'text')
    }
    return metadata, data


"""
    Create Vector Embeddings
    
    
"""
def create_vector_embedding(idx = int):
    # start_time = datetime.now()
    
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en", cache_dir="./cache")

    message = get_message(idx)
    
    embedding_generator = embedding_model.embed(message)
    embedding = list(embedding_generator)
    vector = embedding[0]
    
    # end_time = datetime.now()
    # elapsed_time = end_time - start_time
    # print(f"Elapsed time: {elapsed_time.total_seconds()}s")
    return vector.tolist()

def create_vector_embedding(data = str):
    # start_time = datetime.now()
    
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en", cache_dir="./cache")

    embedding_generator = embedding_model.embed(data)
    embedding = list(embedding_generator)
    vector = embedding[0]
    
    # end_time = datetime.now()
    # elapsed_time = end_time - start_time
    # print(f"Elapsed time: {elapsed_time.total_seconds()}s")
    return vector.tolist()



