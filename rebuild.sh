rm -rf logs/*.log
sudo docker-compose down && sudo docker-compose up -d --build && sh -x run_main.sh 

