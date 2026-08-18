package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strconv"

	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common"
	"github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/common/profile"

	cvm "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/cvm/v20170312"
	vpc "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/vpc/v20170312"
	ssl "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/ssl/v20191205"
	dnspod "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/dnspod/v20210323"
	billing "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/billing/v20180709"
	hunyuan "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/hunyuan/v20230901"
	aiart "github.com/tencentcloud/tencentcloud-sdk-go/tencentcloud/aiart/v20221229"
)

func getCredential() *common.Credential {
	id := os.Getenv("TENCENTCLOUD_SECRET_ID")
	key := os.Getenv("TENCENTCLOUD_SECRET_KEY")
	if id == "" || key == "" {
		fmt.Fprintf(os.Stderr, "Error: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY required\n")
		os.Exit(1)
	}
	return common.NewCredential(id, key)
}

func newProfile() *profile.ClientProfile {
	pf := profile.NewClientProfile()
	pf.Language = "en-US"
	return pf
}

func outputJSON(v interface{}) {
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		fmt.Printf(`{"error": "%s"}`, err.Error())
		return
	}
	fmt.Println(string(b))
}

func main() {
	service := flag.String("service", "", "Tencent Cloud service")
	action := flag.String("action", "", "Action to perform")
	region := flag.String("region", "ap-frankfurt", "Tencent Cloud region")
	paramsJSON := flag.String("params", "{}", "JSON parameters")
	listServices := flag.Bool("list-services", false, "List available services")
	flag.Parse()

	if *listServices {
		outputJSON(map[string][]string{
			"cvm":     {"describe_instances", "describe_zones", "start_instances", "stop_instances", "reboot_instances"},
			"vpc":     {"describe_vpcs", "describe_security_groups"},
			"ssl":     {"describe_certificates"},
			"dnspod":  {"describe_record_list", "describe_domain_list"},
			"billing": {"describe_account_balance", "describe_bill_summary"},
			"hunyuan": {"chat"},
			"aiart":   {"query_text_to_image_job"},
		})
		return
	}

	if *service == "" || *action == "" {
		fmt.Fprintln(os.Stderr, "Usage: tccli --service <svc> --action <act> [--region <reg>] [--params <json>]")
		os.Exit(1)
	}

	cred := getCredential()
	pf := newProfile()

	var params map[string]interface{}
	if err := json.Unmarshal([]byte(*paramsJSON), &params); err != nil {
		params = map[string]interface{}{}
	}

	switch *service {
	case "cvm":
		handleCVM(cred, pf, *region, *action, params)
	case "vpc":
		handleVPC(cred, pf, *region, *action, params)
	case "ssl":
		handleSSL(cred, pf, *region, *action, params)
	case "dnspod":
		handleDNSPod(cred, pf, *region, *action, params)
	case "billing":
		handleBilling(cred, pf, *region, *action, params)
	case "hunyuan":
		handleHunyuan(cred, pf, *region, *action, params)
	case "aiart":
		handleAIArt(cred, pf, *region, *action, params)
	default:
		fmt.Printf(`{"error": "unknown service: %s"}`, *service)
	}
}

