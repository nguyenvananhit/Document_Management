import requests
from bs4 import BeautifulSoup
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import time
from threading import Thread, Lock
from ttkbootstrap import Style

# Khóa để đảm bảo rằng các thao tác cập nhật giao diện được thực hiện một cách đồng bộ
update_lock = Lock()

# Hàm trích xuất thông tin công ty từ một trang
def extract_companies_info(soup):
    companies_info = []
    
    for element in soup.find_all('div', class_='w-100 h-auto shadow rounded-3 bg-white p-2 mb-3'):
        name_tag = element.find('h2')
        name = name_tag.get_text(strip=True) if name_tag else 'Không có tên'
        
        address_tag = element.find('div', class_='listing_diachi_nologo')
        address = address_tag.find('small').get_text(strip=True) if address_tag and address_tag.find('small') else 'Không có địa chỉ'
        
        phone_numbers = []
        phone_tags = element.find_all('a', href=True)
        for tag in phone_tags:
            if 'tel:' in tag['href']:
                phone_number = tag.get_text(strip=True)
                phone_numbers.append(phone_number)
        
        phone_numbers_str = ', '.join(phone_numbers) if phone_numbers else 'Không có số điện thoại'
        
        email = 'Không có email'
        website = 'Không có website'
        email_tag = element.find('div', class_='email_web_section')
        if email_tag:
            a_tags = email_tag.find_all('a')
            if len(a_tags) > 0:
                email = a_tags[0].get('href').replace('mailto:', '').strip() if a_tags[0].get('href') else 'Không có email'
            if len(a_tags) > 1:
                website = a_tags[1].get('href').strip() if a_tags[1].get('href') else 'Không có website'
        
        companies_info.append({
            'Tên công ty': name,
            'Địa chỉ': address,
            'Số điện thoại': phone_numbers_str,
            'Email': email,
            'Website': website
        })
    
    return companies_info

