#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:winsky
# date:2017-4-26 
import httplib, urllib
import ConfigParser
import json
import logging.handlers
import os
import sys

config_path = "/opt/server_init/dnspod_cnf.ini"
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/json",
           "UserAgent": "server dns Client/1.0.0 (1195413185@qq.com)"}

log_file = "/opt/server_init/logs/dnspod.log"
if not os.path.exists("/opt/server_init/logs"):
    os.makedirs('/opt/server_init/logs')
log_level = logging.DEBUG
logger = logging.getLogger("dnspodLogger")
handler = logging.handlers.RotatingFileHandler(filename=log_file,
                                               maxBytes=10 * 1024 * 1024,
                                               backupCount=5)
formatter = logging.Formatter("[%(asctime)s]%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(log_level)


def log(msg):
    # logger.info(msg)
    print msg


if not os.path.isfile(config_path):
    log("没有配置文件")
    sys.exit(0)


def get_config():
    config = ConfigParser.ConfigParser()
    config.readfp(open(config_path), "rb")
    return config


config_param = get_config()
email = config_param.get("global", "login_email")
password = config_param.get("global", "login_password")
domain = config_param.get("global", "domain")
sub_domain = config_param.get("global", "sub_domain")
sub_domain = sub_domain.lower()

host = "dnsapi.cn"
base_param = dict(
    login_email=email,
    login_password=password,
    format="json",
)


def get_ip():
    """
    # 目标网站挂了,换为访问我们自己的服务器获取ip
    sock = socket.create_connection(('ns1.dnspod.net', 6666))
    sock.settimeout(10)
    ip = sock.recv(16)
    sock.close()
    return ip
    """

    host = "root.dotwintech.com:88"
    url = "http://root.dotwintech.com:88/ip_service/getIP.jsp"
    conn = httplib.HTTPConnection(host)
    conn.request(method="GET", url=url)
    response = conn.getresponse()
    res = response.read()
    return res


def post(uri, param):
    result = {}
    conn = httplib.HTTPSConnection(host)
    conn.request("POST", uri, urllib.urlencode(param), headers)
    response = conn.getresponse()
    result["status"] = response.status
    result["reason"] = response.reason
    data = response.read()
    result["data"] = data
    conn.close()

    return result


def get_domain_id():
    result = None

    uri = "/Domain.List"
    param = base_param
    param.update(dict(keyword=domain))
    resp = post(uri, param)
    resp_status = resp["status"]

    if resp_status != 200:
        reason = resp["reason"]
        log(resp_status + reason)
    else:
        data = json.loads(resp["data"])
        status = data["status"]
        code = status["code"]
        if code != "1":
            log(status["message"])
        else:
            domains = data["domains"]
            for item in domains:
                if item["name"] == domain:
                    result = item["id"]
                    break
    return result


def create_record(self_domain_id):
    uri = "/Record.Create"
    param = base_param
    param.update(dict(domain_id=self_domain_id,
                      sub_domain=sub_domain,
                      record_type=config_param.get("global", "record_type"),
                      record_line=config_param.get("global", "record_line"),
                      value=get_ip()))
    resp = post(uri, param)
    resp_status = resp["status"]
    if resp_status != 200:
        reason = resp["reason"]
        log(resp_status + " " + reason)
    else:
        data = json.loads(resp["data"])
        status = data["status"]
        code = status["code"]
        if code != "1":
            log(code + " " + status["message"])
        else:
            log("创建域名%s.%s成功" % (sub_domain, domain))


def get_record(domain_id):
    result = {}

    uri = "/Record.List"
    param = base_param
    param.update(dict(domain_id=domain_id, keyword=sub_domain))
    resp = post(uri, param)
    resp_status = resp["status"]

    if resp_status != 200:
        reason = resp["reason"]
        log(resp_status + reason)
    else:
        data = json.loads(resp["data"])
        status = data["status"]
        code = status["code"]
        if code != "1":
            pass
        else:
            records = data["records"]
            for item in records:
                if item["name"] == sub_domain:
                    result["id"] = item["id"]
                    result["record_ip"] = item["value"]
                    break
    return result


def update(ip, domain_id, record_id):
    uri = "/Record.Ddns"
    params = base_param
    params.update(dict(
        value=ip,
        domain_id=domain_id,
        record_id=record_id,
        sub_domain=sub_domain,
        record_line="默认"
    ))

    resp = post(uri, params)
    resp_status = resp["status"]
    if resp_status != 200:
        log(resp["reason"])
        log(resp["data"])
        return False
    else:
        return True


def run():
    try:
        domain_id = get_domain_id()
        if domain_id:
            record = get_record(domain_id)
            if len(record) == 2:
                ip = get_ip()
                if ip != record["record_ip"]:
                    res = update(ip, domain_id, record["id"])
                    if res:
                        log("更新%s.%s的IP成功" % (sub_domain, domain))
                else:
                    log("ip没有变化，无需修改")
            else:
                log("没有找到符合条件的记录")
                create_record(domain_id)
        else:
            log("没有找到域名id")
    except Exception, e:
        log(e)
        pass


if __name__ == '__main__':
    run()
