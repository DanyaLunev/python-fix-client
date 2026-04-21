# test_simplefix.py - Простейший тест с simplefix

import socket
import simplefix
import datetime

# ========== НАСТРОЙКИ (ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ) ==========
HOST = '192.168.0.13'  # IP сервера банка
PORT = 1234            # Порт сервера банка

# Параметры подключения (попробуйте разные варианты)
SENDER_COMP_ID = "CLIENT"     # Ваш идентификатор
TARGET_COMP_ID = "SERVER"     # Идентификатор банка
FIX_VERSION = "FIX.4.2"       # Версия FIX
# ==========================================================

def create_logon_message():
    """Создает Logon сообщение используя simplefix"""
    
    # Создаем новое сообщение
    msg = simplefix.FixMessage()
    
    # Добавляем поля
    msg.append_pair(35, 'A')                    # MsgType = Logon
    msg.append_pair(49, SENDER_COMP_ID)         # SenderCompID
    msg.append_pair(56, TARGET_COMP_ID)         # TargetCompID
    msg.append_pair(34, 1)                      # MsgSeqNum
    msg.append_utc_timestamp(52)                # SendingTime (автоматический формат)
    msg.append_pair(98, 0)                      # EncryptMethod (0 = нет шифрования)
    msg.append_pair(108, 30)                    # HeartBtInt (30 секунд)
    
    return msg

def print_fix_message(data, prefix="📦 Сообщение"):
    """Красиво печатает FIX сообщение"""
    readable = data.replace(b'\x01', b' | ')
    print(f"{prefix}:")
    print(f"  {readable.decode('ascii', errors='ignore')}")
    print(f"  Длина: {len(data)} байт")

def test_connection():
    """Основной тест подключения"""
    
    print("="*60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ С SIMPLEFIX")
    print("="*60)
    
    print(f"\n📡 Параметры подключения:")
    print(f"   Хост: {HOST}")
    print(f"   Порт: {PORT}")
    print(f"   SenderCompID: {SENDER_COMP_ID}")
    print(f"   TargetCompID: {TARGET_COMP_ID}")
    print(f"   FIX Version: {FIX_VERSION}")
    
    # 1. Создаем сообщение
    print("\n🔧 Создаем Logon сообщение...")
    try:
        msg = create_logon_message()
        encoded_msg = msg.encode()
        print("✅ Сообщение создано успешно")
        print_fix_message(encoded_msg, "📤 Logon сообщение")
    except Exception as e:
        print(f"❌ Ошибка создания сообщения: {e}")
        return False
    
    # 2. Подключаемся к серверу
    print(f"\n🔌 Подключаемся к {HOST}:{PORT}...")
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Таймаут 10 секунд
        sock.connect((HOST, PORT))
        print("✅ Соединение установлено")
    except socket.timeout:
        print("❌ Таймаут подключения! Сервер не отвечает")
        return False
    except ConnectionRefusedError:
        print("❌ Соединение отклонено! Порт закрыт или сервер не слушает")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    
    # 3. Отправляем сообщение
    print("\n📤 Отправляем Logon...")
    try:
        bytes_sent = sock.send(encoded_msg)
        print(f"✅ Отправлено {bytes_sent} байт")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        sock.close()
        return False
    
    # 4. Ждем ответ
    print("\n📥 Ожидание ответа от сервера...")
    try:
        response = sock.recv(4096)
        print(f"✅ Получено {len(response)} байт")
        
        if len(response) == 0:
            print("⚠️ Сервер закрыл соединение без ответа")
            sock.close()
            return False
            
        print_fix_message(response, "📥 Ответ сервера")
        
        # 5. Парсим ответ
        parser = simplefix.FixParser()
        parser.append_buffer(response)
        reply_msg = parser.get_message()
        
        if reply_msg:
            print("\n🔍 Анализ ответа:")
            
            # Получаем тип сообщения
            msg_type = reply_msg.get(35)
            print(f"   MsgType (35): {msg_type}")
            
            if msg_type == 'A':
                print("\n🎉 УСПЕХ! Сервер подтвердил Logon!")
                print("   Подключение работает корректно")
                return True
                
            elif msg_type == '5':
                print("\n⚠️ Сервер отправил Logout")
                print("   Возможные причины:")
                print("   - Неправильный SenderCompID или TargetCompID")
                print("   - Не та версия FIX протокола")
                print("   - Нужен пароль (поле 554)")
                print("   - Неправильный формат времени")
                
                # Пробуем получить текст ошибки
                text = reply_msg.get(58)  # Text поле
                if text:
                    print(f"   Текст ошибки: {text}")
                    
            elif msg_type == '3':
                print("\n⚠️ Ошибка в сообщении (MsgType=3)")
                reason = reply_msg.get(58)
                if reason:
                    print(f"   Причина: {reason}")
                    
            else:
                print(f"\n⚠️ Получен неизвестный тип сообщения: {msg_type}")
        else:
            print("\n⚠️ Не удалось распарсить ответ")
            
    except socket.timeout:
        print("❌ Таймаут ожидания ответа!")
        print("   Сервер не ответил в течение 10 секунд")
    except Exception as e:
        print(f"❌ Ошибка при получении ответа: {e}")
    
    # Закрываем соединение
    sock.close()
    print("\n🔌 Соединение закрыто")
    return False

# Запускаем тест
if __name__ == "__main__":
    success = test_connection()
    
    print("\n" + "="*60)
    if success:
        print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("   simplefix работает корректно")
    else:
        print("❌ ТЕСТ НЕ УДАЛСЯ")
        print("\nРекомендации:")
        print("1. Проверьте IP и порт")
        print("2. Уточните SenderCompID/TargetCompID у банка")
        print("3. Попробуйте другие версии FIX (4.0, 4.1, 4.3, 4.4)")
        print("4. Проверьте, не нужен ли VPN для доступа")
    print("="*60)