# Hàm lấy dữ liệu từ nhiều trang
def scrape_website(urls, start_page, end_page, sleep_time, progress_callback, completion_callback):
    all_companies_info = []

    def process_url(url):
        for page in range(start_page, end_page + 1):
            page_url = f"{url}?page={page}"
            try:
                response = requests.get(page_url)
                response.encoding = 'utf-8'  # Đảm bảo encoding là UTF-8
                response.raise_for_status()  # Kiểm tra lỗi yêu cầu

                soup = BeautifulSoup(response.text, 'html.parser')
                companies_info = extract_companies_info(soup)
                all_companies_info.extend(companies_info)

                progress_callback(f"Đã lấy dữ liệu từ {page_url}")
                time.sleep(sleep_time)  # Tạm dừng giữa các yêu cầu
            except requests.RequestException as e:
                progress_callback(f"Lỗi khi lấy dữ liệu từ {page_url}: {e}")

    threads = []
    for url in urls:
        thread = Thread(target=process_url, args=(url,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    completion_callback(all_companies_info)

# Hàm xử lý khi nhấn nút "Lưu dữ liệu"
def on_save_button_click():
    urls = url_text.get("1.0", tk.END).strip().split('\n')
    start_page = int(start_page_entry.get())
    end_page = int(end_page_entry.get())
    sleep_time = float(sleep_time_entry.get())  # Lấy thời gian nghỉ từ giao diện
    
    def save_data(file_name):
        def update_progress(message):
            log_text.insert(tk.END, message + '\n')
            log_text.yview(tk.END)
        
        def on_done():
            if root.winfo_exists():
                messagebox.showinfo("Thành công", f"Dữ liệu đã được xuất ra {file_name}")

        try:
            scrape_website(urls, start_page, end_page, sleep_time, update_progress, lambda data: save_to_file(file_name, data, on_done))
        except Exception as e:
            if root.winfo_exists():
                messagebox.showerror("Lỗi", str(e))

    def save_to_file(file_name, data, callback):
        try:
            df = pd.DataFrame(data)
            df.to_excel(file_name, index=False, engine='openpyxl')
            callback()
        except Exception as e:
            if root.winfo_exists():
                messagebox.showerror("Lỗi", str(e))

    def show_progress_window():
        progress_window = tk.Toplevel(root)
        progress_window.title("Tiến trình")
        tk.Label(progress_window, text="Đang lưu dữ liệu, vui lòng chờ...", padx=20, pady=20).pack()
        progress_bar = ttk.Progressbar(progress_window, orient='horizontal', length=300, mode='indeterminate')
        progress_bar.pack(padx=20, pady=20)
        progress_bar.start()

        def on_done():
            if root.winfo_exists():
                progress_bar.stop()
                progress_window.destroy()

        # Mở hộp thoại chọn tên file
        file_name = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                               filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
                                               title="Chọn nơi lưu file")
        if file_name:
            thread = Thread(target=lambda: (save_data(file_name), on_done()))
            thread.start()
        else:
            on_done()

    show_progress_window()

# Hàm cập nhật giao diện người dùng với dữ liệu
def update_table(data):
    with update_lock:
        for row in tree.get_children():
            tree.delete(row)
        for item in data:
            tree.insert('', 'end', values=(item['Tên công ty'], item['Địa chỉ'], item['Số điện thoại'], item['Email'], item['Website']))

# Hàm xử lý khi nhấn nút "Tải dữ liệu"
def on_load_button_click():
    urls = url_text.get("1.0", tk.END).strip().split('\n')
    start_page = int(start_page_entry.get())
    end_page = int(end_page_entry.get())
    sleep_time = float(sleep_time_entry.get())  # Lấy thời gian nghỉ từ giao diện
    
    def load_data():
        def update_progress(message):
            log_text.insert(tk.END, message + '\n')
            log_text.yview(tk.END)

        def on_done():
            if root.winfo_exists():
                messagebox.showinfo("Thành công", "Dữ liệu đã được tải và hiển thị")

        try:
            scrape_website(urls, start_page, end_page, sleep_time, update_progress, lambda data: (update_table(data), on_done()))
        except Exception as e:
            if root.winfo_exists():
                messagebox.showerror("Lỗi", str(e))

    def show_progress_window():
        progress_window = tk.Toplevel(root)
        progress_window.title("Tiến trình")
        tk.Label(progress_window, text="Đang tải dữ liệu, vui lòng chờ...", padx=20, pady=20).pack()
        progress_bar = ttk.Progressbar(progress_window, orient='horizontal', length=300, mode='indeterminate')
        progress_bar.pack(padx=20, pady=20)
        progress_bar.start()

        def on_done():
            if root.winfo_exists():
                progress_bar.stop()
                progress_window.destroy()

        thread = Thread(target=lambda: (load_data(), on_done()))
        thread.start()

    show_progress_window()

# Tạo giao diện Tkinter với ttkbootstrap
root = tk.Tk()
root.title("Scrape Web Data")

# Áp dụng chủ đề ttkbootstrap
style = Style(theme='cosmo')  # Có thể thử các chủ đề khác như 'superhero', 'darkly', 'litera'

# URL
tk.Label(root, text="Nhập các URL (mỗi URL trên một dòng):").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
url_text = tk.Text(root, height=6, width=50)
url_text.grid(row=0, column=1, padx=10, pady=5)

# Trang bắt đầu
tk.Label(root, text="Nhập trang bắt đầu:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
start_page_entry = ttk.Entry(root, width=10)
start_page_entry.grid(row=1, column=1, padx=10, pady=5)

# Trang kết thúc
tk.Label(root, text="Nhập trang kết thúc:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
end_page_entry = ttk.Entry(root, width=10)
end_page_entry.grid(row=2, column=1, padx=10, pady=5)

# Thời gian nghỉ
tk.Label(root, text="Thời gian nghỉ (giây):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
sleep_time_entry = ttk.Entry(root, width=10)
sleep_time_entry.grid(row=3, column=1, padx=10, pady=5)

# Nút tải dữ liệu
load_button = ttk.Button(root, text="Tải dữ liệu", command=on_load_button_click)
load_button.grid(row=4, column=0, columnspan=2, pady=10)

# Nút lưu dữ liệu
save_button = ttk.Button(root, text="Lưu dữ liệu", command=on_save_button_click)
save_button.grid(row=5, column=0, columnspan=2, pady=10)

# Hiển thị dữ liệu trong bảng
columns = ('Tên công ty', 'Địa chỉ', 'Số điện thoại', 'Email', 'Website')
tree = ttk.Treeview(root, columns=columns, show='headings')
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=200)
tree.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

# Widget để hiển thị thông báo sự kiện
log_text = tk.Text(root, height=10, width=80)
log_text.grid(row=8, column=0, columnspan=2, padx=10, pady=10)
log_text.insert(tk.END, "Chào mừng bạn đến với ứng dụng Scrape Web Data!\n")

root.mainloop()
