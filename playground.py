"""
mailbox keys:
['Delivered-To', 'Received', 'X-Google-Smtp-Source', 'X-Received', 'ARC-Seal', 'ARC-Message-Signature', 'ARC-Authentication-Results', 'Return-Path',
'Received', 'Received-SPF', 'Authentication-Results', 'DKIM-Signature', 'DKIM-Signature', 'From', 'Reply-To', 'To', 'Subject', 'MIME-Version', 'Content-Type', 
'Content-Transfer-Encoding', 'Message-ID', 'Date', 'Feedback-ID', 'X-SES-Outgoing']
"""

import mailbox

# Path to your mbox file
mbox_file = 'INBOX.mbox/mbox'

# Open the mbox file
mbox = mailbox.mbox(mbox_file)

# Iterate through the messages in the mbox file
i = 0


def print_message(idx = int):
    for item in mbox[idx]:
        print(f"{item}: {mbox[idx][item]}")  

    print()
    if mbox[idx].is_multipart():
        for part in mbox[idx].walk():
            if part.get_content_type() == 'text/plain':
                print(part.get_payload())
    else:
        print(mbox[idx].get_payload(decode=True).decode(mbox[idx].get_content_charset(), errors='replace'))
    print()
    
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

print(count_subscribing_list())


