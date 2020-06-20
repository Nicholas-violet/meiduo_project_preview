from celery_tasks.main import celery_app
from celery_tasks.yuntongxun.ccp_sms import CCP


@celery_app.task(name='ccp_send_sms_code')
def ccp_send_sms_code(mobile, sms_code):
    '''该函数就是一个任务, 用于发送短信'''
    result = CCP().send_template_sms(mobile,
                                     [sms_code, 5],
                                     1)
    return result