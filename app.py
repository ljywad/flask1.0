from flask import Flask, jsonify, request
import pymysql.cursors
from flask_cors import CORS
import numpy as np
from SVD import denoise
import matplotlib.pyplot as plt
import os
from datetime import datetime
from flask_socketio import SocketIO, emit
import pandas as pd
from sklearn import preprocessing
import tensorflow as tf
from tensorflow.keras.models import load_model
from joblib import load
import pymysql
import pandas as pd
import collections
from dateutil import parser
import matplotlib.dates as mdates
from GetData import get_data, calculate_work_hours, calculate_combined_monthly_work_hours, sensor_status, sensor_status
from flask_compress import Compress

app = Flask(__name__)
CORS(app)
app.config['COMPRESS_LEVEL'] = 1
Compress(app)
socketio = SocketIO(app, cors_allowed_origins="*")


db_config2 = {
    'host': '219.216.107.169',
    'user': 'root',
    'password': '654321',
    'database': 'aid'
}

@app.route('/get-data', methods=['GET'])
def get_all_data():
    try:
        # 调用现有函数获取基础数据
        base_data = get_data(db_config)
        data_status = sensor_status(db_config)
        # work_hours_data = calculate_work_hours()
        # monthly_work_hours_data = calculate_combined_monthly_work_hours()

        # 将数据整合到单个响应中
        all_data = {
            'baseData': base_data,
            'sensor_status': data_status,
            # 'workHoursData': work_hours_data,
            # 'monthlyWorkHoursData': monthly_work_hours_data
        }

        return jsonify(all_data)
    except Exception as e:
        print('Error fetching all data:', e)
        return jsonify({'error': 'Error fetching all data'}), 500

@app.route('/get-work-hours', methods=['GET'])
def get_work_hours():
    try:
        # 调用现有函数获取基础数据
        # base_data = get_data()
        # data_status = sensor_status()
        work_hours_data = calculate_work_hours(db_config)
        monthly_work_hours_data = calculate_combined_monthly_work_hours(db_config)

        # 将数据整合到单个响应中
        work_data = {
            # 'workhoursdata': work_hours_data,
            # 'monthworkhoursdata': monthly_work_hours_data,
            'workHoursData': work_hours_data,
            'monthlyWorkHoursData': monthly_work_hours_data
        }

        return jsonify(work_data)
    except Exception as e:
        print('Error fetching work_data:', e)
        return jsonify({'error': 'Error fetching all data'}), 500

from flask import request

@app.route('/get-data-by-time', methods=['POST'])
def get_data_by_time():
    try:
        data = request.get_json()
        selected_table = data.get('selectedTable')
        print(selected_table)
        start_time = data.get('startTime')
        end_time = data.get('endTime')

        if selected_table not in ['test', 'VSA', 'VSA_WIRELESS']:
            return jsonify({'error': 'Invalid table name'}), 400

        connection = pymysql.connect(**db_config2)

        with connection.cursor() as cursor:
            if selected_table == 'VSA_WIRELESS':
                query = "SELECT nowtime, num_x, num_y, num_z FROM VSA_WIRELESS WHERE nowtime BETWEEN %s AND %s"
            else:
                query = f"SELECT nowtime, num FROM {selected_table} WHERE nowtime BETWEEN %s AND %s"

            cursor.execute(query, (start_time, end_time))
            data_by_time = cursor.fetchall()
            formatted_data = []
            if selected_table == 'VSA_WIRELESS':
                for row in data_by_time:
                    formatted_data.append({'nowtime': row[0], 'num_x': row[1], 'num_y': row[2], 'num_z': row[3]})
            else:
                for row in data_by_time:
                    formatted_data.append({'nowtime': row[0], 'num': row[1]})

            # print(data_by_time)
            # print(formatted_data)

        return jsonify({'data': formatted_data})
    except Exception as e:
        print('Error fetching data by time from MySQL:', e)
        return jsonify({'error': 'Error fetching data by time from MySQL'}), 500
    finally:
        if 'connection' in locals():
            connection.close()


model = load_model("autoencoder_model.h5")
scaler = load('scaler.joblib')

# # 连接到 MySQL 数据库
# def connect_to_mysql():
#     conn = pymysql.connect(
#         host='219.216.107.169',
#         user='root',
#         password='654321',
#         database='IMS',
#         cursorclass=pymysql.cursors.DictCursor
#     )
#     return conn
# 连接到 MySQL 数据库
def connect_to_mysql(host, user, password, database):
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

