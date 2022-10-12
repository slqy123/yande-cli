from status import DEVICE_AVAILABLE
from database import *
from datetime import date
import inquirer
import re

from settings import ADB_PATH, DEVICE_ID, ROOT
from utils import call


class YandeHistory:
    history_session = ss

    def __init__(self, history: History):
        self.history = history
        self.id = history.id
        self.date = history.date
        self.start = history.start
        self.end = history.end
        self.amount = history.amount
        self.img_star = history.img_star
        self.finish = history.finish

    @classmethod
    def create_new(cls, imgs) -> 'YandeHistory':
        minId = imgs[0].id
        maxId = imgs[-1].id
        length = len(imgs)
        today = date.today()
        min_star = imgs[0].count

        history = History(
            date=today,
            start=minId,
            end=maxId,
            amount=length,
            img_star=min_star
        )
        cls.history_session.add(history)
        cls.history_session.commit()
        # self.folder_name = self.get_folder_name_from_history(self.history)

        return cls(history)

    @classmethod
    def select(cls, history: History = None) -> 'YandeHistory':
        if history is not None:
            return cls(history)

        histories = cls.history_session.query(History).filter(History.finish == False, History.id > 0).all()
        choices = []
        for i, history in enumerate(histories):
            choices.append(f'[{i}]:{cls.get_description_from_history(history)}')

        question = [
            inquirer.List(
                'choice',
                message='which history do you want to pull?',
                choices=choices
            )
        ]
        ans = inquirer.prompt(question)
        index = re.match(r'\[(\d+)', ans['choice']).group(1)
        return cls(histories[int(index)])

    @classmethod
    def get_folder_name_from_history(cls, history) -> str:
        return f'{history.id}-{history.img_star}-{history.amount}-{history.start}-{history.end}'

    @classmethod
    def get_description_from_history(cls, history: History) -> str:
        folder_name = cls.get_folder_name_from_history(history)
        img_num = int(call(f'"{ADB_PATH}" -s {DEVICE_ID} shell \
"cd {ROOT}/{folder_name} && ls -l |grep ^-|wc -l"')) if DEVICE_AVAILABLE else None
        return f"id={history.id},image star = {history.img_star} pushed at {str(history.date)} \
from {history.start} to {history.end}" + ('' if img_num is None else f"({img_num}/{history.amount})")

    @classmethod
    def commit_history(cls, history: History):
        cls.history_session.add(history)
        cls.history_session.commit()

    @classmethod
    def get_all_unfinished_histories(cls):
        return cls.history_session.query(History).filter(History.finish == False).all()

    def get_folder_name(self):
        return self.get_folder_name_from_history(self.history)

    def get_description(self):
        return self.get_description_from_history(self.history)

    def set(self, commit=False, **params):
        for key, value in params.items():
            setattr(self, key, value)
            setattr(self.history, key, value)
        if commit:
            self.commit()

    def commit(self):
        self.commit_history(self.history)