func handleCVM(cred *common.Credential, pf *profile.ClientProfile, region, action string, params map[string]interface{}) {
	client, _ := cvm.NewClient(cred, region, pf)
	switch action {
	case "describe_instances":
		req := cvm.NewDescribeInstancesRequest()
		resp, err := client.DescribeInstances(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	case "describe_zones":
		req := cvm.NewDescribeZonesRequest()
		resp, err := client.DescribeZones(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	case "start_instances":
		req := cvm.NewStartInstancesRequest()
		if ids, ok := params["instance_ids"].([]interface{}); ok {
			for _, id := range ids {
				req.InstanceIds = append(req.InstanceIds, common.StringPtr(id.(string)))
			}
		}
		resp, err := client.StartInstances(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	case "stop_instances":
		req := cvm.NewStopInstancesRequest()
		if ids, ok := params["instance_ids"].([]interface{}); ok {
			for _, id := range ids {
				req.InstanceIds = append(req.InstanceIds, common.StringPtr(id.(string)))
			}
		}
		resp, err := client.StopInstances(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	case "reboot_instances":
		req := cvm.NewRebootInstancesRequest()
		if ids, ok := params["instance_ids"].([]interface{}); ok {
			for _, id := range ids {
				req.InstanceIds = append(req.InstanceIds, common.StringPtr(id.(string)))
			}
		}
		resp, err := client.RebootInstances(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	default:
		fmt.Printf(`{"error": "unknown cvm action: %s"}`, action)
	}
}

func handleVPC(cred *common.Credential, pf *profile.ClientProfile, region, action string, params map[string]interface{}) {
	client, _ := vpc.NewClient(cred, region, pf)
	switch action {
	case "describe_vpcs":
		req := vpc.NewDescribeVpcsRequest()
		resp, err := client.DescribeVpcs(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	case "describe_security_groups":
		req := vpc.NewDescribeSecurityGroupsRequest()
		resp, err := client.DescribeSecurityGroups(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	default:
		fmt.Printf(`{"error": "unknown vpc action: %s"}`, action)
	}
}

func handleSSL(cred *common.Credential, pf *profile.ClientProfile, region, action string, params map[string]interface{}) {
	client, _ := ssl.NewClient(cred, region, pf)
	switch action {
	case "describe_certificates":
		req := ssl.NewDescribeCertificatesRequest()
		if limit, ok := params["limit"]; ok {
			if l, err := strconv.ParseUint(fmt.Sprintf("%v", limit), 10, 64); err == nil {
				req.Limit = common.Uint64Ptr(l)
			}
		}
		resp, err := client.DescribeCertificates(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	default:
		fmt.Printf(`{"error": "unknown ssl action: %s"}`, action)
	}
}

func handleDNSPod(cred *common.Credential, pf *profile.ClientProfile, region, action string, params map[string]interface{}) {
	client, _ := dnspod.NewClient(cred, region, pf)
	switch action {
	case "describe_domain_list":
		req := dnspod.NewDescribeDomainListRequest()
		resp, err := client.DescribeDomainList(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	case "describe_record_list":
		req := dnspod.NewDescribeRecordListRequest()
		if d, ok := params["domain"].(string); ok {
			req.Domain = common.StringPtr(d)
		}
		resp, err := client.DescribeRecordList(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	default:
		fmt.Printf(`{"error": "unknown dnspod action: %s"}`, action)
	}
}

func handleBilling(cred *common.Credential, pf *profile.ClientProfile, region, action string, params map[string]interface{}) {
	client, _ := billing.NewClient(cred, region, pf)
	switch action {
	case "describe_account_balance":
		req := billing.NewDescribeAccountBalanceRequest()
		resp, err := client.DescribeAccountBalance(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	case "describe_bill_summary":
		req := billing.NewDescribeBillSummaryRequest()
		if m, ok := params["month"].(string); ok {
			req.Month = common.StringPtr(m)
		}
		if gt, ok := params["group_type"].(string); ok {
			req.GroupType = common.StringPtr(gt)
		} else {
			req.GroupType = common.StringPtr("business")
		}
		resp, err := client.DescribeBillSummary(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	default:
		fmt.Printf(`{"error": "unknown billing action: %s"}`, action)
	}
}

func handleHunyuan(cred *common.Credential, pf *profile.ClientProfile, region, action string, params map[string]interface{}) {
	client, _ := hunyuan.NewClient(cred, region, pf)
	switch action {
	case "chat":
		req := hunyuan.NewChatCompletionsRequest()
		if m, ok := params["model"].(string); ok {
			req.Model = common.StringPtr(m)
		} else {
			req.Model = common.StringPtr("hunyuan-pro")
		}
		if msgs, ok := params["messages"].([]interface{}); ok {
			for _, msg := range msgs {
				if m, ok := msg.(map[string]interface{}); ok {
					hm := &hunyuan.Message{}
					if r, ok := m["Role"].(string); ok {
						hm.Role = common.StringPtr(r)
					}
					if c, ok := m["Content"].(string); ok {
						hm.Content = common.StringPtr(c)
					}
					req.Messages = append(req.Messages, hm)
				}
			}
		}
		resp, err := client.ChatCompletions(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	default:
		fmt.Printf(`{"error": "unknown hunyuan action: %s"}`, action)
	}
}

func handleAIArt(cred *common.Credential, pf *profile.ClientProfile, region, action string, params map[string]interface{}) {
	client, _ := aiart.NewClient(cred, region, pf)
	switch action {
	case "query_text_to_image_job":
		req := aiart.NewQueryTextToImageJobRequest()
		if jid, ok := params["job_id"].(string); ok {
			req.JobId = common.StringPtr(jid)
		}
		resp, err := client.QueryTextToImageJob(req)
		if err != nil {
			outputJSON(map[string]string{"error": err.Error()})
			return
		}
		outputJSON(resp.Response)
	default:
		fmt.Printf(`{"error": "unknown aiart action: %s"}`, action)
	}
}
