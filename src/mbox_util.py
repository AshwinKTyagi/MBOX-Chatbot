import hashlib
import os
from dotenv import load_dotenv
from datetime import datetime
from dateutil import parser
import mailbox
import re
from fastembed import TextEmbedding
from bs4 import BeautifulSoup


# Path to your mbox file
mbox_file = '../INBOX.mbox/mbox'
mbox = mailbox.mbox(mbox_file)

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en", cache_dir="./cache")

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


def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    
    for tag in soup(["script", "style"]):
        tag.decompose()
    
    text = soup.get_text(separator="\n")
    clean_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    return clean_text


def get_message(idx = int):
    message = ''
    email_obj = mbox[idx]
    
    if email_obj.is_multipart():
        for part in email_obj.walk():
            ct = part.get_content_type()
            if ct == 'text/plain':
                try:
                    message += part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace') + '\n'
                except Exception:
                    pass    
                    
        if not message:
            for part in email_obj.walk():
                if part.get_content_type() == 'text/html':
                    html_payload = part.get_payload(decode=True)
                    if html_payload:
                        html_str = html_payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                        message = clean_html(html_str)
                        break
    else:
        payload = email_obj.get_payload(decode=True)
        if payload:
            message = payload.decode(email_obj.get_content_charset() or 'utf-8', errors='replace')
 
    return str(message)

def clean_addr(addr = str):
    if not addr:
        return []
    return [a.strip() for a in addr.split(',')]

def extract_metadata(idx = int):
    message = mbox[idx]
    data = get_message(idx)
    if not data:
        return None, None   
    
    date_obj = str(message.get('Date'))
    dt = parser.parse(date_obj)
    date = dt.isoformat()

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
def create_vector_embedding_from_idx(idx = int):
    # start_time = datetime.now()
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

    embedding_generator = embedding_model.embed(data)
    embedding = list(embedding_generator)
    vector = embedding[0]
    
    # end_time = datetime.now()
    # elapsed_time = end_time - start_time
    # print(f"Elapsed time: {elapsed_time.total_seconds()}s")
    return vector.tolist()


if __name__ == "__main__":
    while True:
        print("\nMenu:")
        print("1. Get total number of emails")
        print("2. Extract metadata from an email")
        print("3. Get raw email message")
        print("4. Create vector embedding for an email")
        print("5. Exit")
        
        choice = input("Enter your choice: ")
        
        match choice:
            case "1":
                print(f"Total number of emails: {get_mbox_count()}")
            case "2":
                idx = int(input("Enter email index: "))
                metadata, data = extract_metadata(idx)
                if metadata:
                    print("Metadata:")
                    for key, value in metadata.items():
                        print(f"{key}: {value}")
                else:
                    print("No metadata found for the given index.")
            case "3":
                idx = int(input("Enter email index: "))
                print(get_message(idx))
            case "4":
                idx = int(input("Enter email index: "))
                vector = create_vector_embedding_from_idx(idx)
                print(f"Vector embedding: {vector}")
            case "5":
                print("Exiting...")
                break
            case _:
                print("Invalid choice. Please try again.")
