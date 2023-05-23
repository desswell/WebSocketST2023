from contextlib import closing
import signal, sys
from time import sleep
import grpc

import not_pb2
import not_pb2_grpc
import mysql.connector as connector

exit = True


def signal_handler(signal, frame):
    global exit
    exit = False


while exit:
    with grpc.insecure_channel('localhost:7000') as channel:
        stub = not_pb2_grpc.send_notificationsStub(channel=channel)
        with closing(connector.connect(user='root', password="1234",
                                       host='127.0.0.1', database='gos1')) as connection:
            with connection.cursor(dictionary=True) as cursor:
                signal.signal(signal.SIGINT, signal_handler)
                cursor.execute('select * from zayavki_polz')
                data = cursor.fetchall()
                print(data)
                # insert_request = f'insert into zayavki_polz (id_user, id_service, status) values({} {} {})'
                # cursor.executemany(insert_request, data_to_insert)
                data_to_insert = []
                for item in data:
                    new_data = {'id_user': item['id_user'], 'id_service': item['id_service'], 'status': item['status']}
                    data_to_insert.append(new_data)
                connection.commit()
                response = stub.sendNotifications(not_pb2.notifications(data=data_to_insert))
        sleep(2)

print('exit')
sys.exit(0)
