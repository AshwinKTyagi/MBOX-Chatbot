"""
mailbox keys:
['Delivered-To', 'Received', 'X-Google-Smtp-Source', 'X-Received', 'ARC-Seal', 'ARC-Message-Signature', 'ARC-Authentication-Results', 'Return-Path',
'Received', 'Received-SPF', 'Authentication-Results', 'DKIM-Signature', 'DKIM-Signature', 'From', 'Reply-To', 'To', 'Subject', 'MIME-Version', 'Content-Type', 
'Content-Transfer-Encoding', 'Message-ID', 'Date', 'Feedback-ID', 'X-SES-Outgoing']
"""
import os
from dotenv import load_dotenv
from datetime import datetime
import mailbox
import re
from langchain_community.embeddings.openai import OpenAIEmbeddings

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Path to your mbox file
mbox_file = 'INBOX.mbox/mbox'

# Open the mbox file
mbox = mailbox.mbox(mbox_file)


def print_message(idx = int):
    # for item in mbox[idx]:
    #     print(f"{item}: {mbox[idx][item]}")  

    print()
    if mbox[idx].is_multipart():
        print("Multipart\n")
        for part in mbox[idx].walk():
            if part.get_content_type() == 'text/plain':
                print(part.get_payload())
    else:
        print("Not multipart\n")
        print(mbox[idx].get_payload(decode=True).decode(mbox[idx].get_content_charset(), errors='replace'))
        print()
        
        message = str(mbox[idx].get_payload(decode=True).decode(mbox[idx].get_content_charset(), errors='replace'))
        
        # Remove HTML tags
        clean_message = re.sub(r'<[^>]+>', '\t', message)
        print(clean_message)        
        
def get_message(idx = int):
    """
        Get the message from the mbox file
    """
    message = ''
    if mbox[idx].is_multipart():
        for part in mbox[idx].walk():
            if part.get_content_type() == 'text/plain':
                message +=  part.get_payload() + '\n'
                
        
    else:
        message = mbox[idx].get_payload(decode=True).decode(mbox[idx].get_content_charset(), errors='replace')        

    clean_message = re.sub(r'<[^>]+>', ' ', message)    
    return clean_message

    
    
"""
    Check if a message is from a subscribing list by checking if list-unsubscribe is in the message
    when analyzing the mbox file, we dont want to analyze these messages bc they arent specifically for the users
"""
def count_subscribing_list():
    count = 0
    for i in range(100):
        if 'list-unsubscribe' in mbox[i]:
            count += 1
        
    return count


"""
    Create vector embedding for the message
"""
def create_vector_embedding(idx = int):
    start_time = datetime.now()
    
    embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    
    # Get the message from the mbox file
    message = get_message(idx)
    
    # Use OpenAI API to create vector embedding
    vector = embedding_model.embed_documents([message])
    
    end_time = datetime.now()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time.total_seconds()}s")
    return vector



