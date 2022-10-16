from yandecli.status import ADB_AVAILABLE
from yandecli.tools.file_io import get_device_by_platform
from database import *
from datetime import date
import re


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
        self.platform = history.platform

    @classmethod
    def create_new(cls, imgs, platform: PLATFORM) -> 'YandeHistory':
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
            img_star=min_star,
            platform=platform
        )
        cls.history_session.add(history)
        cls.history_session.commit()
        # self.folder_name = self.get_folder_name_from_history(self.history)

        return cls(history)

    @classmethod
    def select(cls, history: History = None) -> 'YandeHistory':
        if history is not None:
            return cls(history)

        histories = cls.get_all_unfinished_histories()
        choices = []
        for i, history in enumerate(histories):
            choices.append(f'[{i}]:{cls.get_description_from_history(history)}')

        import inquirer
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
        DEVICE = get_device_by_platform(history.platform)

#         img_num = int(call(f'"{ADB_PATH}" -s {DEVICE_ID} shell \
# "cd {ADB_ROOT}/{folder_name} && ls -l |grep ^-|wc -l"')) if ADB_AVAILABLE else None
        img_num = None if ((not ADB_AVAILABLE) and DEVICE.platform == PLATFORM.MOBILE) else len(DEVICE(folder_name).listdir())
        return f"id={history.id},image star = {history.img_star} pushed at {str(history.date)} \
from {history.start} to {history.end} on {history.platform.value}" + ('' if img_num is None else f"({img_num}/{history.amount})")

    @classmethod
    def commit_history(cls, history: History):
        cls.history_session.add(history)
        cls.history_session.commit()

    @classmethod
    def get_all_unfinished_histories(cls):
        if not ADB_AVAILABLE:
            return cls.history_session.query(History).filter(History.finish == False, History.platform == PLATFORM.PC).all()
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

