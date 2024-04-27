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

# # 设置保存图像的文件夹路径
# output_folder = 'F:\\vuetest'
# if not os.path.exists(output_folder):
#     os.makedirs(output_folder)


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# MySQL数据库连接配置，请根据实际情况修改
db_config = {
    'host': '219.216.107.169',
    'user': 'root',
    'password': '654321',  # 替换为你的root密码
    # 'database': 'databa_learn',
    'database': 'aid',
    'cursorclass': pymysql.cursors.DictCursor,
}

# 连接到数据库的路由
@app.route('/connect-to-database', methods=['GET'])
def connect_to_database():
    try:
        connection = pymysql.connect(**db_config)
        return jsonify({'message': 'Connected to MySQL'})
    except Exception as e:
        print('Error connecting to MySQL:', e)
        return jsonify({'error': 'Error connecting to MySQL'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@app.route('/get-data', methods=['GET'])
def get_data():
    try:
        with pymysql.connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT nowtime, num FROM vsa ORDER BY nowtime DESC LIMIT 10000")
                data = cursor.fetchall()

        # 转换日期格式
        formatted_data = [{'nowtime': format_date(entry['nowtime']), 'num': entry['num']} for entry in data]
       # processed_nowtime_data, processed_num_data = denoise(nowtime_data, num_data)
        # 分别提取 nowtime 和 num 数据
        nowtime_data = [entry['nowtime'] for entry in formatted_data]
        num_data = [entry['num'] for entry in formatted_data]
        # 处理数据
        processed_nowtime_data, processed_num_data = denoise(nowtime_data, num_data)
        processed_data = {'nowtime': processed_nowtime_data, 'num': processed_num_data}
        original_data = {'nowtime': nowtime_data, 'num': num_data}
        # processed_data = denoise(nowtime_data, num_data)
        # return jsonify({'delay': delay, 'train': train})
        # 绘制对比图并保存
        # 绘制对比图
        plot_comparison(original_data, processed_data, save_to_folder='F:\\vuetest\\1.jpg')

        return jsonify({'data': processed_data})

    except pymysql.Error as e:
        print('Error fetching data from MySQL:', e)
        return jsonify({'error': 'Error fetching data from MySQL'}), 500

def format_date(date_str):
    # 将日期对象转换为字符串
    date_str = date_str.strftime('%a, %d %b %Y %H:%M:%S')
    # 解析日期字符串
    parsed_date = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S')
    # 格式化日期为 'yyyy-mm-dd' 形式
    formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_date


def plot_comparison(original_data, processed_data, save_to_folder):
    plt.figure(figsize=(6, 6))

    # 绘制处理前的数据
    plt.plot(original_data['nowtime'], original_data['num'], label='Original Data', linestyle='-',)

    # 绘制处理后的数据
    plt.plot(processed_data['nowtime'], processed_data['num'], 'r-', label='Processed Data', linestyle='-', )

    plt.title('Original and Processed Data Comparison')
    plt.xlabel('Time')
    plt.ylabel('Num')
    plt.legend()
    # plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=1))  # 每隔15分钟显示一个标签
    # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))

    plt.xticks(rotation=90, fontsize=10)

    plt.tight_layout()

    # 确保文件夹存在
    os.makedirs(save_to_folder, exist_ok=True)

    # 保存图到指定文件夹
    file_path_combined = os.path.join(save_to_folder, 'combined_data_plot.png')

    plt.savefig(file_path_combined)

    plt.close()  # 关闭图，释放资源

@app.route('/get-data2', methods=['GET'])
def get_data2():
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute("SELECT nowtime, num FROM VSA")
            data = cursor.fetchall()


        return jsonify({'data': data})
    except Exception as e:
        print('Error fetching data from MySQL:', e)
        return jsonify({'error': 'Error fetching data from MySQL'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@app.route('/get-data3', methods=['GET'])
def get_data3():
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute("SELECT nowtime, num FROM VSA ORDER BY nowtime DESC LIMIT 100")
            data = cursor.fetchall()


        return jsonify({'data': data})
    except Exception as e:
        print('Error fetching data from MySQL:', e)
        return jsonify({'error': 'Error fetching data from MySQL'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@app.route('/get-data4', methods=['GET'])
def get_data4():
    try:
        connection = pymysql.connect(**db_config)
        data = {}  # 初始化一个空字典来存放每个表的数据
        tables = ['test', 'VSA']  # 假设这是你要查询的三个表的名称
        with connection.cursor() as cursor:
            for table in tables:
                # 修改这里的SQL查询，添加ORDER BY语句按nowtime降序排序，并使用LIMIT子句限制结果数量为100条
                query = f"SELECT nowtime, num FROM {table} ORDER BY nowtime DESC LIMIT 100"
                cursor.execute(query)
                table_data = cursor.fetchall()
                # 由于我们按nowtime降序排序了数据，如果需要按时间升序展示在前端，可以在这里反转列表
                data[table] = table_data[::-1]  # 将查询到的数据存放在字典中，以表名为键
            query_vsa_wireless = f"SELECT nowtime, num_x, num_y, num_z FROM VSA_WIRELESS ORDER BY nowtime DESC LIMIT 100"
            cursor.execute(query_vsa_wireless)
            vsc_data = cursor.fetchall()
            data['VSA_WIRELESS'] = vsc_data[::-1]  # 将 vsc 数据也添加到响应中

        return jsonify({'data': data})
    except Exception as e:
        print('Error fetching data from MySQL:', e)
        return jsonify({'error': 'Error fetching data from MySQL'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

def calculate_work_hours():
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            # 查询表中最后一条记录的日期
            cursor.execute(f"""                
                     SELECT DATE_FORMAT(MAX(nowtime), '%Y-%m-%d') as last_date 
                     FROM (
                          SELECT nowtime FROM test
                          UNION ALL
                         SELECT nowtime FROM VSA
                          ) AS combined""")
            last_date_row = cursor.fetchone()
            last_date = last_date_row['last_date']

            # 查询最后一天的所有记录，并计算工作时长
            cursor.execute(f"""
                            SELECT DATE(nowtime) AS work_day, COUNT(*) AS work_hours
                            FROM (
                                SELECT DISTINCT nowtime FROM (
                                SELECT nowtime FROM test WHERE nowtime >= '{last_date}' AND nowtime < '{last_date}' + INTERVAL 1 DAY AND num > 0.01
                                UNION ALL
                                SELECT nowtime FROM VSA WHERE nowtime >= '{last_date}' AND nowtime < '{last_date}' + INTERVAL 1 DAY AND num > 0.01
                                ) AS combined
                            ) AS unique_nowtime
                            GROUP BY work_day""")
            work_hours_row = cursor.fetchone()
            work_hours = work_hours_row['work_hours']
            #
            non_work_hours = 24*3600 - work_hours  # 假设一天有24小时

            return {
                'Day': last_date,
                'work_hours': work_hours,
                'non_work_hours': non_work_hours
            }
    finally:
        connection.close()

@app.route('/get-work-hours', methods=['GET'])
def get_work_hours():
    try:
        work_hours_data = calculate_work_hours()
        return jsonify(work_hours_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_combined_monthly_work_hours():
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            # 找出两个表中最后一条记录所在的月份
            cursor.execute(f"""
                SELECT DATE_FORMAT(MAX(nowtime), '%Y-%m') as last_month 
                FROM (
                    SELECT nowtime FROM test
                    UNION ALL
                    SELECT nowtime FROM VSA
                ) AS combined
            """)
            last_month_row = cursor.fetchone()
            last_month = last_month_row['last_month']

            # 查询最后一月中，两个表任一中 num > 0.01 的唯一工作时间点
            cursor.execute(f"""
                SELECT MONTH(nowtime) AS work_month, COUNT(*) AS work_hours
                FROM (
                    SELECT DISTINCT nowtime FROM test
                    WHERE DATE_FORMAT(nowtime, '%Y-%m') = '{last_month}' AND num > 0.01
                    UNION
                    SELECT DISTINCT nowtime FROM VSA
                    WHERE DATE_FORMAT(nowtime, '%Y-%m') = '{last_month}' AND num > 0.01
                    ) AS combined
                GROUP BY work_month
            """)
            work_hours_row = cursor.fetchone()
            work_hours = work_hours_row['work_hours']

            # 假设每月工作总小时数为一个月的小时数
            days_in_month = 30  # 简化计算，假设每月30天
            total_hours_in_month = days_in_month * 24*3600
            non_work_hours = total_hours_in_month - work_hours

            return {
                'month': last_month,
                'work_hours': work_hours,
                'non_work_hours': non_work_hours
            }
    finally:
        connection.close()

@app.route('/get-combined-monthly-work-hours', methods=['GET'])
def get_combined_monthly_work_hours():
    try:
        work_hours_data = calculate_combined_monthly_work_hours()
        return jsonify(work_hours_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get-detailed-monthly-work-hours', methods=['GET'])
def get_detailed_monthly_work_hours():
    connection = pymysql.connect(**db_config)
    try:
        detailed_data = {'test': {f'{month:02}': 0 for month in range(1, 13)},
                         'VSA': {f'{month:02}': 0 for month in range(1, 13)},
                         'VSA_WIRELESS': {f'{month:02}': 0 for month in range(1, 13)}}  # 初始化每个月的工作时间为0

        with connection.cursor() as cursor:
            for table_name in ['test', 'VSA']:
                # 统计2023年每个月的工作小时数
                cursor.execute(f"""
                    SELECT 
                      MONTH(nowtime) AS work_month, 
                      COUNT(*) AS work_hours
                    FROM (
                        SELECT DISTINCT
                             nowtime
                        FROM 
                            {table_name}
                        WHERE 
                            YEAR(nowtime) = 2023 AND num > 0.01
                    ) AS unique_nowtime
                    GROUP BY 
                        work_month;
                """)
                results = cursor.fetchall()
                for result in results:
                    month_key = f'{result["work_month"]:02}'
                    detailed_data[table_name][month_key] = result['work_hours']

            cursor.execute(f"""
                    SELECT 
                      MONTH(nowtime) AS work_month, 
                      COUNT(*) AS work_hours
                    FROM (
                        SELECT DISTINCT
                             nowtime
                        FROM 
                            VSA_WIRELESS
                        WHERE 
                            YEAR(nowtime) = 2023 AND (num_x > 0.1 OR num_y > 0.1 OR num_z > 0.1)
                    ) AS unique_nowtime
                    GROUP BY 
                        work_month;
                """)

            results = cursor.fetchall()
            for result in results:
                month_key = f'{result["work_month"]:02}'
                detailed_data['VSA_WIRELESS'][month_key] = result['work_hours']

        return jsonify(detailed_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-status', methods=['GET'])
def sensor_status():
    status = {'sensor1': '未作业', 'sensor2': '未作业', 'sensor3': '未作业'}  # 初始状态包含传感器3
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            # 查询test表最后一条数据的状态
            cursor.execute("SELECT num FROM test ORDER BY nowtime DESC LIMIT 1")
            result = cursor.fetchone()
            if result and result['num'] > 0.01:
                status['sensor1'] = '作业中'

            # 查询vsa表最后一条数据的状态
            cursor.execute("SELECT num FROM VSA ORDER BY nowtime DESC LIMIT 1")
            result = cursor.fetchone()
            if result and result['num'] > 0.01:
                status['sensor2'] = '作业中'

            # 查询vsa_wireless表最后一条数据的状态，判断传感器3
            cursor.execute("""
                SELECT num_x, num_y, num_z FROM VSA_WIRELESS
                ORDER BY nowtime DESC LIMIT 1
            """)
            result = cursor.fetchone()
            if result and (result['num_x'] > 0.1 or result['num_y'] > 0.1 or result['num_z'] > 0.1):
                status['sensor3'] = '作业中'

        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()
# @app.route('/get-data1', methods=['GET'])
# def get_data1():
#     try:
#         connection = pymysql.connect(**db_config)
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT nowtime, num FROM vsa ORDER BY nowtime DESC LIMIT 100")
#             data = cursor.fetchall()
#
#         # 发送数据到前端
#         socketio.emit('update_data', {'data': data})
#         return jsonify({'data': data})
#     except Exception as e:
#         print('Error fetching data from MySQL:', e)
#         return jsonify({'error': 'Error fetching data from MySQL'}), 500
#     finally:
#         if 'connection' in locals():
#             connection.close()
#
# # 新增SocketIO事件，用于实时推送数据
# @socketio.on('connect')
# def handle_connect():
#     print('Client connected')
#     emit_data()  # 发送初始数据
#
# def emit_data():
#     try:
#         connection = pymysql.connect(**db_config)
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT nowtime, num FROM vsa ORDER BY nowtime DESC LIMIT 100")
#             data = cursor.fetchall()
#         socketio.emit('update_data', {'data': data})
#     except Exception as e:
#         print('Error fetching data from MySQL:', e)
#     finally:
#         if 'connection' in locals():
#             connection.close()
# def emit_data():
#     try:
#         connection = pymysql.connect(**db_config)
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT nowtime, num FROM your_table ORDER BY nowtime DESC LIMIT 100")
#             data = cursor.fetchall()
#         socketio.emit('update_data', {'data': data})
#     except Exception as e:
#         print('Error fetching data from MySQL:', e)
#     finally:
#         if 'connection' in locals():
#             connection.close()
#
# # 新增SocketIO事件，用于实时推送数据
# @socketio.on('connect')
# def handle_connect():
#     print('Client connected')
#     emit_data()  # 发送初始数据
#
# if __name__ == '__main__':
#     socketio.run(app, debug=True)

# @app.route('/get-data-by-time', methods=['POST'])
# def get_data_by_time():
#     try:
#         data = request.get_json()
#         start_time = data.get('startTime')
#         end_time = data.get('endTime')
#         page = data.get('page', 1)  # 默认显示第一页
#         page_size = data.get('pageSize', 50)  # 默认每页显示50条
#
#         connection = pymysql.connect(**db_config)
#         with connection.cursor() as cursor:
#             # 根据时间段查询数据，并进行分页
#             query = "SELECT nowtime, num FROM vsa WHERE nowtime BETWEEN %s AND %s "
#             cursor.execute(query, (start_time, end_time))
#             data_by_time = cursor.fetchall()
#
#         return jsonify({'data': data_by_time})
#     except Exception as e:
#         print('Error fetching data by time from MySQL:', e)
#         return jsonify({'error': 'Error fetching data by time from MySQL'}), 500
#     finally:
#         if 'connection' in locals():
#             connection.close()

@app.route('/get-data-by-time', methods=['POST'])
def get_data_by_time():
    try:
        data = request.get_json()
        selected_table = data.get('selectedTable')
        start_time = data.get('startTime')
        end_time = data.get('endTime')

        if selected_table not in ['test', 'VSA', 'VSA_WIRELESS']:
            return jsonify({'error': 'Invalid table name'}), 400

        connection = pymysql.connect(**db_config)

        with connection.cursor() as cursor:
            if selected_table == 'VSA_WIRELESS':
                query = "SELECT nowtime, num_x, num_y, num_z FROM VSA_WIRELESS WHERE nowtime BETWEEN %s AND %s"
            else:
                query = f"SELECT nowtime, num FROM {selected_table} WHERE nowtime BETWEEN %s AND %s"

            cursor.execute(query, (start_time, end_time))
            data_by_time = cursor.fetchall()

        return jsonify({'data': data_by_time})
    except Exception as e:
        print('Error fetching data by time from MySQL:', e)
        return jsonify({'error': 'Error fetching data by time from MySQL'}), 500
    finally:
        if 'connection' in locals():
            connection.close()


from flask import request
# @app.route('/svd_data', methods=['GET'])
# def svd_data():
#     try:
#         # 连接到MySQL数据库
#         connection = pymysql.connect(**db_config)
#         cursor = connection.cursor()
#
#         # 从数据库中获取数据
#         cursor.execute("SELECT nowtime, num FROM vsa ORDER BY nowtime DESC LIMIT 1000")
#         result = cursor.fetchall()
#
#         # 将数据转换为NumPy数组
#         data_array = np.array(result)
#
#
#         # 获取时间和振动数据列
#         nowtime_column = data_array[:, 0]
#         num_column = data_array[:, 1]
#
#         # 构建数据矩阵
#         data_matrix = np.column_stack((nowtime_column, num_column))
#
#         # 调用SVD降噪函数
#         denoised_matrix = svd_denoise(data_matrix)
#
#         # 绘制对比图
#         plt.figure(figsize=(10, 5))
#         plt.subplot(1, 2, 1)
#         plt.plot(data_matrix[:, 0], data_matrix[:, 1], 'b.', label='原始数据')
#         plt.title('原始数据')
#         plt.xlabel('时间')
#         plt.ylabel('振动数据')
#
#         plt.subplot(1, 2, 2)
#         plt.plot(denoised_matrix[:, 0], denoised_matrix[:, 1], 'g.', label='降噪数据')
#         plt.title('降噪数据')
#         plt.xlabel('时间')
#         plt.ylabel('振动数据')
#
#         # 保存对比图到文件夹
#         image_path = os.path.join(output_folder, 'comparison_plot.png')
#         plt.savefig(image_path)
#         plt.close()
#
#         # 将降噪后的数据转换为字典格式
#         response_data = {'nowtime': denoised_matrix[:, 0].tolist(), 'num': denoised_matrix[:, 1].tolist(), 'image_path': image_path}
#
#         # 关闭数据库连接
#         cursor.close()
#         connection.close()
#
#         return jsonify(response_data)
#
#     except Exception as e:
#         return jsonify({'error': str(e)})
#
# # 路由：返回保存的图像文件
# @app.route('/get_image')
# def get_image():
#     image_path = os.path.join(output_folder, 'comparison_plot.png')
#     return send_file(image_path, mimetype='image/png')

# @app.route('/')
# def get_data1():
#     # 使用pymysql连接MySQL数据库
#     with pymysql.connect(**db_config) as connection:
#         with connection.cursor() as cursor:
#             # 从MySQL表中查询数据
#             query_num1 = "SELECT Datetime, num FROM test"
#             query_num2 = "SELECT Datetime, num FROM VSA"
#
#             # 执行查询
#             cursor.execute(query_num1)
#             result_num1 = cursor.fetchall()
#             cursor.execute(query_num2)
#             result_num2 = cursor.fetchall()
#
#     # 将查询结果转换为pandas DataFrames
#     second_data1 = pd.DataFrame(result_num1).set_index('Datetime')
#     second_data2 = pd.DataFrame(result_num2).set_index('Datetime')
#
#     # 进行连接操作
#     second_data = second_data1.join(second_data2, how='inner', lsuffix='_num1', rsuffix='_num2')
#
#     # 将DataFrame转换为JSON
#     data_json = second_data.to_json(orient='index')
#
#     return jsonify(data_json)

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

# 保存数据库配置信息到数据库
# def save_db_config(config):
#     conn = connect_to_mysql(host='127.0.0.1', user='root', password='123456', database='aid')
#     try:
#         with conn.cursor() as cursor:
#             cursor.execute("""
#                 INSERT INTO db_config2 (host, user, password, database_name)
#                 VALUES (%s, %s, %s, %s)
#             """, (config['host'], config['user'], config['password'], config['database_name']))
#         conn.commit()
#     finally:
#         conn.close()

# 从数据库加载所有数据库配置信息
# def load_all_db_config():
#     conn = connect_to_mysql(host='127.0.0.1', user='root', password='123456', database='aid')
#     try:
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT * FROM db_config2")
#             results = cursor.fetchall()
#             configs = []
#             for result in results:
#                 config = {
#                     'host': result['host'],
#                     'user': result['user'],
#                     'password': result['password'],
#                     'database_name': result['database_name']
#                 }
#                 configs.append(config)
#             return configs
#     finally:
#         conn.close()

# 创建数据库表格
create_config_table()

# 测试路由
@app.route('/')
def index():
    return "Welcome to the database configuration app!"

# 保存数据库配置信息的路由
@app.route('/config/save', methods=['POST'])
def save_config():
    create_config_table()
    config_data = request.json
    global db_config1  # 假设这是应用当前使用的数据库配置
    db_config1 = request.json  # 更新内存中的配置
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


# # 从 MySQL 数据库中读取数据
# def fetch_data_from_mysql():
#     # 连接到 MySQL 数据库
#     conn = pymysql.connect(
#         host='219.216.107.169',
#         user='root',
#         password='654321',
#         database='IMS',
#         cursorclass=pymysql.cursors.DictCursor
#     )
#
#     try:
#         # 执行查询
#         with conn.cursor() as cursor:
#             # query = "SELECT Datetime, Bearing1, Bearing2, Bearing3, Bearing4 FROM test_resmaple_10minutes"
#             query = "SELECT * FROM test_resmaple_10minutes"
#             cursor.execute(query)
#             result = cursor.fetchall()
#
#             # 将查询结果转换为 DataFrame
#             df = pd.DataFrame(result)
#
#             # 如果 Datetime 是字符串类型，将其转换为日期时间格式
#             df['Datetime'] = pd.to_datetime(df['Datetime'])
#
#             # 设置 Datetime 列为索引
#             df.set_index('Datetime', inplace=True)
#
#     finally:
#         # 关闭数据库连接
#         conn.close()
#
#     return df
#
#
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


@app.route('/config/update', methods=['POST'])
def update_config():
    global db_config1
    db_config1 = request.json
    return jsonify({'message': 'Database configuration updated successfully!'})

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

    # 将重构误差转换为 JSON 格式并返回
    return jsonify({'errors': errors.tolist(), 'index': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist()})


if __name__ == '__main__':
    app.run(host='127.0.0.2', port=5002)
    socketio.run(app, debug=True)