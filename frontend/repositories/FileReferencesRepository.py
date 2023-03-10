import os
from typing import List
import socketio as sio
from database.Database import Database
from shared.ObserverPattern import Subject
from models.FileReference import FileReference


class FileReferencesRepository(Subject):
    SIO_NAMESPACE = "/file_references"

    def __init__(self, client: sio.Client, local_db: Database):
        super().__init__()
        self.client = client
        self.local_db = local_db
        self.__file_references = []
        self.client.on("init_file_references",
                       self.__on_init_file_references,
                       namespace=self.SIO_NAMESPACE)
        self.client.on("new_file_reference",
                       self.__on_new_file_reference,
                       namespace=self.SIO_NAMESPACE)
        self.client.on("delete_file_reference",
                       self.__on_delete_file_reference,
                       namespace=self.SIO_NAMESPACE)
        self.client.connect(
            os.getenv("SIO_HOST"),
            transports=["polling", "websocket"],
            namespaces=[self.SIO_NAMESPACE]
        )

    @property
    def file_references(self):
        return [*self.__file_references]

    @file_references.setter
    def file_references(self, file_references: List[FileReference]):
        self.__file_references = file_references
        self.notify_observers()

    def insert(self, file: FileReference, master_key: bytes):
        def on_uploaded(response):
            new_file_reference = FileReference.from_response(response["data"])
            self.file_references = [*self.__file_references,
                                    new_file_reference]
            self.local_db.insert_master_key(new_file_reference.id,
                                            file.name,
                                            master_key,)

        self.client.emit("new_file_reference",
                         file.to_response(),
                         callback=on_uploaded,
                         namespace=self.SIO_NAMESPACE)

    def __on_init_file_references(self, response):
        self.file_references = [FileReference.from_response(file)
                                for file in response["data"]]

    def __on_new_file_reference(self, response):
        self.file_references = [*self.__file_references,
                                FileReference.from_response(response["data"])]

    def __on_delete_file_reference(self, response):
        self.file_references = [file for file in self.__file_references
                                if file.id != response["data"]["id"]]
