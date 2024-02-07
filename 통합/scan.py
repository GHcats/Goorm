# IMAPS_conn 에서 디코딩 과정을 안 없애서 오류가 날 수도 있습니다

import socket
import struct
import time
import uuid
import imaplib
import base64
from pysnmp.hlapi import *
from smbprotocol.connection import Connection

def port123_ntp(host, timeout=1):
    port = 123
    message = '\x1b' + 47 * '\0'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    response_data = {}

    # NTP 서버로 메시지 전송 및 응답 처리
    sock.sendto(message.encode('utf-8'), (host, port))
    response, _ = sock.recvfrom(1024)
    sock.close()

    unpacked = struct.unpack('!B B B b 11I', response)
    t = struct.unpack('!12I', response)[10] - 2208988800
    response_data = {
        'port': port,
        'status': 'open',
        'stratum': unpacked[1],
        'poll': unpacked[2],
        'precision': unpacked[3],
        'root_delay': unpacked[4] / 2**16,
        'root_dispersion': unpacked[5] / 2**16,
        'ref_id': unpacked[6],
        'server_time': time.ctime(t)
    }
    return response_data

def port445_smb(host, timeout=1):
    response_data = {}
    connection = Connection(uuid.uuid4(), host, 445)
    connection.connect(timeout=timeout)
    response_data = {
        'port': 445,
        'status': 'open',
        'negotiated_dialect': connection.dialect
    }
    connection.disconnect()
    return response_data

def port902_vmware_soap(host, timeout=1):
    ports = [902]  # 902 포트만 스캔
    response_data = []

    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        try:
            sock.connect((host, port))

            # SOAP 요청 본문 준비
            soap_request = f"""POST /sdk HTTP/1.1
            Host: {host}:{port}
            Content-Type: text/xml; charset=utf-8
            Content-Length: {{length}}
            SOAPAction: "urn:internalvim25/5.5"

            <?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:vim25="urn:vim25">
            <soapenv:Header/>
            <soapenv:Body>
                <vim25:RetrieveServiceContent>
                <vim25:_this type="ServiceInstance">ServiceInstance</vim25:_this>
                </vim25:RetrieveServiceContent>
            </soapenv:Body>
            </soapenv:Envelope>"""

            body = soap_request.format(length=len(soap_request))
            sock.sendall(body.encode('utf-8'))

            # 서비스로부터 응답 받기
            response = sock.recv(4096)

            if response:
                response_data.append({
                    'port': port,
                    'status': 'open',
                    'response': response.decode('utf-8', errors='ignore')
                })
            else:
                response_data.append({'port': port, 'status': 'no response'})

        except socket.error as e:
            response_data.append({'port': port, 'status': 'error', 'error': str(e)})
        finally:
            sock.close()

    return response_data


def port3306_mysql(host, timeout=1):
    port = 3306
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))
    packet = s.recv(1024)
    s.close()

    if packet:
        end_index = packet.find(b'\x00', 5)
        server_version = packet[5:end_index].decode('utf-8')
        thread_id = struct.unpack('<I', packet[0:4])[0]
        cap_low_bytes = struct.unpack('<H', packet[end_index + 1:end_index + 3])[0]
        cap_high_bytes = struct.unpack('<H', packet[end_index + 19:end_index + 21])[0]
        server_capabilities = (cap_high_bytes << 16) + cap_low_bytes
        response_data = {
            'port': port,
            'status': 'open',
            'server_version': server_version,
            'thread_id': thread_id,
            'server_capabilities': f'{server_capabilities:032b}'
        }
        return response_data
    

def IMAP_conn(host, timeout = 10):
    port = 143
    #host = "imap.gmail.com"
    
    response_data = []
    
    try:
        imap_server = imaplib.IMAP4(host, port)
        print(f"\nConnected to IMAP server successfully.")
        
        # 배너정보 가져오기
        banner_info = imap_server.welcome
        print(f'배너정보: {banner_info}')
        
        # 디코딩 과정 원래 있었는데 생략
        response_data.append({'port': port, 'status': 'open'})
        
    except imaplib.IMAP4.error as imap_error:
        print("IMAP 오류:", imap_error)
        

    except Exception as e:
        print(f"{port}포트 \n예기치 않은 오류 발생\n{e}\n")
    
    return response_data
        

def IMAPS_conn(host, timeout = 10):
    #host = "outlook.office365.com"
    port = 993
    
    response_data = []
    
    try:
        # IMAP 서버에 SSL 연결 설정
        imap_server = imaplib.IMAP4_SSL(host, port)
        
        print("\nConnected to IMAPS server successfully.")  
        
        # 배너정보 가져오기
        banner_info = imap_server.welcome
        
        response_data.append({'port': port, 'status': 'open'})
        
        # Base64로 인코딩된 데이터 추출
        # 먼저 바이트 문자열에서 문자열로 변환
        banner_info_str = banner_info.decode('utf-8')
        pure_banner_info = banner_info_str.split('[')[0]
        encoded_data = banner_info_str.split('[')[1].split(']')[0]
       
        # Base64 디코딩
        decoded_data = base64.b64decode(encoded_data)
        print(f'banner_info: {pure_banner_info}')
       
        # 디코딩된 데이터를 문자열로 변환 (UTF-8 인코딩 사용)
        try:
            decoded_string = decoded_data.decode('utf-8')
            print(f'생성서버: {decoded_string}')
        except UnicodeDecodeError:
            print("UTF-8 디코딩 실패")
            
    except imaplib.IMAP4_SSL.error as ssl_error:
        print("SSL error:", ssl_error)
        return None
        
    except imaplib.IMAP4.error as imap_error:
        print("IMAP error:", imap_error)
        return None
        
    except Exception as e:
        print("An unexpected error occurred:", e)
        return None
    
    return response_data
    

def SNMP_conn(host, timeout = 1):
    port = 161
    community = 'public'
    
    response_data = []

    # OID 객체 생성
    sysname_oid = ObjectIdentity('SNMPv2-MIB', 'sysName', 0) #시스템 이름
    sysdesc_oid = ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0) #시스템 설명 정보 
    
    try: 
        #SNMPD 요청 생성 및 응답
        snmp_request = getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((host, port), timeout=10, retries=1),
            ContextData(),
            ObjectType(sysname_oid),
            ObjectType(sysdesc_oid)
        )
        
        response_data.append({'port': port, 'status': 'open'})
        
        #요청에 대한 결과 추출
        error_indication, error_status, error_index, var_binds = next(snmp_request)
        
        if error_indication:
                print(f"에러: {error_indication}")
        elif error_status:
            print(f"에러 상태: {error_status}")
        else:
            print("\nConnected to SNMP server successfully.") 
            for var_bind in var_binds:
                if sysname_oid.isPrefixOf(var_bind[0]):
                    print(f"시스템 이름: {var_bind[1].prettyPrint()}")
                elif sysdesc_oid.isPrefixOf(var_bind[0]):
                    print(f"시스템 설명: {var_bind[1].prettyPrint()}\n")
    except socket.timeout as timeout_error:
        print(f"연결 시간 초과: {timeout_error}\n")

    except socket.error as socket_error:
        print(f"소켓 오류: {socket_error}\n")

    except Exception as e:
        print("예기치 않은 오류 발생:\n", e)
    
    return response_data
    