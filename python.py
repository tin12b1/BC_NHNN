import streamlit as st
import pandas as pd
from datetime import date

# Hàm tính tuổi từ ngày sinh
def calculate_age(born):
    """
    Tính tuổi của khách hàng dựa trên ngày sinh và ngày hiện tại.
    Hàm xử lý các giá trị NaN/NaT và đảm bảo đối tượng là datetime.date.
    """
    if pd.isna(born):
        return None
    
    # Đảm bảo 'born' là đối tượng date thuần túy
    try:
        if not isinstance(born, date):
            # Nếu là Timestamp, chuyển sang datetime.date
            born = born.to_pydatetime().date() 
    except:
        # Xử lý trường hợp không thể chuyển đổi thành date (dữ liệu lỗi)
        return None 

    today = date.today()
    
    # Công thức tính tuổi
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age

# Hàm chính của ứng dụng Streamlit
def main():
    # Cấu hình trang
    st.set_page_config(page_title="Ứng Dụng Phân Tích Dữ Liệu Excel", layout="wide")
    
    st.title("📊 Công Cụ Phân Tích Dữ Liệu Khách Hàng Tài Khoản")
    st.markdown("""
    Chào mừng bạn! Vui lòng tải lên tệp **Excel (.xlsx, .xls)** của bạn để bắt đầu phân tích.
    """)
    st.markdown("---")

    # I. Chức năng nạp file excel
    uploaded_file = st.file_uploader(
        "Tải lên tệp Excel (chỉ hỗ trợ .xlsx hoặc .xls)", 
        type=["xlsx", "xls"]
    )

    # Khối xử lý khi có tệp được tải lên
    if uploaded_file is not None:
        try:
            # Đọc tệp Excel
            df = pd.read_excel(uploaded_file)
            st.success("Tải tệp lên thành công!")

            # Định nghĩa các cột bắt buộc theo yêu cầu
            required_cols = [
                'Acctcd', 'Customer_No', 'Customer_Name', 
                'Cust_TypeCode', 'Birthday', 'Cust_DetailTypeCode'
            ]
            
            # Kiểm tra và lọc các cột cần thiết
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"""
                **Lỗi: Không tìm thấy các cột bắt buộc sau trong tệp của bạn:** {', '.join(missing_cols)}
                
                Vui lòng kiểm tra chính xác tên các cột: **Acctcd, Customer_No, Customer_Name, Cust_TypeCode, Birthday, Cust_DetailTypeCode**.
                """)
                return

            df_filtered = df[required_cols].copy()
            
            st.subheader("Xem trước Dữ liệu (6 Cột Cần Thiết)")
            st.dataframe(df_filtered.head())
            st.write(f"Tổng số bản ghi trong tệp: **{len(df_filtered):,}**")
            st.markdown("---")

            # Chuẩn hóa dữ liệu cho việc phân tích
            df_filtered['Acctcd'] = df_filtered['Acctcd'].astype(str).str.strip()
            df_filtered['Cust_TypeCode'] = df_filtered['Cust_TypeCode'].astype(str).str.strip()
            df_filtered['Cust_DetailTypeCode'] = df_filtered['Cust_DetailTypeCode'].astype(str).str.strip()
            
            # Chuyển đổi cột 'Birthday' sang định dạng datetime
            df_filtered['Birthday'] = pd.to_datetime(df_filtered['Birthday'], errors='coerce')


            # II. Nút bấm tính toán
            if st.button("🚀 Thực Hiện Phân Tích & Tính Toán", use_container_width=True):
                
                # --- CALCULATIONS ---
                with st.spinner("Đang thực hiện tính toán..."):
                    
                    # 1. Số lượng bản ghi mà khách hàng độ tuổi từ 15 trở lên
                    df_filtered['Age'] = df_filtered['Birthday'].apply(calculate_age)
                    count_age_15_plus = df_filtered[df_filtered['Age'] >= 15].shape[0]

                    # 2. Số lượng tài khoản thanh toán của KHCN
                    # Tiêu chí: Acctcd = 421101 AND Cust_TypeCode = 100
                    criteria_khcn_payment = (
                        (df_filtered['Acctcd'] == '421101') & 
                        (df_filtered['Cust_TypeCode'] == '100')
                    )
                    count_khcn_payment = df_filtered[criteria_khcn_payment].shape[0]
                    
                    # 2.1. Tài khoản EKYC (Sub-item)
                    # Tiêu chí: Acctcd = 421101 AND Cust_TypeCode = 100 AND Cust_DetailTypeCode = '104'
                    criteria_khcn_ekyc = (
                        criteria_khcn_payment & 
                        (df_filtered['Cust_DetailTypeCode'] == '104')
                    )
                    count_khcn_ekyc = df_filtered[criteria_khcn_ekyc].shape[0]

                    # 3. SỐ LƯỢNG HỒ SƠ CIF KHCN (UNIQUE) - ĐÃ BỔ SUNG
                    # Tiêu chí: Cust_TypeCode = 100
                    criteria_khcn_cif = (df_filtered['Cust_TypeCode'] == '100')
                    # Đếm số lượng khách hàng duy nhất (Customer_No)
                    count_khcn_cif = df_filtered[criteria_khcn_cif]['Customer_No'].nunique()
                    
                    # 4. Số lượng hồ sơ CIF KHTC (unique Customer_No) - TRƯỚC LÀ MỤC 3
                    # Tiêu chí: Cust_TypeCode khác 100
                    criteria_khtc_cif = (df_filtered['Cust_TypeCode'] != '100')
                    # Đếm số lượng khách hàng duy nhất (Customer_No)
                    count_khtc_cif = df_filtered[criteria_khtc_cif]['Customer_No'].nunique()

                    # 5. Số lượng tài khoản thanh toán của KHTC - TRƯỚC LÀ MỤC 4
                    # Tiêu chí: Acctcd = 421101 AND Cust_TypeCode khác 100
                    criteria_khtc_payment = (
                        (df_filtered['Acctcd'] == '421101') & 
                        (df_filtered['Cust_TypeCode'] != '100')
                    )
                    count_khtc_payment = df_filtered[criteria_khtc_payment].shape[0]

                # --- DISPLAY RESULTS ---
                st.subheader("🎉 Kết Quả Phân Tích")

                # Chuẩn bị dữ liệu hiển thị chi tiết
                results_data = {
                    "Chỉ Số Phân Tích": [
                        "1. Khách hàng độ tuổi từ 15 trở lên (Bản ghi)",
                        "2. Tài khoản thanh toán của KHCN (Acctcd=421101 & Type=100)",
                        "2.1. Tài khoản EKYC (thuộc mục 2)",
                        "3. Hồ sơ CIF KHCN (Cust_TypeCode = 100) - UNIQUE", # MỚI
                        "4. Hồ sơ CIF KHTC (Cust_TypeCode ≠ 100) - UNIQUE", # ĐÃ CẬP NHẬT
                        "5. Tài khoản thanh toán của KHTC (Acctcd=421101 & Type ≠ 100)" # ĐÃ CẬP NHẬT
                    ],
                    "Số Lượng Kết Quả": [
                        count_age_15_plus,
                        count_khcn_payment,
                        count_khcn_ekyc,
                        count_khcn_cif, # KẾT QUẢ MỚI
                        count_khtc_cif,
                        count_khtc_payment
                    ]
                }
                
                results_df = pd.DataFrame(results_data)

                # Hiển thị bằng Streamlit columns và metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="1. KH Lớn hơn 15 tuổi", 
                        value=f"{count_age_15_plus:,}",
                        delta="Bản ghi"
                    )
                with col2:
                    st.metric(
                        label="2. TKTT KHCN", 
                        value=f"{count_khcn_payment:,}",
                        delta=f"Trong đó EKYC: {count_khcn_ekyc:,}"
                    )
                with col3:
                    st.metric(
                        label="3. Hồ sơ CIF KHCN (Duy nhất)", # ĐÃ CẬP NHẬT
                        value=f"{count_khcn_cif:,}",
                        delta=f"KHTC CIF: {count_khtc_cif:,} (Mục 4)" # Kèm CIF KHTC
                    )
                    
                st.markdown("---")
                
                # Bảng chi tiết kết quả
                st.table(results_df.set_index("Chỉ Số Phân Tích"))

                st.balloons() 
                st.success("Phân tích dữ liệu hoàn tất!")

        except Exception as e:
            st.error(f"Đã xảy ra lỗi trong quá trình xử lý: {e}")
            st.write("Vui lòng kiểm tra lại định dạng tệp Excel, đặc biệt là cột **Birthday**.")

if __name__ == '__main__':
    main()
