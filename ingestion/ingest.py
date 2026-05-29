import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

CSV_OCT = None                  # Cậu không có file Oct
CSV_NOV = "data/2019-Nov.csv"   # Đúng với cấu trúc hiện tại

def main():
    # Kết nối đến MotherDuck (sẽ tự động dùng MOTHERDUCK_TOKEN từ .env)
    con = duckdb.connect("md:")
    
    table_name = "bronze_events_raw"
    
    print(f"✅ Bảng {table_name} đã sẵn sàng")
    
    if CSV_NOV and os.path.exists(CSV_NOV):
        file_name = "2019-Nov"
        print(f"⏳ Đang nạp {file_name}...")
        
        # Kiểm tra bảng đã tồn tại chưa
        tables = con.execute("SHOW TABLES").fetchall()
        table_exists = any(table_name == row[0] for row in tables)
        
        # Đọc dữ liệu từ file csv và đẩy lên MotherDuck
        if not table_exists:
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{CSV_NOV}')")
        else:
            con.execute(f"INSERT INTO {table_name} SELECT * FROM read_csv_auto('{CSV_NOV}')")
            
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"✅ Đã nạp {count:,} rows từ {file_name}")
    else:
        print(f"❌ Không tìm thấy file {CSV_NOV}")

if __name__ == "__main__":
    main()
