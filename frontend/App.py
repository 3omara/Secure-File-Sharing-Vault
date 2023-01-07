import os
from ftplib import FTP
from ttkthemes import ThemedTk
from dataclasses import dataclass
import socketio as sio

from ciphers.AESCipher import AESCipher
from ciphers.DESCipher import DESCipher
from ciphers.BlowfishCipher import BlowfishCipher
from ciphers.FileCipher import FileCipher
from repositories.FileReferencesRepository import FileReferencesRepository
from services.FileReferencesService import FileReferencesService
from services.SecureFTPService import SecureFTPService


@dataclass(frozen=True)
class Subjects:
    explorer: FileReferencesService


class App:
    def __init__(self):
        self.__sio_client = sio.Client()
        self.__file_references_repository = FileReferencesRepository(
            self.__sio_client
        )
        self.file_references_service = FileReferencesService(
            self.__file_references_repository
        )
        self.ftp_service = SecureFTPService(
            ftp=FTP(),
            cipher=FileCipher(
                [AESCipher(), DESCipher(), BlowfishCipher()]
            ),
            master_cipher=FileCipher(
                [AESCipher()]
            ),
            file_references_repository=self.__file_references_repository
        )
        self.ftp_service.connect(
            host=os.getenv("FTP_HOST"),
            port=int(os.getenv("FTP_PORT")),
        )
        self.ftp_service.login(
            user=os.getenv("FTP_USER"),
            passwd=os.getenv("FTP_PASSWD")
        )
        self.subjects: Subjects = Subjects(
            explorer=self.file_references_service
        )

    def run(self):
        self.setup_window()
        self.window.mainloop()

    def setup_window(self):
        self.width = 1000
        self.height = 600
        self.window = ThemedTk(theme="arc")
        self.window.title("Vault")
        self.window.geometry(f"{self.width}x{self.height}")
        self.window.resizable(False, False)
        from views.MainView import MainView
        MainView(self.window).build(self)