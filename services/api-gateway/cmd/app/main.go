package main

import "github.com/Segun228/MAN_Alpha_bot/services/api-gateway/internal/app"

const configPath string = "./configs/config.yml"

func main() {
	app.Run(configPath)
}