# 创建数据库表格以保存数据库配置信息
def create_config_table():
    conn = connect_to_mysql(host='127.0.0.1', user='root', password='123456', database='aid')
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS db_config (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    host VARCHAR(255) NOT NULL,
                    user VARCHAR(255) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    database_name VARCHAR(255) NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()

# 创建数据库表格
create_config_table()

@app.route('/config/save', methods=['POST'])
def save_config():
    create_config_table()
    config_data = request.json
    global db_config  # 假设这是应用当前使用的数据库配置
    db_config = request.json  # 更新内存中的配置
    print(db_config)
    conn = connect_to_mysql(host='127.0.0.1', user='root', password='123456', database='aid')
    try:
        with conn.cursor() as cursor:
            # 这里我们每次保存新配置之前不删除旧的配置
            cursor.execute("""
                            SELECT COUNT(*) AS count FROM db_config 
                            WHERE host = %s AND user = %s AND password = %s AND database_name = %s
                        """,
                           (config_data['host'], config_data['user'], config_data['password'], config_data['database']))
            result = cursor.fetchone()
            if result['count'] == 0:
                cursor.execute("""
                    INSERT INTO db_config (host, user, password, database_name)
                    VALUES (%s, %s, %s, %s)
                """, (config_data['host'], config_data['user'], config_data['password'], config_data['database']))
                conn.commit()
            return jsonify({'message': '数据库配置保存成功！'})
    finally:
        conn.close()
    return jsonify({'message': 'Database configuration saved successfully!'})

# 保存数据库配置信息的路由
@app.route('/config1/save', methods=['POST'])
def save_config1():
    create_config_table()
    config_data = request.json
    global db_config1  # 假设这是应用当前使用的数据库配置
    db_config1 = request.json  # 更新内存中的配置
    print(db_config1)
    conn = connect_to_mysql(host='127.0.0.1', user='root', password='123456', database='aid')
    try:
        with conn.cursor() as cursor:
            # 这里我们每次保存新配置之前不删除旧的配置
            cursor.execute("""
                            SELECT COUNT(*) AS count FROM db_config 
                            WHERE host = %s AND user = %s AND password = %s AND database_name = %s
                        """,
                           (config_data['host'], config_data['user'], config_data['password'], config_data['database']))
            result = cursor.fetchone()
            if result['count'] == 0:
                cursor.execute("""
                    INSERT INTO db_config (host, user, password, database_name)
                    VALUES (%s, %s, %s, %s)
                """, (config_data['host'], config_data['user'], config_data['password'], config_data['database']))
                conn.commit()
            return jsonify({'message': '数据库配置保存成功！'})
    finally:
        conn.close()
    return jsonify({'message': 'Database configuration saved successfully!'})

# 加载所有数据库配置信息的路由
@app.route('/config/load', methods=['GET'])
def load_config():
    conn = connect_to_mysql(host='127.0.0.1', user='root', password='123456', database='aid')
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM db_config")
            configs = cursor.fetchall()
            return jsonify(configs)
    finally:
        conn.close()


@app.route('/config/delete/<int:id>', methods=['DELETE'])
def delete_config(id):
    conn = connect_to_mysql(host='127.0.0.1', user='root', password='123456', database='aid')
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM db_config WHERE id = %s", (id,))
            conn.commit()
            return jsonify({'message': '数据库配置删除成功！'})
    finally:
        conn.close()
@app.route('/config/edit/<int:id>', methods=['PUT'])
def edit_config(id):
    config_data = request.json
    conn = connect_to_mysql(host='127.0.0.1', user='root', password='123456', database='aid')
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE db_config 
                SET host = %s, user = %s, password = %s, database_name = %s
                WHERE id = %s
            """, (config_data['host'], config_data['user'], config_data['password'], config_data['database'], id))
            conn.commit()
            return jsonify({'message': '数据库配置修改成功！'})
    finally:
        conn.close()
# 预处理数据
def preprocess_data(data):
    data_scaled = scaler.transform(data)
    return pd.DataFrame(data_scaled, columns=data.columns, index=data.index)

#
db_config1 = {
    'host': 'initial_host',
    'user': 'initial_user',
    'password': 'initial_password',
    'database': 'initial_database'
}
db_config = {
    'host': 'initial_host',
    'user': 'initial_user',
    'password': 'initial_password',
    'database': 'initial_database'
}

# 动态连接数据库
def fetch_data_from_mysql():
    conn = pymysql.connect(
        host=db_config1['host'],
        user=db_config1['user'],
        password=db_config1['password'],
        database=db_config1['database'],
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM test_resmaple_10minutes"
            cursor.execute(query)
            result = cursor.fetchall()

            # 将查询结果转换为 DataFrame
            df = pd.DataFrame(result)

            # 如果 Datetime 是字符串类型，将其转换为日期时间格式
            df['Datetime'] = pd.to_datetime(df['Datetime'])

            # 设置 Datetime 列为索引
            df.set_index('Datetime', inplace=True)
            # 假设你已经对df进行了必要的处理
    finally:
        conn.close()
    return df

def calculate_y(x):
    if x >= 0 and x <= 0.3:
        y = (1 - x ** 0.78)*100
    elif x > 0.3 and x <= 15:
        y = (1 - (x / 15) ** 0.24)*100
    else:
        y = 0
    return y

@app.route('/predict', methods=['GET'])
def predict():
    # 从数据库中获取数据
    df = fetch_data_from_mysql()

    # 数据预处理
    df_preprocessed = preprocess_data(df)

    # 进行预测
    predictions = model.predict(df_preprocessed)

    # 重构数据框架
    reconstructed_df = pd.DataFrame(predictions, columns=df.columns, index=df.index)

    # 计算重构误差
    errors = np.mean(np.abs(reconstructed_df - df_preprocessed), axis=1)
    y_values = [calculate_y(error) for error in errors]

    # 将重构误差转换为 JSON 格式并返回
    return jsonify({'errors': y_values, 'index': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    socketio.run(app, debug=True)