# open만 출력하도록 설정되어 있습니다. -> 아래 코드에서 주석해제로 변경 가능
# scan은 파이썬 3.9 scan2는 파이썬 3.7

import concurrent.futures
import time
from scan import *


def scan_all(host):
    # 각 스캔 작업을 함수와 연관 메타데이터(포트 번호)와 함께 정의    
    scan_tasks = [
    (scan_ftp_ssh_port,{'port': 21}),
    (scan_ftp_ssh_port, {'port': 22}),
    (scan_telnet_port, {'port': 23}),
    (scan_smtp_ldap_port, {'port': 25}),
    (scan_dns_port, {'port': 53}),
    (scan_http_port, {'port': 80}),
    (scan_ntp_port, {'port': 123}),
    (scan_imap_port, {'port': 143}),
    (scan_snmp_port, {'port': 161}),
    (scan_smtp_ldap_port, {'port': 389}),
    (scan_ssl_port, {'port': 443}),
    (scan_smb_port, {'port': 445}),
    (scan_ssl_port, {'port': 465}),
    (scan_udp_port, {'port': 520}),
    (scan_smtp_ldap_port, {'port': 587}),
    (scan_ssl_port, {'port': 636}),
    (scan_vmware_port, {'port': 902}),
    (scan_imap_port, {'port': 993}),
    (scan_mysql_port, {'port': 3306}),
    (scan_rdp_port, {'port': 3389}),
    (scan_pop3_rsync_port, {'port': 873}),
    (scan_pop3_rsync_port, {'port': 110})
]


    results = []  # 결과를 저장할 리스트
    open_ports_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=22) as executor:
        # 각 스캔 작업에 대한 future 생성
        futures = []
        for task, metadata in scan_tasks:
            future = executor.submit(task, host, metadata['port'])
            futures.append((future, metadata))

        for future, metadata in futures:
            try:
                result = future.result()
                state = result.get('state', '').lower()
                # 'open'만 출력
                if 'open' in state and not any(x in state for x in ['closed', 'error']):
                    results.append(result)
                    open_ports_count += 1

                # 'closed'만 출력
                # if 'closed' not in result.get('state', '').lower() and 'closed or filtered' not in result.get('state', '').lower():
                #     results.append(result)
                #     open_ports_count += 1
                
                # 모든 결과 출력
                # results.append(result)

            except Exception as e:
                # 예외 발생 시 오류 메시지에 올바른 포트 번호를 포함
                error_result = {'port': metadata['port'], 'state': 'error', 'error': str(e)}
                #results.append(error_result)

    
    # 결과를 포트 번호에 따라 정렬
    filtered_results = [r for r in results if r is not None]
    sorted_results = sorted(filtered_results, key=lambda x: x['port'] if isinstance(x, dict) else x[0]['port'])
    
    # 정렬된 결과 출력   
    print(f"Open ports count: {open_ports_count}")
    for result in sorted_results:
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"{key}: {value}")
        print()
    

if __name__ == "__main__":
    host =  '127.0.0.1'
    
    startTime = time.time()
    
    scan_all(host)
    
    endTime = time.time()
    
    print("Executed Time:", (endTime - startTime))