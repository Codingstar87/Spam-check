from fastapi import APIRouter, HTTPException, Response, status, Body,BackgroundTasks
import requests



class Usercheck:
    GITHUB_LINKS = [
        "https://raw.githubusercontent.com/tsirolnik/spam-domains-list/refs/heads/master/spamdomains.txt",
        "https://gist.githubusercontent.com/bugwrangler/69c02872dbdc5460d7251792daba7863/raw/09a7ae479aa14a07d177933990e9688e39e91630/gistfile1.txt",
        "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/refs/heads/main/allowlist.conf",
        "https://gist.githubusercontent.com/E1101/7638434ba448963f45d662158d6eca37/raw/da00895151b841e04ebbc44fd1891b48447dc411/spam_list.txt",
    ]

    @staticmethod
    def collect_domains():
        for link in Usercheck.GITHUB_LINKS:
            try:
                res = requests.get(link, timeout=10) 
                if res.status_code == 200:
                    data = res.text.strip()
                    
                    if "," in data:
                        entries = data.split(",")
                    elif " OR " in data:
                        entries = data.split(" OR ")
                    elif " " in data:
                        entries = data.split()
                    else:
                        entries = data.splitlines()

                    for entry in entries:
                        domain = entry.strip()
                        if domain:
                            payload = {
                                "domain": domain,
                                "disposable": True,
                                "publicDomain": False,
                                "suspicious": False,
                            }
                            response = requests.post("http://127.0.0.1:8090/add_domain", json=payload)
                            
                            if response.status_code != 200:
                                print(f"Failed to add domain {domain}: {response.text}")

            except requests.RequestException as e:
                print(f"Error fetching data from {link}: {e}")


