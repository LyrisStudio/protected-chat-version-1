import stun
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

# Конфигурация
SOURCE_IP = "0.0.0.0"
SOURCE_PORT = 8547
STUN_HOST = 'stun.l.google.com'
STUN_PORT = 19302

class UDPChatApp:
    def __init__(self, master):
        self.master = master
        self.master.title("UDP Chat")

        self.chat_area = scrolledtext.ScrolledText(master, state='disabled', wrap=tk.WORD)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.message_entry = tk.Entry(master)
        self.message_entry.pack(padx=10, pady=10, fill=tk.X)
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(master, text="Отправить", command=self.send_message)
        self.send_button.pack(padx=10, pady=10)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((SOURCE_IP, SOURCE_PORT))

        nat_type, nat = stun.get_nat_type(self.sock, SOURCE_IP, SOURCE_PORT, stun_host=STUN_HOST, stun_port=STUN_PORT)
        self.external_ip = nat['ExternalIP']
        self.external_port = nat['ExternalPort']

        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"Ваш внешний адрес: {self.external_ip}:{self.external_port}\n")
        self.chat_area.config(state='disabled')

        self.reader_thread = threading.Thread(target=self.read_chat, daemon=True)
        self.reader_thread.start()

        self.remote_address = self.get_remote_address()

    def get_remote_address(self):
        while True:
            remote_input = simpledialog.askstring("Удаленный адрес", "Введите `адрес:порт` другого компьютера:")
            if remote_input:
                try:
                    remote_ip, remote_port = remote_input.split(':')
                    remote_port = int(remote_port)
                    return (remote_ip, remote_port)
                except ValueError:
                    messagebox.showerror("Ошибка", "Неверный формат. Пожалуйста, используйте `адрес:порт`.")

    def read_chat(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = f'\r{addr} < {data.decode()}'
                self.update_chat_area(message)
            except Exception as e:
                print(f"Ошибка при получении данных: {e}")

    def update_chat_area(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def send_message(self, event=None):
        line = self.message_entry.get()
        if line == '/exit':
            self.sock.close()
            self.master.quit()
            return
        try:
            self.sock.sendto(line.encode(), self.remote_address)
            self.message_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при отправке сообщения: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = UDPChatApp(root)
    root.mainloop()

