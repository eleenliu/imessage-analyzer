"""
This project imports iMessage data from the MacBook archive from 2015-present;
calculates volume totals, % of messages from sender and receiver, and topic modelling.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import seaborn as sns

def style():
    sns.set()
    sns.set_palette('husl',10)

def load_contacts():
    # username = input("Input your username: ")
    # conn = sqlite3.connect('/Users/', username, '/Library/Application Support/AddressBook/AddressBook-v22.abcddb')

    conn = sqlite3.connect('/Users/Eleen/Library/Application Support/AddressBook/AddressBook-v22.abcddb')
    contacts_query = "SELECT DISTINCT ZFIRSTNAME || ' ' || ZLASTNAME AS FULLNAME, ZFULLNUMBER FROM ZABCDPHONENUMBER " \
                     "LEFT JOIN ZABCDRECORD ON ZABCDRECORD.Z_PK = ZABCDPHONENUMBER.ZOWNER"
    contacts = pd.read_sql_query(contacts_query, conn)

    for count in range(0,len(contacts['ZFULLNUMBER'])):
        contacts['ZFULLNUMBER'][count] = contacts['ZFULLNUMBER'][count].replace(" ", "").replace(" ","").replace("(", "").replace(")", "").replace("-","")
        string = contacts['ZFULLNUMBER'][count]
        if string[:1] != "+":
            contacts['ZFULLNUMBER'][count] = "+1" + contacts['ZFULLNUMBER'][count]
    return contacts


def get_df():    # creates data frame from local iMessage database
    # username = input("Input your username: ")
    # conn = sqlite3.connect('/Users/', username, '/Library/Messages/chat.db')

    conn = sqlite3.connect('/Users/Eleen/Library/Messages/chat.db')
    message_query = " SELECT *, datetime(message.date + strftime('%s', '2001-01-01') ,'unixepoch','localtime') " \
                    "as date_uct  FROM message "
    messages = pd.read_sql_query(message_query, conn)

    handles = pd.read_sql_query(" SELECT * FROM handle ", conn)

    messages.rename(columns={'ROWID': 'message_id'}, inplace=True)
    handles.rename(columns={'ROWID': 'handle_id', 'id': 'phone_number'}, inplace=True)

    merge_df = pd.merge(messages[['text', 'handle_id', 'date_uct', 'is_sent', 'message_id', 'is_from_me']],
                        handles[['handle_id', 'phone_number']], on='handle_id', how='left')
    return merge_df


def get_info():   # get phone number and name
    is_default = input("Press X for default value, Y to input from contacts, or any other button to continue: ")

    if is_default.upper() == "X":
        num_list = ["+61466356596", "+447463074383"]
        return num_list, "Christian"

    elif is_default.upper() == "Y":
        contacts = load_contacts()
        while True:
            name_str = input("Enter the full name or X to quit: ")
            num_list = contacts.loc[contacts['FULLNAME'] == name_str, 'ZFULLNUMBER']
            num_list = num_list.tolist()
            if num_list:
                break
            elif name_str.upper() == 'X':
                print("Goodbye!")
                raise SystemExit
            else:
                print(name_str, "is not in your contacts.")

    else:
        num_list = input("Input number(s), separated by commas: ")
        num_list = num_list.split()
        name_str = input("Input name: ")

    return num_list, name_str


def volume(df):
    msg_from_me = df[df['is_from_me'] == 1]
    print("Total Messages:", len(df))
    print("Messages from Me to Recipient: ", len(msg_from_me))
    print("Messages from Recipient to Me: ", len(df)-len(msg_from_me))


def percent(df):    # percent of messages from sender to recipient
    msg_from_me = df[df['is_from_me'] == 1]
    try:
        print("Percentage from Me to Recipient:", "%.2f%%" % float(len(msg_from_me)*100/len(df)))
        print("Percentage from Recipient to Me:", "%.2f%%" % (100 - float(len(msg_from_me)*100/len(df))))
    except ZeroDivisionError:
        pass


def word_cloud(df):      # create word cloud of iMessage history
    print("\nGenerating word cloud...")

    text = " "
    try:
        for x in df['text']:
            x += " "
            text += x
    except TypeError:
        pass

    try:
        cloud = WordCloud(max_words=60, background_color="white", width=1600, height=800).generate(text)
        plt.figure(figsize=(20, 10), facecolor='k')
        plt.imshow(cloud)
        plt.show()
    except ValueError:
        print("Word cloud cannot be generated.")


def time_series(df):
    style()
    df["date_uct"] = df["date_uct"].astype("datetime64")
    month = df['date_uct'].dt.month
    year = df['date_uct'].dt.year
    sns.countplot(x=month, data=df)
    plt.show()


def show_text(df):
    for msg in df['text']:
        print(msg)


pd.options.mode.chained_assignment = None
df = get_df()                                           # generate df
numbers, name = get_info()                            # get phone number list and target from user

target_df = df[df['phone_number'].isin(numbers)]        # filter df by phone numbers
sent_msgs = target_df[target_df['is_from_me'] == 1]         # filter messages from me
received_msgs = target_df[target_df['is_from_me'] != 1]     # filter messages not from me

print("\nShowing iMessage stats for", name, "...\n")
volume(target_df)
percent(target_df)
# show_text(target_df)
# word_cloud(target_df)
time_series(target_df)
