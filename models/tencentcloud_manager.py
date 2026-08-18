"""Tencent Cloud SDK integration for EvolvixOS.

Provides a unified interface to Tencent Cloud services via the official Python SDK.
Requires TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY env vars.

Supported services:
  - CVM (Cloud Virtual Machine) — server management
  - CDB (Cloud Database MySQL) — database management
  - VPC (Virtual Private Cloud) — networking
  - SSL — certificate management
  - DNSPod — DNS management
  - CDN — content delivery
  - Billing — cost tracking
  - CAM — access management
  - Hunyuan — Tencent LLM
  - ASR — speech recognition
  - AIArt — image generation
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

class TencentCloudManager:
    def __init__(self):
        self.secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID", "")
        self.secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY", "")
        self.region = os.environ.get("TENCENTCLOUD_REGION", "ap-frankfurt")
        self._credential = None
        self._profile = None
        if self.secret_id and self.secret_key:
            try:
                from tencentcloud.common.credential import Credential
                from tencentcloud.common.profile.client_profile import ClientProfile
                from tencentcloud.common.profile.http_profile import HttpProfile
                self._credential = Credential(self.secret_id, self.secret_key)
                hp = HttpProfile()
                hp.endpoint = None
                hp.reqMethod = "POST"
                hp.reqTimeout = 30
                self._profile = ClientProfile()
                self._profile.httpProfile = hp
                self._profile.language = "en-US"
                logger.info("Tencent Cloud credentials loaded")
            except Exception as e:
                logger.error("Failed to init Tencent Cloud: %s", e)

    def is_configured(self):
        return self._credential is not None

    def _get_client(self, service, version, region=None):
        mod_map = {
            ("cvm", "20170312"): "tencentcloud.cvm.v20170312.cvm_client.CvmClient",
            ("cdb", "20170320"): "tencentcloud.cdb.v20170320.cdb_client.CdbClient",
            ("vpc", "20170312"): "tencentcloud.vpc.v20170312.vpc_client.VpcClient",
            ("ssl", "20191205"): "tencentcloud.ssl.v20191205.ssl_client.SslClient",
            ("dnspod", "20210323"): "tencentcloud.dnspod.v20210323.dnspod_client.DnspodClient",
            ("cdn", "20180606"): "tencentcloud.cdn.v20180606.cdn_client.CdnClient",
            ("billing", "20180709"): "tencentcloud.billing.v20180709.billing_client.BillingClient",
            ("cam", "20190116"): "tencentcloud.cam.v20190116.cam_client.CamClient",
            ("hunyuan", "20230901"): "tencentcloud.hunyuan.v20230901.hunyuan_client.HunyuanClient",
            ("asr", "20190614"): "tencentcloud.asr.v20190614.asr_client.AsrClient",
            ("aiart", "20221229"): "tencentcloud.aiart.v20221229.aiart_client.AiartClient",
        }
        key = (service, version)
        if key not in mod_map:
            raise ValueError(f"Unsupported service: {service}/{version}")
        import importlib
        cls_path = mod_map[key]
        parts = cls_path.rsplit(".", 1)
        mod = importlib.import_module(parts[0])
        cls = getattr(mod, parts[1])
        r = region or self.region
        return cls(self._credential, r, self._profile)

    def _call(self, service, version, action, params=None):
        try:
            client = self._get_client(service, version)
            req_mod = __import__(f"tencentcloud.{service}.v{version}.{service}_models", fromlist=[action + "Request"])
            req_cls = getattr(req_mod, action + "Request")
            req = req_cls()
            if params:
                for k, v in params.items():
                    if hasattr(req, k):
                        setattr(req, k, v)
            resp = getattr(client, action)(req)
            return json.loads(resp._deserialize())
        except Exception as e:
            return {"error": str(e)}

    # === CVM ===
    def cvm_describe_instances(self, region=None):
        client = self._get_client("cvm", "20170312", region)
        from tencentcloud.cvm.v20170312.cvm_models import DescribeInstancesRequest
        req = DescribeInstancesRequest()
        resp = client.DescribeInstances(req)
        return json.loads(resp.serialize())

    def cvm_describe_zones(self, region=None):
        client = self._get_client("cvm", "20170312", region)
        from tencentcloud.cvm.v20170312.cvm_models import DescribeZonesRequest
        req = DescribeZonesRequest()
        resp = client.DescribeZones(req)
        return json.loads(resp.serialize())

    def cvm_run_instances(self, zone, instance_type, image_id=None, instance_name="evolvixos-instance", region=None):
        client = self._get_client("cvm", "20170312", region)
        from tencentcloud.cvm.v20170312.cvm_models import RunInstancesRequest
        req = RunInstancesRequest()
        req.InstanceType = instance_type
        req.Placement = {"Zone": zone}
        if image_id:
            req.ImageId = image_id
        req.InstanceName = instance_name
        req.InstanceChargeType = "POSTPAID_BY_HOUR"
        resp = client.RunInstances(req)
        return json.loads(resp.serialize())

    def cvm_start_instances(self, instance_ids, region=None):
        client = self._get_client("cvm", "20170312", region)
        from tencentcloud.cvm.v20170312.cvm_models import StartInstancesRequest
        req = StartInstancesRequest()
        req.InstanceIds = instance_ids
        resp = client.StartInstances(req)
        return json.loads(resp.serialize())

    def cvm_stop_instances(self, instance_ids, region=None):
        client = self._get_client("cvm", "20170312", region)
        from tencentcloud.cvm.v20170312.cvm_models import StopInstancesRequest
        req = StopInstancesRequest()
        req.InstanceIds = instance_ids
        resp = client.StopInstances(req)
        return json.loads(resp.serialize())

    def cvm_reboot_instances(self, instance_ids, region=None):
        client = self._get_client("cvm", "20170312", region)
        from tencentcloud.cvm.v20170312.cvm_models import RebootInstancesRequest
        req = RebootInstancesRequest()
        req.InstanceIds = instance_ids
        resp = client.RebootInstances(req)
        return json.loads(resp.serialize())

    # === Billing ===
    def billing_describe_bill_summary(self, start_month, end_month):
        client = self._get_client("billing", "20180709")
        from tencentcloud.billing.v20180709.billing_models import DescribeBillSummaryRequest
        req = DescribeBillSummaryRequest()
        req.StartMonth = start_month
        req.EndMonth = end_month
        resp = client.DescribeBillSummary(req)
        return json.loads(resp.serialize())

    def billing_describe_account_balance(self):
        client = self._get_client("billing", "20180709")
        from tencentcloud.billing.v20180709.billing_models import DescribeAccountBalanceRequest
        req = DescribeAccountBalanceRequest()
        resp = client.DescribeAccountBalance(req)
        return json.loads(resp.serialize())

    # === SSL ===
    def ssl_describe_certificates(self, limit=100):
        client = self._get_client("ssl", "20191205")
        from tencentcloud.ssl.v20191205.ssl_models import DescribeCertificatesRequest
        req = DescribeCertificatesRequest()
        req.Limit = limit
        resp = client.DescribeCertificates(req)
        return json.loads(resp.serialize())

    # === DNSPod ===
    def dnspod_describe_record_list(self, domain, subdomain=None):
        client = self._get_client("dnspod", "20210323")
        from tencentcloud.dnspod.v20210323.dnspod_models import DescribeRecordListRequest
        req = DescribeRecordListRequest()
        req.Domain = domain
        if subdomain:
            req.SubDomain = subdomain
        resp = client.DescribeRecordList(req)
        return json.loads(resp.serialize())

    def dnspod_describe_domain_list(self):
        client = self._get_client("dnspod", "20210323")
        from tencentcloud.dnspod.v20210323.dnspod_models import DescribeDomainListRequest
        req = DescribeDomainListRequest()
        resp = client.DescribeDomainList(req)
        return json.loads(resp.serialize())

    # === CDN ===
    def cdn_describe_domains(self):
        client = self._get_client("cdn", "20180606")
        from tencentcloud.cdn.v20180606.cdn_models import DescribeDomainsRequest
        req = DescribeDomainsRequest()
        resp = client.DescribeDomains(req)
        return json.loads(resp.serialize())

    # === Hunyuan (Tencent LLM) ===
    def hunyuan_chat(self, messages, model="hunyuan-pro"):
        client = self._get_client("hunyuan", "20230901")
        from tencentcloud.hunyuan.v20230901.hunyuan_models import ChatCompletionsRequest
        req = ChatCompletionsRequest()
        req.Model = model
        req.Messages = messages
        resp = client.ChatCompletions(req)
        return json.loads(resp.serialize())

    # === AIArt ===
    def aiart_text_to_image(self, prompt, styles=None, result_config=None):
        client = self._get_client("aiart", "20221229")
        from tencentcloud.aiart.v20221229.aiart_models import TextToImageRequest
        req = TextToImageRequest()
        req.Prompt = prompt
        if styles:
            req.Styles = styles
        if result_config:
            req.ResultConfig = result_config
        resp = client.TextToImage(req)
        return json.loads(resp.serialize())

    # === VPC ===
    def vpc_describe_vpcs(self, region=None):
        client = self._get_client("vpc", "20170312", region)
        from tencentcloud.vpc.v20170312.vpc_models import DescribeVpcsRequest
        req = DescribeVpcsRequest()
        resp = client.DescribeVpcs(req)
        return json.loads(resp.serialize())

    def vpc_describe_security_groups(self, region=None):
        client = self._get_client("vpc", "20170312", region)
        from tencentcloud.vpc.v20170312.vpc_models import DescribeSecurityGroupsRequest
        req = DescribeSecurityGroupsRequest()
        resp = client.DescribeSecurityGroups(req)
        return json.loads(resp.serialize())

    # === CAM ===
    def cam_list_users(self):
        client = self._get_client("cam", "20190116")
        from tencentcloud.cam.v20190116.cam_models import ListUsersRequest
        req = ListUsersRequest()
        resp = client.ListUsers(req)
        return json.loads(resp.serialize())

    # === CDB ===
    def cdb_describe_instances(self, region=None):
        client = self._get_client("cdb", "20170320", region)
        from tencentcloud.cdb.v20170320.cdb_models import DescribeDBInstancesRequest
        req = DescribeDBInstancesRequest()
        resp = client.DescribeDBInstances(req)
        return json.loads(resp.serialize())

    def list_services(self):
        """Return all available services."""
        return {
            "cvm": ["describe_instances", "describe_zones", "run_instances", "start_instances", "stop_instances", "reboot_instances"],
            "cdb": ["describe_instances"],
            "vpc": ["describe_vpcs", "describe_security_groups"],
            "ssl": ["describe_certificates"],
            "dnspod": ["describe_record_list", "describe_domain_list"],
            "cdn": ["describe_domains"],
            "billing": ["describe_bill_summary", "describe_account_balance"],
            "cam": ["list_users"],
            "hunyuan": ["chat"],
            "aiart": ["text_to_image"],
        }


if __name__ == "__main__":
    tc = TencentCloudManager()
    if tc.is_configured():
        print("Tencent Cloud configured, region:", tc.region)
        print("Services:", json.dumps(tc.list_services(), indent=2))
    else:
        print("Not configured. Set TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY env vars.")
