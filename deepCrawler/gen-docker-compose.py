#NAMES = ['bart', 'homer', 'marge', 'lisa',"martin","patty","rainier","cletus","kumiko","maggie","abraham","santa","barney","dewey","eddie","edna","janey","jasper","kent","lou"]

NUM_PROXIES = 2
WARNING = "# Generated by gen-docker-compose script.\n\n"

# Generate docker-compose.yml.
#
with open("docker-compose.yml", "w") as f:
    f.write(WARNING)
    f.write("version: '3'\n\nservices:\n")

    for index in range(NUM_PROXIES):
        name = "privoxy" + str(index)
        f.write(f"  {name}:\n")
        f.write(f"    container_name: '{name}'\n")
        f.write("    image: 'pickapp/tor-proxy:latest'\n")
        #f.write("    ports:\n")
        #f.write(f"      - '{9990+index}:8888'\n")
        f.write("    environment:\n")
        f.write("      - IP_CHANGE_SECONDS=30\n")
        f.write("    restart: always\n")

    f.write(f"  scrapy:\n")
    f.write("    build: .\n")
    f.write("    volumes:\n")
    f.write("      - scrapyVol:/usr/src/jobs/\n")
    f.write("    depends_on:\n")
    for index in range(NUM_PROXIES):
        name = "privoxy" + str(index)
        f.write(f'      - "{name}"\n')

    f.write("volumes:\n")
    f.write("  scrapyVol:\n")
# Generate proxy-list.txt.
#
with open("proxy-list.txt", "w") as f:
    f.write(WARNING)

    for index in range(NUM_PROXIES):
        name = "privoxy" + str(index)
        f.write(f'http://{name}:8888\n')
