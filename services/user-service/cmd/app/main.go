package main

import "github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/app"

const configPath = "./configs/config.yml"

func main() {
	app.Run(configPath)
}
