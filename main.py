import sys
import locale
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                            QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QFrame)
from PyQt6.QtCore import Qt
from wakeonlan import send_magic_packet
import json
import os
from PyQt6.QtGui import QIcon

# Uygulama sürümü
APP_VERSION = "v1.1"
APP_NAME = f"WOL Manager {APP_VERSION}"
APP_COMPANY = "by WebAdhere Technologies"

def resource_path(relative_path):
    """ PyInstaller için kaynak dosya yolunu alır """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WakeOnLANApp(QMainWindow):
    def __init__(self, system_dark_mode=False, system_language="en"):
        super().__init__()
        # Sistem ayarlarını sakla
        self._system_dark_mode = system_dark_mode
        self._system_language = system_language
        
        # Varsayılan değerleri ayarla
        self.dark_mode = system_dark_mode  # Başlangıçta sistem temasını kullan
        self.current_language = system_language
        
        # Cihazları yükle
        self.devices = self.load_devices()
        
        # İkon yolu
        icon_path = resource_path('pwr.png')
        self.app_icon = QIcon(icon_path)
        self.setWindowIcon(self.app_icon)
        
        # UI'ı başlat
        self.init_ui()
        
        # Stili yükle
        self.load_style()
        
        # Tema combobox'ını güncelle
        self.update_theme_combo()
        
        # Kaydedilmiş ayarları yükle ve uygula
        self._load_and_apply_settings()

    def _load_and_apply_settings(self):
        try:
            settings_path = os.path.join(os.path.expanduser('~'), 'wake_on_lan_settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Tema ayarını uygula
                    if 'dark_mode' in settings:
                        self.dark_mode = settings['dark_mode']
                        self.load_style()
                        self.update_theme_combo()
                    # Dil ayarını uygula
                    if 'language' in settings:
                        self.current_language = settings.get('language', self._system_language)
            else:
                # İlk kez çalıştırılıyorsa sistem ayarlarını kaydet
                self._save_settings()
        except Exception as e:
            print(f"Ayarlar yüklenirken hata: {e}")
            self.dark_mode = self._system_dark_mode
            self.current_language = self._system_language
            self._save_settings()
        
        # Dil indeksini ayarla
        lang_index_map = {
            "tr": 0,
            "en": 1,
            "de": 2,
            "fr": 3,
            "it": 4,
            "ru": 5
        }
        
        # Dil ayarını uygula
        self.language_combo.setCurrentIndex(lang_index_map.get(self.current_language, 1))
        self.retranslate_ui()

    def _save_settings(self):
        try:
            settings_path = os.path.join(os.path.expanduser('~'), 'wake_on_lan_settings.json')
            settings = {
                'dark_mode': self.dark_mode,
                'language': self.current_language
            }
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ayarlar kaydedilirken hata: {e}")

    def init_ui(self):
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(600, 450)  # Minimum boyutu artır
        self.setMaximumSize(1000, 750)  # Maximum boyutu artır
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Sonuç etiketi
        self.result_label = QLabel("")
        
        # Üst menü
        top_menu = QHBoxLayout()
        
        # Dil seçimi
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Türkçe", "English", "Deutsch", "Français", "Italiano", "Русский"])
        self.language_combo.setFixedWidth(120)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        
        # Tema seçimi
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(120)
        self.theme_combo.currentIndexChanged.connect(self.toggle_theme)
        
        top_menu.addWidget(self.language_combo)
        top_menu.addWidget(self.theme_combo)
        top_menu.addStretch()
        
        layout.addLayout(top_menu)
        
        # Cihaz ekleme formu
        form_layout = QHBoxLayout()
        
        self.device_name = QLineEdit()
        self.device_name.setPlaceholderText(self.tr("Cihaz Adı"))
        self.device_name.setObjectName("input_field")  # Stil için ID ekle
        
        self.mac_address = QLineEdit()
        self.mac_address.setMinimumWidth(150)
        self.mac_address.setPlaceholderText("XX:XX:XX:XX:XX:XX")
        self.mac_address.setObjectName("input_field")  # Stil için ID ekle
        
        self.add_button = QPushButton(self.tr("Ekle"))
        self.add_button.setFixedWidth(100)
        self.add_button.setObjectName("add_button")  # Stil için ID ekle
        self.add_button.clicked.connect(self.add_device)
        
        form_layout.addWidget(self.device_name, 1)
        form_layout.addWidget(self.mac_address, 1)
        form_layout.addWidget(self.add_button)
        
        layout.addLayout(form_layout)
        
        # Cihaz tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            self.tr("Cihaz Adı"),
            self.tr("MAC Adresi"),
            self.tr("İşlem"),
            self.tr("Sil")
        ])
        
        # Tablo ayarları
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 50)
        
        # Satır numaralarını gizle
        self.table.verticalHeader().setVisible(False)
        
        # Sıralama özelliğini etkinleştir
        self.table.setSortingEnabled(True)
        
        self.update_device_table()
        layout.addWidget(self.table)
        
        # Alt bilgi bölümü
        bottom_info = QHBoxLayout()
        
        # Ayraç çizgisi
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Sürüm ve firma bilgisi
        self.version_label = QLabel()  # Boş oluştur, metin retranslate_ui'da ayarlanacak
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.version_label.setStyleSheet("color: #666666;")
        self.version_label.setOpenExternalLinks(True)  # Dış linkleri açmayı etkinleştir
        
        version_label = QLabel(f"Wake-On-Lan Manager {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_label.setStyleSheet("color: #666666;")
        
        bottom_info.addWidget(self.version_label)
        bottom_info.addStretch()
        bottom_info.addWidget(version_label)
        
        layout.addLayout(bottom_info)
        layout.addWidget(self.result_label)

    def load_devices(self):
        try:
            devices_path = os.path.join(os.path.expanduser('~'), 'wake_on_lan_devices.json')
            if os.path.exists(devices_path):
                with open(devices_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_devices(self):
        try:
            devices_path = os.path.join(os.path.expanduser('~'), 'wake_on_lan_devices.json')
            with open(devices_path, 'w') as f:
                json.dump(self.devices, f)
        except:
            self.result_label.setText(self.tr("Cihaz listesi kaydedilemedi!"))

    def add_device(self):
        name = self.device_name.text()
        mac = self.mac_address.text()
        
        if name and mac:
            self.devices.append({
                "name": name,
                "mac": mac
            })
            self.save_devices()
            self.update_device_table()
            self.device_name.clear()
            self.mac_address.clear()

    def update_device_table(self):
        try:
            self.table.setRowCount(len(self.devices))
            try:
                self.table.itemChanged.disconnect(self.save_device_changes)
            except:
                pass
        except:
            pass
        
        # Cihazları isme göre sırala
        self.devices.sort(key=lambda x: x.get("name", "").lower())
        
        # Dil çevirilerini al
        translations = {
            "tr": {
                "wake": "Uyandır",
                "delete": "❌"
            },
            "en": {
                "wake": "Wake",
                "delete": "❌"
            },
            "de": {
                "wake": "Aufwecken",
                "delete": "❌"
            },
            "fr": {
                "wake": "Réveiller",
                "delete": "❌"
            },
            "it": {
                "wake": "Sveglia",
                "delete": "❌"
            },
            "ru": {
                "wake": "Разбудить",
                "delete": "❌"
            }
        }
        
        # Mevcut dil için çevirileri al
        t = translations.get(self.current_language, translations["en"])
        
        for i, device in enumerate(self.devices):
            try:
                name_item = QTableWidgetItem(device.get("name", ""))
                name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
                
                mac_item = QTableWidgetItem(device.get("mac", ""))
                
                # Uyandır butonu
                wake_button = QPushButton(t["wake"])
                wake_button.clicked.connect(lambda checked, mac=device.get("mac", ""): self.wake_device(mac))
                
                # Sil butonu
                delete_button = QPushButton(t["delete"])
                delete_button.setStyleSheet("color: red;")
                delete_button.clicked.connect(lambda checked, idx=i: self.delete_device(idx))
                
                self.table.setItem(i, 0, name_item)
                self.table.setItem(i, 1, mac_item)
                self.table.setCellWidget(i, 2, wake_button)
                self.table.setCellWidget(i, 3, delete_button)
            except:
                continue
        
        try:
            self.table.itemChanged.connect(self.save_device_changes)
        except:
            pass

    def delete_device(self, index):
        # Dil çevirilerini al
        translations = {
            "tr": {
                "deleted": "Cihaz silindi",
                "error": "Silme hatası!"
            },
            "en": {
                "deleted": "Device deleted",
                "error": "Delete error!"
            },
            "de": {
                "deleted": "Gerät gelöscht",
                "error": "Löschungsfehler!"
            },
            "fr": {
                "deleted": "Appareil supprimé",
                "error": "Erreur de suppression!"
            },
            "it": {
                "deleted": "Dispositivo eliminato",
                "error": "Errore di eliminazione!"
            },
            "ru": {
                "deleted": "Устройство удалено",
                "error": "Ошибка удаления!"
            }
        }
        
        # Mevcut dil için çevirileri al
        t = translations.get(self.current_language, translations["en"])
        
        try:
            if 0 <= index < len(self.devices):
                del self.devices[index]
                self.save_devices()
                self.update_device_table()
                self.result_label.setText(t["deleted"])
        except:
            self.result_label.setText(t["error"])

    def save_device_changes(self, item):
        try:
            if item.column() == 0:  # Sadece isim değişikliklerini kaydet
                row = item.row()
                if row < len(self.devices):
                    self.devices[row]["name"] = item.text()
                    self.save_devices()
        except:
            pass

    def wake_device(self, mac):
        # Dil çevirilerini al
        translations = {
            "tr": {
                "invalid_mac": "Geçersiz MAC adresi!",
                "sent": "Magic packet gönderildi!",
                "error": "Hata oluştu!"
            },
            "en": {
                "invalid_mac": "Invalid MAC address!",
                "sent": "Magic packet sent!",
                "error": "Error occurred!"
            },
            "de": {
                "invalid_mac": "Ungültige MAC-Adresse!",
                "sent": "Magic Packet gesendet!",
                "error": "Fehler aufgetreten!"
            },
            "fr": {
                "invalid_mac": "Adresse MAC invalide!",
                "sent": "Paquet magique envoyé!",
                "error": "Erreur survenue!"
            },
            "it": {
                "invalid_mac": "Indirizzo MAC non valido!",
                "sent": "Magic packet inviato!",
                "error": "Errore!"
            },
            "ru": {
                "invalid_mac": "Неверный MAC-адрес!",
                "sent": "Magic packet отправлен!",
                "error": "Произошла ошибка!"
            }
        }
        
        # Mevcut dil için çevirileri al
        t = translations.get(self.current_language, translations["en"])
        
        if not mac:
            self.result_label.setText(t["invalid_mac"])
            return
            
        try:
            send_magic_packet(mac)
            self.result_label.setText(t["sent"])
        except:
            self.result_label.setText(t["error"])

    def toggle_theme(self, index):
        self.dark_mode = index == 1  # 1 = Dark mode
        self.load_style()
        self._save_settings()

    def update_theme_combo(self):
        current_index = 1 if self.dark_mode else 0
        self.theme_combo.clear()
        self.theme_combo.addItems([self.tr("Aydınlık"), self.tr("Karanlık")])
        self.theme_combo.setCurrentIndex(current_index)

    def load_style(self):
        if self.dark_mode:
            style = """
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #444444;
                border: none;
                padding: 5px;
                color: white;
            }
            QLineEdit#input_field {
                background-color: #3b3b3b;
                border: 1px solid #555555;
                border-radius: 3px;
                color: white;
                padding: 5px;
            }
            QTableWidget {
                background-color: #2b2b2b;
                color: white;
                gridline-color: #555555;
            }
            QTableWidget QHeaderView::section {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555555;
            }
            QTableWidget::item {
                color: white;
            }
            QFrame {
                color: #555555;
            }
            QLabel {
                color: #ffffff;
            }
            QComboBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: white;
                selection-background-color: #555555;
            }
            QPushButton#add_button {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            """
        else:
            style = """
            QMainWindow, QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: none;
                padding: 5px;
                color: #000000;
            }
            QLineEdit#input_field {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
                color: #000000;
                padding: 5px;
            }
            QTableWidget {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #cccccc;
            }
            QTableWidget QHeaderView::section {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QTableWidget::item {
                color: #000000;
            }
            QFrame {
                color: #cccccc;
            }
            QLabel {
                color: #000000;
            }
            QComboBox {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #e0e0e0;
            }
            QPushButton#add_button {
                background-color: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
            """
        
        self.setStyleSheet(style)

    def change_language(self, index):
        lang_map = {
            0: "tr",    # Türkçe
            1: "en",    # English
            2: "de",    # Deutsch
            3: "fr",    # Français
            4: "it",    # Italiano
            5: "ru"     # Русский
        }
        self.current_language = lang_map.get(index, "en")
        self.retranslate_ui()
        self.update_device_table()  # Tabloyu güncelle
        self._save_settings()

    def retranslate_ui(self):
        translations = {
            "tr": {
                "title": APP_NAME,
                "device_name": "Cihaz Adı",
                "mac_address": "MAC Adresi",
                "add": "Ekle",
                "error": "Hata oluştu!",
                "sent": "Magic packet gönderildi!",
                "deleted": "Cihaz silindi",
                "delete": "Sil",
                "delete_error": "Silme hatası!",
                "invalid_mac": "Geçersiz MAC adresi!",
                "light": "Aydınlık",
                "dark": "Karanlık",
                "wake": "Uyandır",
                "action": "İşlem",
                "company": "<a href='https://webadhere.com' style='color: #666666; text-decoration: none;'>WebAdHere</a> Yazılım"
            },
            "en": {
                "title": APP_NAME,
                "device_name": "Device Name",
                "mac_address": "MAC Address",
                "add": "Add",
                "error": "Error occurred!",
                "sent": "Magic packet sent!",
                "deleted": "Device deleted",
                "delete": "Delete",
                "delete_error": "Delete error!",
                "invalid_mac": "Invalid MAC address!",
                "light": "Light",
                "dark": "Dark",
                "wake": "Wake",
                "action": "Action",
                "company": "<a href='https://webadhere.com' style='color: #666666; text-decoration: none;'>WebAdHere</a> Software"
            },
            "de": {
                "title": APP_NAME,
                "device_name": "Gerätename",
                "mac_address": "MAC-Adresse",
                "add": "Hinzufügen",
                "error": "Fehler aufgetreten!",
                "sent": "Magic Packet gesendet!",
                "deleted": "Gerät gelöscht",
                "delete": "Löschen",
                "delete_error": "Löschungsfehler!",
                "invalid_mac": "Ungültige MAC-Adresse!",
                "light": "Hell",
                "dark": "Dunkel",
                "wake": "Aufwecken",
                "action": "Aktion",
                "company": "<a href='https://webadhere.com' style='color: #666666; text-decoration: none;'>WebAdHere</a> Software"
            },
            "fr": {
                "title": APP_NAME,
                "device_name": "Nom de l'appareil",
                "mac_address": "Adresse MAC",
                "add": "Ajouter",
                "error": "Erreur survenue!",
                "sent": "Paquet magique envoyé!",
                "deleted": "Appareil supprimé",
                "delete": "Supprimer",
                "delete_error": "Erreur de suppression!",
                "invalid_mac": "Adresse MAC invalide!",
                "light": "Clair",
                "dark": "Sombre",
                "wake": "Réveiller",
                "action": "Action",
                "company": "<a href='https://webadhere.com' style='color: #666666; text-decoration: none;'>WebAdHere</a> Logiciel"
            },
            "it": {
                "title": APP_NAME,
                "device_name": "Nome dispositivo",
                "mac_address": "Indirizzo MAC",
                "add": "Aggiungi",
                "error": "Errore!",
                "sent": "Magic packet inviato!",
                "deleted": "Dispositivo eliminato",
                "delete": "Elimina",
                "delete_error": "Errore di eliminazione!",
                "invalid_mac": "Indirizzo MAC non valido!",
                "light": "Chiaro",
                "dark": "Scuro",
                "wake": "Sveglia",
                "action": "Azione",
                "company": "<a href='https://webadhere.com' style='color: #666666; text-decoration: none;'>WebAdHere</a> Software"
            },
            "ru": {
                "title": APP_NAME,
                "device_name": "Имя устройства",
                "mac_address": "MAC-адрес",
                "add": "Добавить",
                "error": "Произошла ошибка!",
                "sent": "Magic packet отправлен!",
                "deleted": "Устройство удалено",
                "delete": "Удалить",
                "delete_error": "Ошибка удаления!",
                "invalid_mac": "Неверный MAC-адрес!",
                "light": "Светлая",
                "dark": "Темная",
                "wake": "Разбудить",
                "action": "Действие",
                "company": "<a href='https://webadhere.com' style='color: #666666; text-decoration: none;'>WebAdHere</a> Программное"
            }
        }
        
        t = translations[self.current_language]
        
        self.setWindowTitle(t["title"])
        self.device_name.setPlaceholderText(t["device_name"])
        self.mac_address.setPlaceholderText(t["mac_address"])
        self.add_button.setText(t["add"])
        
        # Tablo başlıklarını güncelle
        headers = [t["device_name"], t["mac_address"], t["action"], t["delete"]]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Sütun genişliklerini dile göre ayarla
        column_widths = {
            "tr": {"mac": 150, "action": 80, "delete": 50},
            "en": {"mac": 150, "action": 80, "delete": 80},
            "de": {"mac": 150, "action": 90, "delete": 90},
            "fr": {"mac": 150, "action": 90, "delete": 100},
            "it": {"mac": 150, "action": 80, "delete": 80},
            "ru": {"mac": 150, "action": 110, "delete": 90}
        }
        
        widths = column_widths.get(self.current_language, column_widths["en"])
        self.table.setColumnWidth(1, widths["mac"])
        self.table.setColumnWidth(2, widths["action"])
        self.table.setColumnWidth(3, widths["delete"])
        
        # Tema seçeneklerini güncelle (mevcut seçimi koru)
        current_theme = self.theme_combo.currentIndex()
        self.theme_combo.clear()
        self.theme_combo.addItems([t["light"], t["dark"]])
        self.theme_combo.setCurrentIndex(current_theme)
        
        # Alt bilgiyi güncelle
        self.version_label.setText(t["company"])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Sistem temasını al
    system_dark_mode = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    print(f"Sistem teması: {'Dark' if system_dark_mode else 'Light'}")
    
    # Sistem dilini al
    system_locale = locale.getdefaultlocale()[0].lower()
    system_language = "en"  # Varsayılan
    
    # Sistem diline göre varsayılan dili belirle
    lang_map = {
        "tr": "tr",
        "en": "en",
        "de": "de",
        "fr": "fr",
        "it": "it",
        "ru": "ru"
    }
    
    for lang_code in lang_map:
        if system_locale.startswith(lang_code):
            system_language = lang_map[lang_code]
            break
    
    print(f"Sistem dili: {system_language}")
    
    # Ayarlar dosyası yolu
    settings_path = os.path.join(os.path.expanduser('~'), 'wake_on_lan_settings.json')
    
    # Kaydedilmiş ayarları kontrol et
    saved_settings = None
    try:
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                # Eğer dark_mode ayarı yoksa sistem temasını kullan
                if 'dark_mode' not in saved_settings:
                    saved_settings['dark_mode'] = system_dark_mode
    except Exception as e:
        print(f"Ayarlar yüklenirken hata: {e}")
        saved_settings = None
    
    # Eğer kaydedilmiş ayar yoksa sistem ayarlarını kullan
    if not saved_settings:
        saved_settings = {
            'dark_mode': system_dark_mode,
            'language': system_language
        }
        # Sistem ayarlarını kaydet
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(saved_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ayarlar kaydedilirken hata: {e}")
    
    # Ana pencereyi oluştur
    window = WakeOnLANApp(
        system_dark_mode=system_dark_mode,  # Her zaman sistem temasını gönder
        system_language=saved_settings.get('language', system_language)
    )
    
    # Pencereyi göster
    window.show()
    
    # Eğer kaydedilmiş tema ayarı varsa, onu uygula
    if saved_settings and 'dark_mode' in saved_settings:
        window.dark_mode = saved_settings['dark_mode']
        window.load_style()
        window.update_theme_combo()
    
    sys.exit(app.exec()) 