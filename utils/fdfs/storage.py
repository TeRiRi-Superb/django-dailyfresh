from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client


class FDFSStorage(Storage):
    '''fast dfs 文件存储类'''

    def __init__(self, base_client=None, base_url=None):

        if base_client is None:
            base_client = settings.FDFS_CLIENT_CONF
        self.base_client = base_client
        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def open(self, name, mode='rb'):
        '''打开文件时使用'''
        pass

    def save(self, name, content, max_length=None):
        '''name: 上传文件的文件名
           content: 将会成为 File 对象自身。
        '''
        client = Fdfs_client(self.base_client)

        # 根据文件名上传文件
        # client.upload_by_filename()
        res = client.upload_by_buffer(content.read())  # 根据文件内容上传

        # @return dict 上传成功时，返回的字典格式
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id, 文件内容id
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # } if success else None

        # 判断上传的状态 成功就继续执行
        if res.get('Status') != 'Upload successed.':
            raise Exception('上传文件失败')

        # 得到保存的文件内容id
        filename = res.get('Remote file_id')

        return filename

    def exists(self, name):
        '''
            False:没有这个文件名， 代表是新的可以文件名
            True： 已经存在这个文件名，不是可用的新文件名
            Django 判断文件名是否是新的可用的 ，但我的文件是保存在fastdfs里 所以一直是可用的
        '''

        return False

    def url(self, name):
        # 返回文件内容id
        return self.base_url + name
