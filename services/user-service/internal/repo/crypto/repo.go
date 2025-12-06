package crypto

import "github.com/Segun228/MAN_Alpha_bot/services/user-service/internal/repo"

func NewCryptoRepos(repos *repo.Repositories, encrypter Decrypter) *repo.Repositories {
	repos.User = NewUserCryptoRepo(repos.User, encrypter)
	repos.Business = NewBusinessCryptoRepo(repos.Business, encrypter)
	repos.Reports = NewReportsCryptoRepo(repos.Reports, encrypter)

	return repos
}
