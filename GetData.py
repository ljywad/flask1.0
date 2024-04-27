import pymysql

def get_data(db_config):
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
                # data[table] = table_data[::-1]  # 将查询到的数据存放在字典中，以表名为键
                data[table] = [{'nowtime': row[0], 'num': row[1]} for row in table_data]  # 将查询到的数据存放在字典中，以表名为键
            query_vsa_wireless = f"SELECT nowtime, num_x, num_y, num_z FROM VSA_WIRELESS ORDER BY nowtime DESC LIMIT 100"
            cursor.execute(query_vsa_wireless)
            vsc_data = cursor.fetchall()
            # data['VSA_WIRELESS'] = vsc_data[::-1]  # 将 vsc 数据也添加到响应中
            data['VSA_WIRELESS'] = [{'nowtime': row[0], 'num_x': row[1], 'num_y': row[2], 'num_z': row[3]} for row in
                                    vsc_data]  # 将 vsc 数据也添加到响应中
            # print("table_data structure:", table_data)
            # print("vsc_data structure:", vsc_data)

    except Exception as e:
        print('Error fetching base data from MySQL:', e)
    finally:
        if connection:
            connection.close()

    return data

def calculate_work_hours(db_config):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            # 查询表中最后一条记录的日期
            cursor.execute(f"""                
                     SELECT DATE_FORMAT(MAX(nowtime), '%Y-%m-%d') as last_date
                     FROM (
                            SELECT MAX(nowtime) as nowtime FROM test
                            UNION ALL
                            SELECT MAX(nowtime) as nowtime FROM VSA
                           ) AS combined""")
            last_date_row = cursor.fetchone()
            last_date = last_date_row[0]

            # 查询最后一天的所有记录，并计算工作时长
            cursor.execute(f"""
                            SELECT DATE(nowtime) AS work_day, COUNT(*) AS work_hours
                            FROM (
                                SELECT DISTINCT nowtime FROM test WHERE nowtime >= '{last_date}' AND nowtime < '{last_date}' + INTERVAL 1 DAY AND num > 0.01
                                UNION 
                                SELECT DISTINCT nowtime FROM VSA WHERE nowtime >= '{last_date}' AND nowtime < '{last_date}' + INTERVAL 1 DAY AND num > 0.01
                            ) AS combined
                            GROUP BY work_day
                            """)
            work_hours_row = cursor.fetchone()
            work_hours = work_hours_row[1]
            #
            non_work_hours = 24*3600 - work_hours  # 假设一天有24小时

            return {
                'Day': last_date,
                'work_hours': work_hours,
                'non_work_hours': non_work_hours
            }
    finally:
        connection.close()



def calculate_combined_monthly_work_hours(db_config):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            # 找出两个表中最后一条记录所在的月份
            cursor.execute(f"""
                SELECT DATE_FORMAT(MAX(nowtime), '%Y-%m') as last_month
                FROM (
                    SELECT MAX(nowtime) as nowtime FROM test
                    UNION ALL
                    SELECT MAX(nowtime) as nowtime FROM VSA
                ) AS combined""")

            last_month_row = cursor.fetchone()
            last_month = last_month_row[0]

            # 查询最后一月中，两个表任一中 num > 0.01 的唯一工作时间点
            cursor.execute(f"""
                   SELECT MONTH( nowtime ) AS work_month, COUNT(*) AS work_hours 
                   FROM
	                  (
	                  SELECT nowtime FROM test
	                  WHERE
		                nowtime >= '{last_month}-01'
		                AND nowtime < DATE_ADD( '{last_month}-01', INTERVAL 1 MONTH ) AND num > 0.01 UNION
	                  SELECT
		                nowtime 
	                  FROM
		                VSA
	                  WHERE
		                nowtime >= '{last_month}-01'
		                AND nowtime < DATE_ADD( '{last_month}-01', INTERVAL 1 MONTH ) AND num > 0.01 
	                  ) AS combined 
                   GROUP BY
	                    work_month
            """)
            work_hours_row = cursor.fetchone()
            work_hours = work_hours_row[1]

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

def sensor_status(db_config):
    status = {'sensor1': '未作业', 'sensor2': '未作业', 'sensor3': '未作业'}  # 初始状态包含传感器3
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            # 查询test表最后一条数据的状态
            cursor.execute("SELECT num FROM test ORDER BY nowtime DESC LIMIT 1")
            result = cursor.fetchone()
            if result and result[0] > 0.01:
                status['sensor1'] = '作业中'

            # 查询vsa表最后一条数据的状态
            cursor.execute("SELECT num FROM VSA ORDER BY nowtime DESC LIMIT 1")
            result = cursor.fetchone()
            if result and result[0] > 0.01:
                status['sensor2'] = '作业中'

            # 查询vsa_wireless表最后一条数据的状态，判断传感器3
            cursor.execute("""
                SELECT num_x, num_y, num_z FROM VSA_WIRELESS
                ORDER BY nowtime DESC LIMIT 1
            """)
            result = cursor.fetchone()
            if result and (result[0] > 0.1 or result[1] > 0.1 or result[2] > 0.1):
                status['sensor3'] = '作业中'

    except Exception as e:
        print('Error fetching base data from MySQL:', e)
    finally:
        if connection:
            connection.close()

    return status

