import pandas as pd
import numpy as np

def check_labels(csv_path):
    """檢查CSV中label欄位的值
    
    Args:
        csv_path: CSV檔案路徑
        
    檢查項目:
    1. 統計每個label出現次數
    2. 檢查是否有空值
    3. 檢查資料型態
    4. 列出所有unique的值
    """
    # 讀取CSV
    df = pd.read_csv(csv_path)
    
    print("=== Label欄位檢查報告 ===")
    
    # 1. 基本資訊
    print("\n1. 基本資訊:")
    print(f"總資料筆數: {len(df)}")
    print(f"Label欄位資料型態: {df['label'].dtype}")
    
    # 2. 空值檢查
    print("\n2. 空值檢查:")
    null_count = df['label'].isnull().sum()
    print(f"空值數量: {null_count}")
    if null_count > 0:
        print("空值的索引:")
        print(df[df['label'].isnull()].index.tolist())
        
        # 顯示這些空值記錄的其他欄位資訊
        print("\n空值記錄的詳細資訊:")
        print(df[df['label'].isnull()])
    
    # 3. 值的分布
    print("\n3. Label值分布:")
    print(df['label'].value_counts())
    
    # 4. 檢查非字串值
    print("\n4. 檢查非字串值:")
    non_str = df[~df['label'].apply(lambda x: isinstance(x, str) if pd.notnull(x) else True)]
    if len(non_str) > 0:
        print("發現非字串值:")
        print(non_str[['label']])
    else:
        print("所有值都是字串類型")
    
    # 5. 顯示所有unique值 (排除NaN)
    print("\n5. 所有不重複的label值:")
    # 使用dropna()去除NaN值再排序
    unique_labels = df['label'].dropna().unique()
    try:
        unique_labels = sorted(unique_labels)
        print("排序後的label值:")
    except TypeError:
        print("無法排序(可能包含不同型態),直接顯示:")
    print(unique_labels)
    
    # 6. 檢查每個label的值是否合理
    print("\n6. Label值的長度檢查:")
    label_lengths = df['label'].str.len()
    print(f"最短label長度: {label_lengths.min()}")
    print(f"最長label長度: {label_lengths.max()}")
    
    # 找出特別短或特別長的label
    if label_lengths.min() < 2:  # 假設正常label至少2個字
        print("\n特別短的label:")
        print(df[label_lengths < 2]['label'].unique())
    
    if label_lengths.max() > 20:  # 假設正常label不會超過20個字
        print("\n特別長的label:")
        print(df[label_lengths > 20]['label'].unique())

if __name__ == "__main__":
    csv_path = "data\ETL_dataframe.csv"  # 使用你的CSV檔案路徑
    check_labels(csv_path)