import argparse
from pathlib import Path

from stundenplan24_py.proxies import ProxyProvider, Proxy


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("proxies_txt_file", type=str)
    argparser.add_argument("proxies_json_file", type=str, default="proxies.json", nargs="?")
    args = argparser.parse_args()

    proxy_provider = ProxyProvider(Path(args.proxies_json_file))
    with open(args.proxies_txt_file, "r") as f:
        for line in f.readlines():
            host, port = line.rsplit(":", 1)
            port = int(port)
            if (host, port) in proxy_provider.proxies.proxies:
                print(f"-> Proxy {host!r}:{port!r} already exists.")
                continue
            proxy_provider.proxies.add_proxy(Proxy(host, int(port), None))

    proxy_provider.store_proxies()

    print("...Done!")


if __name__ == "__main__":
    main()
