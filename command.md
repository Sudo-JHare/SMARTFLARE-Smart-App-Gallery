commands:
docker build -t smartflare .
docker run -d -p 5000:5000 -v "$(pwd)/uploads:/app/uploads"-v "$(pwd)/instance:/app/instance" --name smartflare-app2 smartflare