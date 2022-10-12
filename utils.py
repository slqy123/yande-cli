from subprocess import run

from database import *


# def get_id_from_url(url: str) -> int:
#     res = re.search(r"yande.re%20(\d+)%20", url)
#     return int(res.group(1))
#
#
# def get_id_from_file_name(file_name: str) -> int:
#     assert file_name.startswith('yande')
#     return int(file_name.split(' ')[1])


def check_exists(obj, **kwargs):
    # print(kwargs)
    res = ss.query(obj).filter_by(**kwargs).all()
    if len(res) == 0:
        return False
    if len(res) == 1:
        return res[0]
    raise


# def check_img_change(new_img, exist_img):
#     if not os.path.exists(IMG_PATH + '/' + exist_img):
#         print('file not exists')
#         return True
#     if new_img != exist_img:
#         return True
#     else:
#         return False
#
#
# def process_image(img_name):
#     res = re.sub(r'_[2-9](\.[a-z]+)$', r'\1', img_name)
#     _img = res.rsplit('.', 1)[0].split(' ')[1:]
#     img_id = int(_img[0])
#     img_tags = _img[1:]
#     imgProcessRes = {
#         'id': img_id,
#         'name': res
#     }
#
#     tag_list = []
#     for tag in img_tags:
#         tagRes = check_exists(Tag, name=tag)
#         if tagRes:
#             tag_list.append(tagRes)
#         else:
#             new_tag = Tag(name=tag)
#             tag_list.append(new_tag)
#
#     imgProcessRes['tags'] = tag_list
#     return imgProcessRes
#
#
# def del_exists_link(path: str):
#     with open(path) as f:
#         with open('demo.txt', 'w') as fr:
#             urls = f.read().split('\n')
#             for url in urls:
#                 res = re.search(r"yande.re%20(\d+)%20", url)
#                 checkR = check_exists(Image, id=int(res.group(1)))
#                 if not checkR:
#                     fr.write(url + '\n')
#

def call(command):
    # return os.popen().read()
    result = run(command, check=True, capture_output=True, encoding='utf8')
    return result.stdout


class LazyImport:
    def __init__(self, module_name):
        self.module_name = module_name
        self.module = None

    def __getattr__(self, funcname):
        if self.module is None:
            self.module = __import__(self.module_name)
            print(self.module)
        return getattr(self.module, funcname)