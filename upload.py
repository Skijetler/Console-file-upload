#!/usr/bin/python

from requests import post, get, RequestException
import sys
import random
import json
import sqlite3
import argparse


database_file = "files.db"

sql_create_files_table = """ CREATE TABLE IF NOT EXISTS files (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    url text NOT NULL,
                                    size text NOT NULL
                                ); """


urls = ["https://bayfiles.com/api/upload"]


def database_connect(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error:
        print("Error! cannot create the database connection.")

    return None

def add_file_to_db(req, file):
    sql_add_file = "INSERT INTO files(name, url, size) VALUES(?,?,?)"
    file_list = [file["name"], file["url"], file["size"]]
    req.execute(sql_add_file, file_list)

def get_all_files_from_db(req):
    sql_get_all_files = "SELECT * FROM files"
    req.execute(sql_get_all_files)
    return req.fetchall()

def get_file_from_db(req, db_id):
    sql_get_file = "SELECT * FROM files WHERE id=?"
    req.execute(sql_get_file, (db_id,))
    return req.fetchall()

def delete_file_from_db(req, db_id):
    sql_delete_file = "DELETE FROM files WHERE id=?"
    req.execute(sql_delete_file, (db_id,))

def send_file(filename):
    files = {'file': open(filename, 'rb')}

    responce = None
    conn_error = None

    while conn_error is not False:
        try:
            responce = post(url=random.choice(urls), files=files)
            conn_error = False
        except RequestException:
            conn_error = True

    json_responce = json.loads(responce.text)

    if conn_error == False and json_responce["status"] is not False:
        return {"error": False,
                "name": json_responce["data"]["file"]["metadata"]["name"],
                "url": json_responce["data"]["file"]["url"]["short"],
                "size": json_responce["data"]["file"]["metadata"]["size"]["readable"]}
    else:
        return {"error": True}

# don't use
def get_proxy(proxy_type):
    responce = get(url="https://www.proxy-list.download/api/v1/get", params={"type": proxy_type, "anon": "elite", "country": "US"})
    return proxy_type + "://" + random.choice(responce.text.split())

def print_file_data(file_data):
    print("id: " + str(file_data[0]) + " name: " + file_data[1] + " url: " + file_data[2] + " size: " + file_data[3])


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Upload files from command line to file hostings')
    parser.add_argument("-f", type=str, metavar='filename', dest="filename", help="upload file")
    parser.add_argument("-d", type=int, metavar='id', dest="db_id_d", help="delete file from database")
    parser.add_argument("-s", type=str, metavar='id', dest="db_id_s", help="show all information about file")
    parser.add_argument("--show_all", action='store_true', help="show all files in database")

    args = parser.parse_args()
    
    if (args.filename is None and args.db_id_d is None and args.db_id_s is None and args.show_all == False):
        print("execute programm with '-h' argument for more detailed information")

    else:
        db = database_connect(database_file)

        if db is not None:
            requester = db.cursor()
            requester.execute(sql_create_files_table)

            if args.filename is not None :
                file_data = send_file(args.filename)
                if file_data["error"] == True:
                    print("Something goes wrong with sending file to file hosting")
                    db.close()
                    sys.exit()
                add_file_to_db(requester, file_data)
                db.commit()
                db.close()
                print("name: " + file_data["name"] + " url: " + file_data["url"] + " size: " + file_data["size"])
                sys.exit()
                
            if args.show_all != False :
                files_data = get_all_files_from_db(requester)
                db.close()
                for file_data in files_data:
                    print_file_data(file_data)
                sys.exit()

            if args.db_id_s is not None :
                file_data = get_file_from_db(requester, args.db_id_s)[0]
                db.close()
                print_file_data(file_data)
                sys.exit()

            if args.db_id_d is not None :
                delete_file_from_db(requester, args.db_id_d)
                db.commit()
                db.close()
                sys.exit()

        else:
            sys.exit()